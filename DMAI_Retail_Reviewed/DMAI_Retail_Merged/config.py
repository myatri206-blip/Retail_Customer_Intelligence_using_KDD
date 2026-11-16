"""
config.py  -  every setting in ONE place.
If your teacher asks "what if the window was 60 days?", you change one number here
and re-run. This is called 'parameterisation' and it makes experiments repeatable.
"""
from pathlib import Path

BASE = Path(__file__).parent
DATA_FILE = BASE / "data" / "Online Retail.xlsx"   # the REAL UCI file (put it here)
# DATA_FILE = BASE / "data" / "online_retail_demo.csv"   # fake demo data from 00_make_demo_data.py
DB_PATH = BASE / "retail.db"
OUT = BASE / "outputs"
OUT.mkdir(exist_ok=True)

HISTORY_DAYS = 90      # how far back we look to describe a customer's behaviour
HORIZON_DAYS = 30      # how far forward we look to see if they came back
SNAPSHOT_STEP_DAYS = 15  # we take a "photo" of all customers every 15 days
LABEL_COLUMN = f"repurchased_{HORIZON_DAYS}d"
TEST_FRACTION = 0.25   # last 25% of snapshots are kept aside for testing
K_RANGE = range(2, 9)  # K values to try for K-Means
K_FINAL = None         # None = pick best silhouette among valid K_RANGE values; or set e.g. 4
RANDOM_STATE = 42      # makes results reproducible (same numbers every run)
