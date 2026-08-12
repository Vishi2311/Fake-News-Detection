import psycopg2

try:
    connection = psycopg2.connect(
        host="localhost",
        database="olist_analysis",
        user="postgres",
        password="vishesh@#2311",
        port="5432"
    )

    print("PostgreSQL connection successful!")

    connection.close()

except Exception as e:
    print("Database connection failed!")
    print(e)