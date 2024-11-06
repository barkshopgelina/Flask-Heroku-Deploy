import mysql.connector
from urllib.parse import urlparse

# Your JawsDB URL (this part remains unchanged)
db_url = "mysql://boh3qmod5qu7lrr0:a4fupyk0zfvmpm2u@b4e9xxkxnpu2v96i.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/pf1eq480royf7mk9"

# Parse the URL
url = urlparse(db_url)

# Set up the database connection configuration using the parsed URL details
db_config = {
    "user": url.username,  # Extract username
    "password": url.password,  # Extract password
    "host": url.hostname,  # Extract hostname
    "port": url.port,  # Extract port
    "database": url.path[1:],  # Extract database name (remove leading '/')
    "raise_on_warnings": True  # Raise warnings if any, for better debugging
}

# Test connection separately
try:
    conn = mysql.connector.connect(**db_config)
    print("Successfully connected to the database!")
except mysql.connector.Error as err:
    print(f"Error connecting to database: {err}")
    exit()

# Attempt to execute SQL queries from file
try:
    cursor = conn.cursor()

    # Open the repository.sql file with the correct encoding (utf-8)
    with open("repository.sql", "r", encoding="utf-8") as file:
        sql_queries = file.read()

    # Split and execute each query
    queries = [q.strip() for q in sql_queries.split(';') if q.strip()]
    for query in queries:
        try:
            cursor.execute(query)
            print(f"Executed query: {query[:30]}...")  # Print first 30 chars of query for debugging
        except mysql.connector.Error as err:
            print(f"Error executing query: {err}")

    # Commit the changes
    conn.commit()
    print("SQL queries executed successfully!")

except mysql.connector.Error as err:
    print(f"Error: {err}")

finally:
    # Close cursor and connection
    if cursor:
        cursor.close()
    if conn:
        conn.close()
