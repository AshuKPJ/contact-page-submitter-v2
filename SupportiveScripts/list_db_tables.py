from sqlalchemy import create_engine, inspect, text
from tabulate import tabulate  # pip install tabulate
import pandas as pd  # pip install pandas

# 🔑 Replace with your actual database URL
# Example: "postgresql://user:password@host:5432/dbname"
DATABASE_URL = "postgresql://neondb_owner:npg_TIN40HCxdqBU@ep-long-glitter-aekty8cj-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"


def list_tables_and_columns(db_url: str):
    # Create engine
    engine = create_engine(db_url)
    inspector = inspect(engine)

    # Get all tables
    tables = inspector.get_table_names()

    if not tables:
        print("⚠️ No tables found in this database.")
        return

    print("\n📋 Tables and Columns in the Database:\n")

    for table in tables:
        print(f"🔹 Table: {table}")
        columns = inspector.get_columns(table)

        # Build rows for tabulate
        rows = [
            (col["name"], str(col["type"]), col.get("nullable", True))
            for col in columns
        ]

        print(tabulate(rows, headers=["Column Name", "Data Type", "Nullable"]))
        print("-" * 60)


def show_table_records(db_url: str, table_name: str, limit: int = 20):
    # Create engine
    engine = create_engine(db_url)

    # Query table
    query = text(f"SELECT * FROM {table_name} LIMIT {limit};")
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    print(f"\n📋 Records from table: {table_name} (showing {limit} rows)")
    print(df.to_string(index=False))  # neat tabular output


if __name__ == "__main__":
    # list_tables_and_columns(DATABASE_URL)
    show_table_records(DATABASE_URL, "users", limit=10)
