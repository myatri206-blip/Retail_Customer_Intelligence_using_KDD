
-- QUERY 1: Total transaction rows and unique customers

SELECT
    COUNT(*) AS TotalRows,
    COUNT(DISTINCT CustomerID) AS TotalCustomers,
    COUNT(DISTINCT InvoiceNo) AS TotalOrders
FROM clean_transactions;


-- QUERY 2: Total sales revenue

SELECT
    ROUND(SUM(Revenue), 2) AS TotalRevenue
FROM clean_transactions;


-- QUERY 3: Top 10 customers by spending

SELECT
    CustomerID,
    ROUND(SUM(Revenue), 2) AS TotalSpent,
    COUNT(DISTINCT InvoiceNo) AS TotalOrders
FROM clean_transactions
GROUP BY CustomerID
ORDER BY TotalSpent DESC
LIMIT 10;


-- QUERY 4: Top 10 products by revenue

SELECT
    StockCode,
    Description,
    SUM(Quantity) AS UnitsSold,
    ROUND(SUM(Revenue), 2) AS TotalRevenue
FROM clean_transactions
GROUP BY StockCode, Description
ORDER BY TotalRevenue DESC
LIMIT 10;


-- QUERY 5: Monthly sales revenue

SELECT
    SUBSTR(InvoiceDate, 1, 7) AS SalesMonth,
    ROUND(SUM(Revenue), 2) AS MonthlyRevenue
FROM clean_transactions
GROUP BY SalesMonth
ORDER BY SalesMonth;


-- QUERY 6: Revenue by country

SELECT
    Country,
    COUNT(DISTINCT InvoiceNo) AS TotalOrders,
    ROUND(SUM(Revenue), 2) AS TotalRevenue
FROM clean_transactions
GROUP BY Country
ORDER BY TotalRevenue DESC
LIMIT 10;
