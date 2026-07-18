import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

MODEL_NAME = os.getenv(
    "OPENAI_MODEL",
    "gpt-4.1-mini",
)

if not API_KEY:
    try:
        import streamlit as st

        API_KEY = st.secrets.get(
            "OPENAI_API_KEY"
        )

        MODEL_NAME = st.secrets.get(
            "OPENAI_MODEL",
            MODEL_NAME,
        )

    except Exception:
        API_KEY = None
        

client = OpenAI(api_key=API_KEY) if API_KEY else None


DATABASE_SCHEMA = """
customers(
    customer_id,
    customer_name,
    country,
    customer_segment,
    signup_date
)

products(
    product_id,
    product_name,
    category,
    unit_price
)

orders(
    order_id,
    customer_id,
    product_id,
    order_date,
    quantity,
    unit_price,
    order_value,
    order_status
)

shipments(
    shipment_id,
    order_id,
    carrier,
    promised_delivery_date,
    actual_delivery_date,
    delay_days,
    shipment_status
)

metadata(
    table_name,
    column_name,
    description,
    data_type
)
"""


def get_client() -> OpenAI:
    """
    Return the configured OpenAI client.

    Raises:
        RuntimeError: If the API key is unavailable.
    """
    if client is None:
        raise RuntimeError(
            "OPENAI_API_KEY was not found. "
            "Check that your .env file is saved in the project folder."
        )

    return client


def clean_generated_sql(sql: str) -> str:
    """
    Remove markdown formatting from model-generated SQL.
    """
    cleaned_sql = (
        sql.replace("```sql", "")
        .replace("```SQL", "")
        .replace("```", "")
        .strip()
    )

    return cleaned_sql


def validate_generated_sql(sql: str) -> None:
    """
    Validate that generated SQL is read-only.
    """
    normalized_sql = sql.strip().lower()

    blocked_terms = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "create",
        "replace",
        "truncate",
        "attach",
        "detach",
        "pragma",
        "vacuum",
    ]

    if not normalized_sql.startswith("select"):
        raise ValueError(
            "The generated query was blocked because "
            "it was not a SELECT statement."
        )

    if any(term in normalized_sql for term in blocked_terms):
        raise ValueError(
            "The generated query contained a blocked SQL command."
        )

    if ";" in normalized_sql.rstrip(";"):
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )


def generate_sql(question: str) -> str:
    """
    Convert a natural-language business question into SQLite SQL.
    """
    if not question.strip():
        raise ValueError("A business question is required.")

    prompt = f"""
You are a senior enterprise data analyst.

Convert the user's business question into exactly one valid
SQLite SELECT query.

DATABASE SCHEMA

{DATABASE_SCHEMA}

BUSINESS RULES

- Revenue means orders.order_value.
- Orders join to customers using customer_id.
- Orders join to products using product_id.
- Orders join to shipments using order_id.
- A delayed shipment has shipment_status = 'Delayed'.
- On-time shipments have shipment_status = 'Delivered'.
- delay_days measures days beyond the promised delivery date.

SQL RULES

- Return SQL only.
- Do not include markdown.
- Generate exactly one SELECT query.
- Never modify data.
- Use only tables and columns listed in the schema.
- Use explicit JOIN conditions.
- Use SQLite-compatible syntax.
- Use LIMIT 100 for detailed record listings.
- Do not use LIMIT for normal aggregate summaries unless requested.
- Use meaningful aliases.
- Avoid SELECT * unless detailed records are explicitly requested.

USER QUESTION

{question}
"""

    response = get_client().responses.create(
        model=MODEL_NAME,
        input=prompt,
    )

    generated_sql = clean_generated_sql(
        response.output_text
    )

    validate_generated_sql(generated_sql)

    return generated_sql


def generate_business_summary(
    question: str,
    sql: str,
    result_text: str,
) -> str:
    """
    Generate a concise stakeholder summary from query results.
    """
    prompt = f"""
You are a senior business data analyst.

Review the question, SQL, and query result below.

QUESTION

{question}

SQL

{sql}

QUERY RESULT

{result_text}

Write a concise response containing:

1. Main finding
2. Business implication
3. One useful follow-up question

Requirements:

- Use only evidence contained in the result.
- Do not invent causes or explanations.
- If the result is insufficient, state that clearly.
- Keep the response below 150 words.
- Write for a business stakeholder.
"""

    response = get_client().responses.create(
        model=MODEL_NAME,
        input=prompt,
    )

    return response.output_text.strip()

