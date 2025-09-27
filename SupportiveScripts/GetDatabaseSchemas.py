# list_schemas.py
from sqlalchemy import create_engine, text

# Your provided DATABASE_URL
DATABASE_URL = "postgresql://neondb_owner:npg_TIN40HCxdqBU@ep-long-glitter-aekty8cj-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(DATABASE_URL)


def get_schema_details():
    with engine.connect() as conn:
        print("\n=== Tables in 'public' schema ===")
        tables = conn.execute(
            text(
                """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
            )
        ).fetchall()
        for t in tables:
            print(f"- {t[0]}")

        print("\n=== Columns per table ===")
        for t in tables:
            print(f"\nTable: {t[0]}")
            columns = conn.execute(
                text(
                    """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :table
                ORDER BY ordinal_position;
            """
                ),
                {"table": t[0]},
            ).fetchall()
            for c in columns:
                print(f"  {c[0]} | {c[1]} | nullable={c[2]} | default={c[3]}")

        print("\n=== Indexes ===")
        indexes = conn.execute(
            text(
                """
            SELECT
                t.relname AS table_name,
                i.relname AS index_name,
                a.attname AS column_name
            FROM
                pg_class t,
                pg_class i,
                pg_index ix,
                pg_attribute a
            WHERE
                t.oid = ix.indrelid
                AND i.oid = ix.indexrelid
                AND a.attrelid = t.oid
                AND a.attnum = ANY(ix.indkey)
                AND t.relkind = 'r'
                AND t.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            ORDER BY t.relname, i.relname;
        """
            )
        ).fetchall()
        for idx in indexes:
            print(f"- {idx[0]} | {idx[1]} | column: {idx[2]}")

        print("\n=== Constraints ===")
        constraints = conn.execute(
            text(
                """
            SELECT
                conrelid::regclass AS table_name,
                conname AS constraint_name,
                pg_get_constraintdef(c.oid) AS definition
            FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE n.nspname = 'public'
            ORDER BY table_name, constraint_name;
        """
            )
        ).fetchall()
        for cons in constraints:
            print(f"- {cons[0]} | {cons[1]} | {cons[2]}")


if __name__ == "__main__":
    get_schema_details()
