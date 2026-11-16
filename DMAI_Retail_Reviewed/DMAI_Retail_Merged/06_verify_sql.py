"""Verify the reviewed database and export SQL summaries for the team report."""
import sqlite3

import pandas as pd

from config import BASE, DB_PATH, OUT

if not DB_PATH.is_file():
    raise SystemExit("Run 01_load_raw.py and 02_clean_build_db.py first.")

output = OUT / "sql"
output.mkdir(exist_ok=True)
with sqlite3.connect(DB_PATH) as conn:
    # Match the partner scripts' column names using the existing invoice tables.
    # This view reads the latest cleaned rows whenever a query runs.
    conn.execute("""
        CREATE VIEW IF NOT EXISTS clean_transactions AS
        SELECT i.invoice_no AS InvoiceNo, it.stock_code AS StockCode,
               p.description AS Description, it.quantity AS Quantity,
               i.invoice_date AS InvoiceDate, it.unit_price AS UnitPrice,
               i.customer_id AS CustomerID, i.country AS Country,
               it.quantity * it.unit_price AS Revenue
        FROM invoice_items AS it
        JOIN invoices AS i ON i.invoice_no = it.invoice_no
        JOIN products AS p ON p.stock_code = it.stock_code
    """)
    conn.execute("PRAGMA query_only = ON")
    quality = pd.read_sql_query("""
        SELECT COUNT(*) AS sales_lines, COUNT(DISTINCT CustomerID) AS customers,
               COUNT(DISTINCT InvoiceNo) AS invoices,
               ROUND(SUM(Revenue), 2) AS gross_purchases,
               COUNT(*) FILTER (WHERE CustomerID IS NULL) AS missing_customers,
               COUNT(*) FILTER (WHERE Quantity <= 0 OR UnitPrice <= 0) AS invalid_sales,
               COUNT(*) FILTER (WHERE InvoiceNo LIKE 'C%') AS cancellations_in_sales
        FROM clean_transactions
    """, conn)
    row = quality.iloc[0]
    expected = conn.execute(
        "SELECT rows_after FROM cleaning_log ORDER BY rowid DESC LIMIT 1"
    ).fetchone()[0]
    quality["duplicates_removed_during_cleaning"] = conn.execute(
        "SELECT rows_removed FROM cleaning_log WHERE step = '5. duplicate rows'"
    ).fetchone()[0]
    quality["foreign_key_violations"] = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    print(quality.to_string(index=False))
    quality.to_csv(output / "cleaning_checks.csv", index=False)
    errors = ["missing_customers", "invalid_sales", "cancellations_in_sales", "foreign_key_violations"]
    if row.sales_lines != expected or quality[errors].any().any():
        raise SystemExit("The cleaning checks failed. Inspect outputs/sql/cleaning_checks.csv.")

    # The file contains one SELECT per section, separated by a blank line.
    # sqlite3 recognises complete statements, including multiline queries.
    statement = ""
    number = 0
    for line in (BASE / "analysis_queries.sql").read_text(encoding="utf-8-sig").splitlines(True):
        if not statement.strip() and (not line.strip() or line.lstrip().startswith("--")):
            continue
        statement += line
        if sqlite3.complete_statement(statement):
            number += 1
            result = pd.read_sql_query(statement, conn)
            result.to_csv(output / f"query_{number}.csv", index=False)
            print(f"Query {number}: {len(result)} rows")
            statement = ""
    if statement.strip():
        raise SystemExit("The last SQL query needs a terminating semicolon.")
