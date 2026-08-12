# 📰 Fake News Detection System

A Machine Learning based Fake News Detection System that classifies
news as **REAL** or **FAKE** using Natural Language Processing (NLP).

The system provides a prediction along with a confidence score and
stores prediction history in PostgreSQL.

---

## 🚀 Project Features

- News title and article input
- Fake/Real news classification
- TF-IDF based text feature extraction
- Machine Learning prediction
- Confidence score
- Streamlit web interface
- PostgreSQL prediction storage
- Prediction history
- Secure database credentials using `.env`
- Error handling for database operations

---

## 🧠 Technologies Used

### Programming
- Python

### Machine Learning
- Scikit-learn
- LinearSVC
- CalibratedClassifierCV
- TF-IDF Vectorization

### Database
- PostgreSQL
- psycopg2

### Web Application
- Streamlit

### Data Processing
- Pandas
- NumPy

---

## 📂 Project Structure

```text
Fake-News-Detection/
│
├── app/
│   └── app.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── models/
│   ├── calibrated_fake_news_model.pkl
│   ├── fake_news_model.pkl
│   └── tfidf_vectorizer.pkl
│
├── notebooks/
│   ├── 01_data_preparation.ipynb
│   └── 02_tfidf_preprocessing.ipynb
│
├── src/
│   ├── db_test.py
│   ├── predict.py
│   └── test_predictions.py
│
├── sql/
│   ├── Fake_News_Day1_SQL.sql
│   ├── Fake_News_Day2_SQL.sql
│   └── Fake_News_Day4_SQL.sql
│
├── .env
├── .gitignore
├── README.md
└── requirements.txt