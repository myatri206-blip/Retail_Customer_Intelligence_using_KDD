# DMAI retail team project

## Upgrade an existing run

Open the folder where `config.py` and your finished `retail.db` are located. Copy the following four files from this package into that folder.

- Replace `05_segment_customers.py` with this version.
- Add `06_verify_sql.py`, `07_eda.py` and `analysis_queries.sql`.

In the VS Code terminal with your existing environment active, run these commands one at a time.

```powershell
python 05_segment_customers.py
python 06_verify_sql.py
python 07_eda.py
```

05 refreshes the segmentation outputs and adds the customer-level CSVs and histograms. 06 verifies the cleaned retail tables, creates a SQLite view called `clean_transactions` and exports SQL summaries. 07 uses the view to make the five EDA charts. The prediction model and its features already work with these data.

## Run from the beginning

Extract the folder, put the real workbook in `data/Online Retail.xlsx`, and open the folder containing `config.py`. With Python 3.12 and the project environment active, run:

```powershell
python -m pip install -r requirements.txt
python 01_load_raw.py
python 02_clean_build_db.py
python 03_build_features.py
python 04_predict_repurchase.py
python 05_segment_customers.py
python 06_verify_sql.py
python 07_eda.py
```

## Where to find the results

| Path | Contents |
| --- | --- |
| outputs/cleaning_log.csv | Rows removed by each cleaning rule |
| outputs/model_comparison.csv | Evaluation of repurchase prediction on later dates |
| outputs/segment_profiles.csv | Segment medians and shares of customers and purchases |
| outputs/rfm/ | One row per customer and three distributions using full-period RFM |
| outputs/clustering/ | Customer segment assignments, mean profiles and K evaluation |
| outputs/sql/ | Cleaning checks and query results |
| outputs/eda/ | Monthly sales, top products, countries, spending and order frequency, plus summary statistics |

## How the two analyses fit together

All reports use the reviewed database and the same definition of a qualifying sale. The view joins invoice items to invoice headers and product descriptions to recreate one row per item. Its dates and countries come from invoice headers. The cleaned database uses one standard description per product code. Original line-level values remain in the raw table.

The SQL file contains three example queries supplied with this merge. The original partner SQL file was not attached. To run the team's original queries later, review their input tables and column names. Queries against the clean_transactions view can use InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country and Revenue. The raw table is named raw_online_retail. For additional summaries, add one SELECT statement ending in a semicolon on its own final line or at the end of the last line of the statement, then rerun 06.

The partner's original RFM calculation subtracts timestamps and rounds down to whole days. The merged version uses calendar-day differences. On the real workbook, a purchase on 9 December has recency 1 on 10 December.

Segmentation uses the whole purchase period, K from 2 through 8 and a silhouette score calculated on all customers. Repurchase prediction uses dated snapshots and a forward 30-day target. Final customer segments are calculated at the end of the dataset and are excluded from prediction inputs.

The five EDA plots use Matplotlib, which is already included in the project environment. December 2011 ends on the 9th in this workbook, so its monthly total covers only part of the month. Gross purchases cover qualifying positive sales before subtracting returns.
