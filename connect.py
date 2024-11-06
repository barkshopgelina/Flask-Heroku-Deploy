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
        query = query.strip()  # Strip extra whitespace/newlines
        if query:  # Only execute non-empty queries
            try:
                cursor.execute(query)
                print(f"Executed query: {query[:30]}...")  # Print first 30 chars of query for debugging
            except mysql.connector.Error as err:
                print(f"Error executing query: {err}")

    # Commit the changes
    conn.commit()
    print("SQL queries executed successfully!")

    # Close cursor and connection
    cursor.close()
    conn.close()

except mysql.connector.Error as err:
    print(f"Error: {err}")
