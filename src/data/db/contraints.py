from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import text


def drop_constraints(conn, tables: list[str], types: tuple[str, ...] = ('f', 'p')) -> list[tuple]:
    """
    Supprime les contraintes (FK et/ou PK) des tables données pour accélérer le
    COPY en masse. Jamais de nom de contrainte en dur : ils sont lus dans
    pg_constraint, avec leur définition complète (pg_get_constraintdef) pour
    pouvoir les recréer via restore_constraints. FK supprimées avant PK.
    :return: lignes (table, conname, ddl, contype) à repasser à restore_constraints
    """
    rows = conn.execute(text("""
                             SELECT rel.relname                   AS tbl,
                                    con.conname,
                                    pg_get_constraintdef(con.oid) AS ddl,
                                    con.contype::text
                             FROM pg_constraint con
                                      JOIN pg_class rel ON rel.oid = con.conrelid
                             WHERE rel.relname = ANY (:tables)
                               AND con.contype::text = ANY (:types)
                             """), {"tables": tables, "types": list(types)}).fetchall()

    for tbl, conname, ddl, contype in sorted(rows, key=lambda r: r[3] != 'f'):
        conn.execute(text(f'ALTER TABLE "{tbl}" DROP CONSTRAINT IF EXISTS "{conname}"'))

    return rows


def restore_constraints(engine, rows: list[tuple], max_workers: int = 3) -> None:
    """
    Recrée les contraintes retirées par drop_constraints, une connexion par
    table en parallèle. Les tables de jonction sont indépendantes entre elles
    (leurs FK référencent produits/categories/labels/marques/origines, jamais
    une autre table de jonction), donc leurs index de PK peuvent se reconstruire
    en parallèle sans se bloquer. À l'intérieur d'une même table, PK avant FK.
    """
    by_table: dict[str, list[tuple]] = {}
    for row in rows:
        by_table.setdefault(row[0], []).append(row)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_restore_table_constraints, engine, tbl_rows) for tbl_rows in by_table.values()]
        for future in futures:
            future.result()


def _restore_table_constraints(engine, rows: list[tuple]) -> None:
    """Recrée les contraintes d'UNE table (PK avant FK), sur sa propre connexion."""
    with engine.begin() as conn:
        conn.execute(text("SET maintenance_work_mem = '1GB'"))
        conn.execute(text("SET max_parallel_maintenance_workers = 4"))
        for tbl, conname, ddl, contype in sorted(rows, key=lambda r: r[3] != 'p'):
            conn.execute(text(f'ALTER TABLE "{tbl}" ADD CONSTRAINT "{conname}" {ddl}'))
