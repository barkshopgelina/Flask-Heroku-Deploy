from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Helper function to create a database connection using SQLAlchemy
def get_database_connection():
    try:
        # Use the Heroku DATABASE_URL directly
        DATABASE_URL = "postgresql://u27l99coqanlt1:pde56cc32f516f04b002f5e4ca52627e5dac2c5f745ad8736bb9ea693430b14af@c9pv5s2sq0i76o.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d3r9dbg3e66ibn"
        
        # Create an engine for connecting to the database
        engine = create_engine(DATABASE_URL, echo=True)  # `echo=True` will show SQL queries in the output
        Session = sessionmaker(bind=engine)
        session = Session()
        print("Connected to the database")
        return session
    except Exception as e:
        print(f"Error: {e}")
        return None

# Function to execute SQL script (migration) using SQLAlchemy
def migrate_database():
    session = get_database_connection()
    if session:
        try:
            # Try reading the file with UTF-8 encoding
            with open('repository.sql', 'r', encoding='utf-8', errors='ignore') as file:
                sql_script = file.read()

            # Split the SQL script into individual statements
            statements = sql_script.split(';')

            # Execute each statement
            for statement in statements:
                if statement.strip():
                    session.execute(text(statement))  # Execute the SQL statement
            session.commit()  # Commit the transaction
            print("Migration completed successfully")
        except Exception as err:
            print(f"Error: {err}")
        finally:
            session.close()

if __name__ == "__main__":
    migrate_database()
