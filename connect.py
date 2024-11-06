import mysql.connector
import os
from mysql.connector import Error

# Helper function to get a database connection
def get_database_connection():
    try:
        connection = mysql.connector.connect(
            host="b4e9xxkxnpu2v96i.cbetxkdyhwsb.us-east-1.rds.amazonaws.com",
            user="boh3qmod5qu7lrr0",
            password="a4fupyk0zfvmpm2u",
            database="pf1eq480royf7mk9"
        )
        print("Connected to the database")
        return connection
    except Error as err:
        print(f"Error: {err}")
        return None

# Test the connection
if __name__ == "__main__":
    conn = get_database_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        for table in cursor.fetchall():
            print(table)
        cursor.close()
        conn.close()
