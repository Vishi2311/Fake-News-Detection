-- ============================================================
-- FAKE NEWS DETECTION PROJECT
-- DAY 2 - PREDICTION DATA ANALYSIS
-- ============================================================

-- View all stored predictions
SELECT *
FROM predictions;


-- Count total predictions
SELECT COUNT(*) AS total_predictions
FROM predictions;


-- Count FAKE predictions
SELECT COUNT(*) AS fake_predictions
FROM predictions
WHERE prediction = 'FAKE';


-- Count REAL predictions
SELECT COUNT(*) AS real_predictions
FROM predictions
WHERE prediction = 'REAL';


-- Compare FAKE and REAL predictions
SELECT
    prediction,
    COUNT(*) AS total
FROM predictions
GROUP BY prediction
ORDER BY prediction;


-- Average confidence
SELECT
    prediction,
    ROUND(AVG(confidence), 2) AS average_confidence
FROM predictions
GROUP BY prediction;