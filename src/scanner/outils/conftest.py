"""Configuration des tests du contrat : l'option --scanner et le chargement de votre fonction.

Lancement, depuis la racine de votre dépôt :

    pytest outils
    pytest outils --scanner src/workflow.py:scanner_etiquette     # si votre fonction est ailleurs
"""

from __future__ import annotations

from typing import Any

import pytest

from atelier_commun import SCANNER_PAR_DEFAUT, ScannerIntrouvable, charger_scanner


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--scanner", default=SCANNER_PAR_DEFAUT,
                     help=f"où est votre fonction : fichier.py:nom_fonction (défaut : {SCANNER_PAR_DEFAUT})")


@pytest.fixture(scope="session")
def scanner_etiquette(request: pytest.FixtureRequest):
    """Sans scanner, inutile de lancer 90 tests : un seul message clair, et on s'arrête."""
    # L'option n'existe pas si pytest est lancé sans « outils » en argument : on prend alors le défaut.
    indication = request.config.getoption("--scanner", default=SCANNER_PAR_DEFAUT)
    try:
        return charger_scanner(indication)
    except ScannerIntrouvable as e:
        pytest.exit(f"Scanner introuvable : {e}", returncode=2)


@pytest.fixture(scope="session")
def scanner_une_fois(scanner_etiquette):
    """Chaque image n'est scannée qu'une fois, quel que soit le nombre de tests qui l'utilisent."""
    deja: dict[str, Any] = {}

    def scanner(cle: str, image: Any) -> Any:
        if cle not in deja:
            try:
                deja[cle] = ("ok", scanner_etiquette(image))
            except Exception as e:
                deja[cle] = ("exception", f"{type(e).__name__}: {e}")
        etat, valeur = deja[cle]
        if etat == "exception":
            pytest.fail(f"scanner_etiquette a levé une exception (le contrat l'interdit) : {valeur}", pytrace=False)
        return valeur

    return scanner
