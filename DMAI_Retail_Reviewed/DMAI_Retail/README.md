# Retail customer segmentation and repurchase prediction

## Run the project on Windows

1. Extract the ZIP. Open the extracted folder containing `config.py` in VS Code.
2. Put the full `Online Retail.xlsx` workbook in the `data` folder. If you already keep it in a project folder such as `data/raw`, change `DATA_FILE` in `config.py` to point there. The ZIP contains the code only.
3. Open Terminal → New Terminal. Create the environment and install the versions used to check the project. These commands use Python 3.12 and work from PowerShell without activation.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Run each line and wait for it to finish before starting the next one.

```powershell
.\.venv\Scripts\python.exe 01_load_raw.py
.\.venv\Scripts\python.exe 02_clean_build_db.py
.\.venv\Scripts\python.exe 03_build_features.py
.\.venv\Scripts\python.exe 04_predict_repurchase.py
.\.venv\Scripts\python.exe 05_segment_customers.py
```

| Stage | What to check on the full workbook |
| --- | --- |
| 01 | SQLite stores 541,909 raw transaction lines in `retail.db`. |
| 02 | The cleaned database contains 4,334 customers, 18,402 invoices and 391,148 invoice lines. The foreign-key check returns zero violations. `outputs/cleaning_log.csv` records removals in order. |
| 03 | 17 snapshot dates yield 33,153 customer-date rows. Each row describes a customer who made a qualifying purchase in the preceding 90 days. The target records whether they bought again in the next 30 days. |
| 04 | The terminal prints three validation periods and results on 8,615 held-out customer-date rows. Open `outputs/model_comparison.csv` and `outputs/confusion_matrices.png`. |
| 05 | The script clusters all 4,334 cleaned customers using purchases across the full period. Open `outputs/choose_k.png`, `outputs/segment_profiles.csv` and `outputs/segments.png`. K = 2 has the highest silhouette score in this run. |

If you are working on segmentation first, run 01, 02 and 05. Script 05 reads the cleaned sales tables directly.

## Check the difference between a label and a prediction

For customer 15061 on the snapshot of 1 March 2011, the previous 90 days contained 18 distinct orders and £22,671.33 in qualifying purchases. The next order was on 2 March, so the observed label is 1. That future order is used to check the prediction. The model only receives the features available on 1 March.

## How to interpret the results

- A snapshot is a dated view of a customer. The same customer can appear on many dates. The evaluation measures future purchases among existing, recently active customers.
- The last four snapshot dates form the test set. During model tuning, each validation fold also holds out entire snapshot dates. Training rows are eligible only after their full 30-day outcome window has finished.
- The default cluster count is the highest silhouette score among feasible values of K from 2 through 8. Look at the medians and cluster sizes before interpreting the assigned segment names.
- Monetary value and revenue share refer to qualifying positive purchases. Cancellation lines are recorded separately and have not been subtracted. Report these amounts as gross purchases after filtering.
- The cleaning rule keeps stock codes beginning with five digits. The duplicate rule treats lines with matching invoice, stock, quantity, timestamp, unit price and customer as duplicates. These are project assumptions.

## Optional demo run

The full workbook is the default. To try synthetic data, run `.\.venv\Scripts\python.exe 00_make_demo_data.py`, then select the demo CSV line in `config.py` instead of the workbook line. Run 01 through 05. Both modes write to the same database and outputs in a project folder. Use a separate extracted copy if keeping both sets of results.
