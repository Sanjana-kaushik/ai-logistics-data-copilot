from pathlib import Path
import sqlite3

from datetime import datetime

import pandas as pd


DATABASE_PATH = "logistics.db"
DATA_FOLDER = Path("data")


def get_connection():
    """
    Create and return a connection to the SQLite database.
    """
    return sqlite3.connect(DATABASE_PATH)


def create_database():
    """
    Read the CSV files and load them into SQLite tables.
    """
    files = {
        "customers": "customers.csv",
        "products": "products.csv",
        "orders": "orders.csv",
        "shipments": "shipments.csv",
        "metadata": "metadata.csv",
    }

    with get_connection() as connection:
        for table_name, file_name in files.items():
            file_path = DATA_FOLDER / file_name

            if not file_path.exists():
                raise FileNotFoundError(
                    f"{file_path} was not found. "
                    "Run generate_data.py first."
                )

            dataframe = pd.read_csv(file_path)

            dataframe.to_sql(
                table_name,
                connection,
                if_exists="replace",
                index=False,
            )

            print(
                f"Loaded {len(dataframe)} rows "
                f"into the {table_name} table."
            )

    print("SQLite database created successfully.")
    create_query_history_table()



def run_query(query):
    """
    Run a safe, read-only SQL query.
    """

    normalized_query = query.strip().lower()

    blocked_words = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "create",
        "replace",
        "truncate",
        "attach",
        "pragma",
    ]

    if not normalized_query.startswith("select"):
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    if any(
        blocked_word in normalized_query
        for blocked_word in blocked_words
    ):
        raise ValueError(
            "Potentially unsafe SQL was blocked."
        )

    with get_connection() as connection:
        return pd.read_sql_query(
            query,
            connection,
        )
    print(result)

def create_query_history_table():
    """
    Create a table for approved AI queries.
    """
    connection = sqlite3.connect("logistics.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS query_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_question TEXT NOT NULL,
            generated_sql TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            executed_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()

def save_query_history(
    user_question: str,
    generated_sql: str,
    row_count: int,
):
    """
    Save an approved and successfully executed query.
    """
    connection = sqlite3.connect("logistics.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO query_history (
            user_question,
            generated_sql,
            row_count,
            executed_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_question,
            generated_sql,
            row_count,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        ),
    )

    connection.commit()
    connection.close()


def get_query_history():
    """
    Return the 50 most recent approved AI queries.
    """
    connection = sqlite3.connect("logistics.db")

    query = """
        SELECT
            history_id,
            executed_at,
            user_question,
            generated_sql,
            row_count
        FROM query_history
        ORDER BY history_id DESC
        LIMIT 50
    """

    history_dataframe = pd.read_sql_query(
        query,
        connection,
    )

    connection.close()

    return history_dataframe