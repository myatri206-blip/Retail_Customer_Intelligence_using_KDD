
# Retail Customer Intelligence Using KDD

## Project Overview
This project applies Knowledge Discovery in Databases
(KDD) to retail transaction data.

## Dataset
UCI Online Retail Dataset

## Technologies
- Python
- SQLite
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Scikit-learn

## Member 1: Data Analysis and Customer Segmentation
1. Dataset import into SQLite
2. Data cleaning and preprocessing
3. SQL analysis
4. Exploratory Data Analysis
5. RFM feature engineering
6. K-Means customer segmentation
7. Elbow method and silhouette evaluation

## Member 2: Repeat-Purchase Prediction
- Time-based feature engineering
- Decision Tree classification
- Random Forest classification
- Model evaluation
- Streamlit dashboard integration

## Setup
Install dependencies:

    python -m pip install -r requirements.txt

Download the UCI Online Retail dataset and place
Online Retail.xlsx inside the data folder.

Run the Member 1 pipeline:

    python src/01_import_data.py
    python src/02_clean_data.py
    python src/03_sql_analysis.py
    python src/04_eda.py
    python src/05_rfm_analysis.py
    python src/06_clustering.py

## Note
Large datasets, local databases and generated
outputs are excluded from Git.
