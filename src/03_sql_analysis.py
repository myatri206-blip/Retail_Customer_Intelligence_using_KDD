
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

db_path = ROOT / "database" / "retail.db"
sql_path = ROOT / "database" / "analysis_queries.sql"
output_dir = ROOT / "outputs" / "sql"

output_dir.mkdir(parents=True, exist_ok=True)

sql_script = sql_path.read_text(encoding="utf-8")

queries = [
    query.strip()
    for query in sql_script.split(";")
    if query.strip()
]

with sqlite3.connect(db_path) as conn:
    for i, query in enumerate(queries, start=1):

        result = pd.read_sql_query(query, conn)

        print(f"\nQUERY {i}")
        print(result.to_string(index=False))

        output_file = output_dir / f"query_{i}.csv"
        result.to_csv(output_file, index=False)

        print("Saved:", output_file)

print("\nSQL analysis completed successfully!")
