-- ============================================================
-- FAKE NEWS DETECTION PROJECT
-- DAY 1 - DATABASE AND TABLE SETUP
-- ============================================================

-- Database used by this project:
-- postgres

-- Create the predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    prediction VARCHAR(10) NOT NULL,
    confidence NUMERIC(5,2),
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Check that the table exists
SELECT *
FROM predictions;