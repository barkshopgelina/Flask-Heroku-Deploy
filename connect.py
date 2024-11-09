import mysql.connector
import os
from urllib.parse import urlparse

# Helper function to get a database connection
def get_database_connection():
    try:
        # Get the JAWSDB URL from environment variables
        jawsdb_url = os.getenv('JAWSDB_URL')  # Fetch the actual environment variable
        if jawsdb_url is None:
            print("Error: JAWSDB_URL environment variable is not set.")
            return None
        
        # Parse the URL
        url = urlparse(jawsdb_url)
        
        # Connect to the database using the parsed details
        connection = mysql.connector.connect(
            host=url.hostname,
            user=url.username,
            password=url.password,
            database=url.path[1:]  # Removing the leading '/'
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
