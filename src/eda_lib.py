from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats

pd.options.mode.copy_on_write = True


NUTRIMENT_COLS = [
    "energy-kcal_100g",
    "fat_100g",
    "saturated-fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "fiber_100g",
    "proteins_100g",
    "salt_100g",
    "sodium_100g",
]


def _as_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def clean_minimal_tp10(df: pd.DataFrame) -> pd.DataFrame:
    """Apply fallback cleaning rules from TP10 when TP9 output is unavailable."""
    cleaned = df.copy()

    cleaned = cleaned.drop_duplicates(subset=["code"], keep="first")

    nutriments_0_100 = [
        "fat_100g",
        "saturated-fat_100g",
        "carbohydrates_100g",
        "sugars_100g",
        "fiber_100g",
        "proteins_100g",
        "salt_100g",
        "sodium_100g",
    ]

    for col in nutriments_0_100:
        if col in cleaned.columns:
            series = _as_numeric(cleaned[col])
            valid = series.isna() | ((series >= 0) & (series <= 100))
            cleaned = cleaned.loc[valid].copy()

    if "energy-kcal_100g" in cleaned.columns:
        kcal = _as_numeric(cleaned["energy-kcal_100g"])
        valid_kcal = kcal.isna() | ((kcal >= 0) & (kcal <= 900))
        cleaned = cleaned.loc[valid_kcal].copy()

    return cleaned


def filter_known_rayon(df: pd.DataFrame, group_col: str = "pnns_groups_1") -> pd.DataFrame:
    if group_col not in df.columns:
        return df.copy()
    mask = df[group_col].notna() & (~df[group_col].astype(str).str.lower().eq("unknown"))
    return df.loc[mask].copy()


def resume_univarie(s: pd.Series, quantiles: Iterable[float] = (0.05, 0.25, 0.5, 0.75, 0.95)) -> dict:
    x = _as_numeric(s).dropna()
    n_total = int(s.shape[0])
    n_valid = int(x.shape[0])
    n_missing = n_total - n_valid

    if n_valid == 0:
        base = {
            "n": n_total,
            "n_valid": 0,
            "n_missing": n_missing,
            "missing_rate": np.nan,
            "mean": np.nan,
            "median": np.nan,
            "std": np.nan,
            "iqr": np.nan,
            "mad": np.nan,
            "cv": np.nan,
            "skew": np.nan,
            "kurtosis": np.nan,
        }
        for q in quantiles:
            base[f"q{int(round(q * 100)):02d}"] = np.nan
        return base

    q_vals = x.quantile(list(quantiles))
    mean = float(x.mean())
    median = float(x.median())
    std = float(x.std(ddof=1)) if n_valid > 1 else 0.0
    iqr = float(x.quantile(0.75) - x.quantile(0.25))
    mad = float(stats.median_abs_deviation(x, nan_policy="omit", scale="normal"))
    cv = float(std / mean) if mean != 0 else np.nan

    out = {
        "n": n_total,
        "n_valid": n_valid,
        "n_missing": n_missing,
        "missing_rate": n_missing / n_total if n_total else np.nan,
        "mean": mean,
        "median": median,
        "std": std,
        "iqr": iqr,
        "mad": mad,
        "cv": cv,
        "skew": float(x.skew()),
        "kurtosis": float(x.kurtosis()),
    }
    for q, v in q_vals.items():
        out[f"q{int(round(q * 100)):02d}"] = float(v)
    return out


def profil_par_rayon(
    df: pd.DataFrame,
    colonnes: list[str],
    group_col: str = "pnns_groups_1",
    min_n: int = 30,
) -> tuple[pd.DataFrame, list[str]]:
    base = filter_known_rayon(df, group_col=group_col)
    counts = base.groupby(group_col, observed=True).size().rename("n")
    valid_groups = counts[counts >= min_n].index
    dropped_groups = counts[counts < min_n].index.tolist()

    base = base.loc[base[group_col].isin(valid_groups)].copy()
    rows: list[pd.DataFrame] = []

    for col in colonnes:
        x = _as_numeric(base[col])
        g = base[group_col]
        agg = (
            pd.DataFrame({group_col: g, "x": x})
            .groupby(group_col, observed=True)["x"]
            .agg(n="count", mean="mean", median="median", q1=lambda s: s.quantile(0.25), q3=lambda s: s.quantile(0.75))
            .reset_index()
        )
        agg.insert(1, "nutriment", col)
        rows.append(agg)

    return pd.concat(rows, ignore_index=True), dropped_groups


def crosstab_percent_and_cramers_v(df: pd.DataFrame, col_a: str, col_b: str) -> tuple[pd.DataFrame, float]:
    tab = pd.crosstab(df[col_a], df[col_b], normalize="index") * 100
    observed = pd.crosstab(df[col_a], df[col_b])
    if observed.empty:
        return tab, np.nan

    chi2, _, _, _ = stats.chi2_contingency(observed)
    n = observed.to_numpy().sum()
    if n == 0:
        return tab, np.nan
    r, k = observed.shape
    phi2 = chi2 / n
    phi2_corr = max(0.0, phi2 - ((k - 1) * (r - 1)) / max(n - 1, 1))
    r_corr = r - ((r - 1) ** 2) / max(n - 1, 1)
    k_corr = k - ((k - 1) ** 2) / max(n - 1, 1)
    denom = min((k_corr - 1), (r_corr - 1))
    if denom <= 0:
        return tab, np.nan
    return tab, float(np.sqrt(phi2_corr / denom))


def completude_par_groupe(
    df: pd.DataFrame,
    groupe: str,
    colonnes: list[str],
    min_n: int = 20,
) -> pd.DataFrame:
    work = df.copy()
    counts = work.groupby(groupe, observed=True).size().rename("n")
    valid_groups = counts[counts >= min_n].index
    work = work.loc[work[groupe].isin(valid_groups)].copy()

    rows = []
    for grp, part in work.groupby(groupe, observed=True):
        row = {groupe: grp, "n": int(len(part))}
        complete_flags = np.ones(len(part), dtype=bool)
        for col in colonnes:
            present = _as_numeric(part[col]).notna()
            row[f"presence_{col}"] = float(present.mean())
            complete_flags &= present.to_numpy()
        row["taux_fiches_completes"] = float(complete_flags.mean())
        if "nutriscore_score" in part.columns:
            row["presence_nutriscore_score"] = float(_as_numeric(part["nutriscore_score"]).notna().mean())
        rows.append(row)

    return pd.DataFrame(rows).sort_values("n", ascending=False).reset_index(drop=True)


def incoherences_metier(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    for col in NUTRIMENT_COLS:
        if col in work.columns:
            work[col] = _as_numeric(work[col])

    calc_kcal = (
        9 * work.get("fat_100g", 0)
        + 4 * work.get("carbohydrates_100g", 0)
        + 4 * work.get("proteins_100g", 0)
        + 2 * work.get("fiber_100g", 0)
    )

    inco = pd.DataFrame(index=work.index)
    inco["sucres_sup_glucides"] = work.get("sugars_100g") > work.get("carbohydrates_100g")
    inco["satures_sup_lipides"] = work.get("saturated-fat_100g") > work.get("fat_100g")
    if "sodium_100g" in work.columns and "salt_100g" in work.columns:
        diff = (work["salt_100g"] - 2.5 * work["sodium_100g"]).abs()
        inco["sel_diff_sodium"] = diff > 0.2
    else:
        inco["sel_diff_sodium"] = False

    if "energy-kcal_100g" in work.columns:
        inco["energie_ecart_150"] = (work["energy-kcal_100g"] - calc_kcal).abs() > 150
        macro_sum = work[["fat_100g", "carbohydrates_100g", "proteins_100g"]].sum(axis=1, skipna=True)
        inco["energie_nulle_avec_macros"] = (work["energy-kcal_100g"] == 0) & (macro_sum > 0)
    else:
        inco["energie_ecart_150"] = False
        inco["energie_nulle_avec_macros"] = False

    return inco.fillna(False).astype(bool)


def correlations_nutriscore(
    df: pd.DataFrame,
    colonnes: list[str],
    cible: str = "nutriscore_score",
    min_n: int = 30,
) -> pd.DataFrame:
    rows = []
    y = _as_numeric(df[cible])
    for col in colonnes:
        x = _as_numeric(df[col])
        pair = pd.DataFrame({"x": x, "y": y}).dropna()
        n = len(pair)
        if n < min_n:
            continue
        pearson = stats.pearsonr(pair["x"], pair["y"]).statistic
        spearman = stats.spearmanr(pair["x"], pair["y"]).statistic
        rows.append({"variable": col, "n": n, "pearson": float(pearson), "spearman": float(spearman)})

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("spearman", key=lambda s: s.abs(), ascending=False).reset_index(drop=True)


def paires_redondantes(matrice: pd.DataFrame, seuil: float = 0.8) -> pd.DataFrame:
    rows = []
    cols = list(matrice.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            val = float(matrice.loc[a, b])
            if np.isfinite(val) and abs(val) >= seuil:
                rows.append({"var_a": a, "var_b": b, "corr": val, "abs_corr": abs(val)})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("abs_corr", ascending=False).reset_index(drop=True)


def correlations_par_rayon(
    df: pd.DataFrame,
    colonne: str,
    cible: str = "nutriscore_score",
    group_col: str = "pnns_groups_1",
    min_n: int = 30,
) -> pd.DataFrame:
    work = filter_known_rayon(df, group_col=group_col)
    rows = []
    for grp, part in work.groupby(group_col, observed=True):
        pair = pd.DataFrame({"x": _as_numeric(part[colonne]), "y": _as_numeric(part[cible])}).dropna()
        if len(pair) < min_n:
            continue
        rows.append(
            {
                group_col: grp,
                "n": int(len(pair)),
                "spearman": float(stats.spearmanr(pair["x"], pair["y"]).statistic),
                "pearson": float(stats.pearsonr(pair["x"], pair["y"]).statistic),
            }
        )

    return pd.DataFrame(rows).sort_values("n", ascending=False).reset_index(drop=True)


def zscore_robuste(s: pd.Series) -> pd.Series:
    x = _as_numeric(s)
    med = x.median(skipna=True)
    mad = stats.median_abs_deviation(x.dropna(), scale="normal")
    if not np.isfinite(mad) or mad == 0:
        std = x.std(skipna=True, ddof=1)
        if not np.isfinite(std) or std == 0:
            return pd.Series(np.zeros(len(x), dtype=float), index=s.index)
        return (x - med) / std
    return (x - med) / mad


def extremes_restants(
    df: pd.DataFrame,
    colonnes: list[str],
    group_col: str = "pnns_groups_1",
    seuil: float = 3.5,
) -> pd.DataFrame:
    work = filter_known_rayon(df, group_col=group_col)
    rows = []
    for grp, part in work.groupby(group_col, observed=True):
        for col in colonnes:
            z = zscore_robuste(part[col])
            flagged = part.loc[z.abs() > seuil, [group_col, "code", "product_name", col]].copy()
            if flagged.empty:
                continue
            flagged["variable"] = col
            flagged["z_robuste"] = z.loc[flagged.index]
            flagged = flagged.rename(columns={col: "value"})
            rows.append(flagged)

    if not rows:
        return pd.DataFrame(columns=[group_col, "code", "product_name", "variable", "value", "z_robuste"])

    out = pd.concat(rows, ignore_index=True)
    return out.sort_values("z_robuste", key=lambda s: s.abs(), ascending=False).reset_index(drop=True)


@dataclass
class GroupCompareResult:
    n_a: int
    n_b: int
    median_a: float
    median_b: float
    delta_median: float
    cohen_d: float
    mann_whitney_u: float
    p_value: float


def comparer_deux_groupes(a: pd.Series, b: pd.Series) -> GroupCompareResult:
    x = _as_numeric(a).dropna()
    y = _as_numeric(b).dropna()
    if len(x) < 2 or len(y) < 2:
        return GroupCompareResult(len(x), len(y), np.nan, np.nan, np.nan, np.nan, np.nan, np.nan)

    s1 = x.std(ddof=1)
    s2 = y.std(ddof=1)
    pooled = np.sqrt(((len(x) - 1) * (s1**2) + (len(y) - 1) * (s2**2)) / (len(x) + len(y) - 2))
    d = (x.mean() - y.mean()) / pooled if pooled else np.nan

    u_test = stats.mannwhitneyu(x, y, alternative="two-sided")
    return GroupCompareResult(
        n_a=int(len(x)),
        n_b=int(len(y)),
        median_a=float(x.median()),
        median_b=float(y.median()),
        delta_median=float(x.median() - y.median()),
        cohen_d=float(d),
        mann_whitney_u=float(u_test.statistic),
        p_value=float(u_test.pvalue),
    )