SELECT *
FROM predictions;

SELECT *
FROM predictions
ORDER BY predicted_at DESC;

SELECT
    prediction,
    COUNT(*) AS total
FROM predictions
GROUP BY prediction;