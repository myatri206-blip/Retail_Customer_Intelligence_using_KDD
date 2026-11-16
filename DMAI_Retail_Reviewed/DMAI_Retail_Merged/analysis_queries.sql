-- Team merge example 1. Monthly positive product purchases.
SELECT substr(InvoiceDate, 1, 7) AS month, COUNT(DISTINCT InvoiceNo) AS orders,
       ROUND(SUM(Revenue), 2) AS gross_purchases
FROM clean_transactions
GROUP BY month
ORDER BY month;

-- Team merge example 2. Ten products with the highest qualifying sales.
SELECT StockCode, Description, ROUND(SUM(Revenue), 2) AS gross_purchases
FROM clean_transactions
GROUP BY StockCode, Description
ORDER BY gross_purchases DESC, StockCode
LIMIT 10;

-- Team merge example 3. Ten countries with the highest qualifying sales.
SELECT Country, COUNT(DISTINCT CustomerID) AS customers,
       ROUND(SUM(Revenue), 2) AS gross_purchases
FROM clean_transactions
GROUP BY Country
ORDER BY gross_purchases DESC, Country
LIMIT 10;
