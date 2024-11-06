import mysql.connector
from urllib.parse import urlparse

# Replace with your JawsDB URL or use environment variable
db_url = "mysql://boh3qmod5qu7lrr0:a4fupyk0zfvmpm2u@b4e9xxkxnpu2v96i.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/pf1eq480royf7mk9"

# Parse the URL
url = urlparse(db_url)

# Set up database connection using the parsed information
db_config = {
    "user": url.username,
    "password": url.password,
    "host": url.hostname,
    "port": url.port,
    "database": url.path[1:]  # remove the leading '/'
}

# Attempt to connect to the MySQL database
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    print("Successfully connected to the database!")

    # Open the repository.sql file with the correct encoding (utf-8)
    with open("repository.sql", "r", encoding="utf-8") as file:
        sql_queries = file.read()

    # Execute each query from the file
    for query in sql_queries.split(";"):
        if query.strip():  # Skip empty queries
            cursor.execute(query)

    # Commit the changes
    conn.commit()
    print("SQL queries executed successfully!")

    # Close cursor and connection
    cursor.close()
    conn.close()

except mysql.connector.Error as err:
    print(f"Error: {err}")
