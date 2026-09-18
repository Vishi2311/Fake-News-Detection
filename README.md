# Fake News Detection Using ML & NLP

A Machine Learning and Natural Language Processing based Fake News Detection System that combines a trained text classification model with external evidence verification.

The system accepts a news headline and/or article, generates an ML prediction, searches for external evidence, evaluates the evidence, and produces a final assessment.

## Project Overview

Traditional fake news classifiers rely mainly on patterns learned from historical datasets. This project extends that approach by combining:

1. Machine Learning based news classification
2. TF-IDF based text representation
3. Calibrated LinearSVC prediction
4. External evidence retrieval
5. Evidence relevance and quality analysis
6. Source trust evaluation
7. Supporting and contradicting evidence detection
8. Final decision generation
9. PostgreSQL prediction history
10. Streamlit web interface

The final system can produce three outcomes:

- REAL
- FAKE
- NEEDS VERIFICATION

## System Workflow

```text
User enters News
       |
       v
Headline / Article Processing
       |
       +----------------------+
       |                      |
       v                      v
Machine Learning        External Evidence
Prediction              Retrieval
       |                      |
       |                      v
       |               Evidence Analysis
       |                      |
       |                      v
       |               Evidence Scoring
       |                      |
       +----------+-----------+
                  |
                  v
           Final Decision Engine
                  |
        +---------+---------+
        |         |         |
        v         v         v
      REAL      FAKE    NEEDS VERIFICATION
                  |
                  v
          PostgreSQL Storage
                  |
                  v
           Streamlit Interface