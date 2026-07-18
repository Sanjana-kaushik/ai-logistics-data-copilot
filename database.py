from pathlib import Path
import sqlite3

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