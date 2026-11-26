from sqlalchemy import text
from src.config import SCRIPT_CREATION


def create_tables(conn) -> None:
    """
    Crée les tables à partir du script de création
    :return:
    """
    with open(SCRIPT_CREATION, "r") as f:
        sql_script = f.read()

    for statement in sql_script.split(";"):
        statement = statement.strip()
        if statement:
            conn.execute(text(statement))
