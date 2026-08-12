-- ============================================================
-- FAKE NEWS DETECTION PROJECT
-- DAY 4 - POSTGRESQL INTEGRATION
-- ============================================================

-- View latest prediction history
SELECT
    id,
    title,
    prediction,
    confidence,
    predicted_at
FROM predictions
ORDER BY predicted_at DESC
LIMIT 20;


-- Total predictions
SELECT COUNT(*) AS total_predictions
FROM predictions;


-- FAKE percentage
SELECT
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE prediction = 'FAKE')
        / NULLIF(COUNT(*), 0),
        2
    ) AS fake_percentage
FROM predictions;


-- REAL percentage
SELECT
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE prediction = 'REAL')
        / NULLIF(COUNT(*), 0),
        2
    ) AS real_percentage
FROM predictions;


-- Highest confidence predictions
SELECT
    title,
    prediction,
    confidence
FROM predictions
ORDER BY confidence DESC
LIMIT 10;