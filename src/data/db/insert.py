import io
import pandas as pd
import logging
from src.data.db.connection import get_engine

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def insert_in_db(df: pd.DataFrame, name: str) :
    engine = get_engine()
    try:
        with engine.begin() as conn:  # commit automatique si succès, rollback si erreur
            insert_in_db_copy(df, name, conn)
            logger.info(f"{len(df)} lignes importées avec succès")
    except Exception as e:
        logger.error(f"Échec de l'import ({len(df)} lignes) : {e}")

def insert_in_db_copy(df: pd.DataFrame, name: str, conn) :
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False, sep="\t", na_rep="\\N")
    buffer.seek(0)

    cur = conn.connection.cursor()
    cur.copy_expert(
        f"COPY {name} FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\\\N')",
        buffer
    )