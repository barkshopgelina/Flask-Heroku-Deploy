from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt
from config import Config
from models import User, Admin  # Assuming you have SQLAlchemy models defined for User and Admin

# Create your database engine
DATABASE_URL = 'postgresql://u27l99coqanlt1:pde56cc32f516f04b002f5e4ca52627e5dac2c5f745ad8736bb9ea693430b14af@c9pv5s2sq0i76o.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d3r9dbg3e66ibn'  # Example: 'postgresql://user:password@localhost/mydatabase'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Function to register a new user
def register_user(first_name=None, last_name=None, course=None, major=None, year_level=None, username=None, password=None, email=None):
    session = Session()

    # Check if the user exists based on first name, last name, username, email, course, and major
    user_exists = session.query(User).filter(
        User.first_name == first_name,
        User.last_name == last_name,
        User.email == email,
        User.course == course,
        User.major == major,
        User.username == username
    ).count()

    if user_exists:
        raise Exception("A user with the same details already exists.")

    # Check if the username already exists
    username_exists = session.query(User).filter(User.username == username).count()

    if username_exists:
        raise Exception("Username already exists.")

    # Hash the password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insert user data into the database
    try:
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            course=course,
            major=major,
            year_level=year_level,
            username=username,
            password_hash=password_hash,
            email=email
        )
        session.add(new_user)
        session.commit()
        print("User registered successfully!")
    except Exception as err:
        print(f"Error: {err}")
        session.rollback()
    finally:
        session.close()

# Function to register a new admin
def register_admin(username=None, email=None, password=None):
    session = Session()

    # Check if the username or email already exists
    admin_exists = session.query(Admin).filter(
        (Admin.username == username) | (Admin.email == email)
    ).count()

    if admin_exists:
        return False  # Username or email already exists

    # Hash the password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insert admin data into the database
    try:
        new_admin = Admin(username=username, email=email, password=password_hash)
        session.add(new_admin)
        session.commit()
        print("Admin registered successfully!")
        return True  # Successful registration
    except Exception as err:
        print(f"Error: {err}")
        session.rollback()
        return False  # Failed registration due to DB error
    finally:
        session.close()

# Function to check the number of admins
def admin_count():
    session = Session()
    count = session.query(Admin).count()
    session.close()
    return count

# Function to authenticate a user
def authenticate_user(username, password):
    session = Session()
    user = session.query(User).filter(User.username == username).first()
    
    if user:
        stored_password_hash = user.password_hash
        if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            session.close()
            return True
    session.close()
    return False

# Function to authenticate admin
def authenticate_admin(username, password):
    session = Session()
    admin = session.query(Admin).filter(Admin.username == username).first()
    
    if admin:
        stored_password = admin.password
        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            session.close()
            return True
    session.close()
    return False

# Function to change user password
def change_user_password(username, new_password):
    session = Session()
    try:
        # Hash the new password
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # Update the password in the database
        user = session.query(User).filter(User.username == username).first()
        if user:
            user.password_hash = new_password_hash
            session.commit()
            return True
    except Exception as err:
        print(f"Error: {err}")
        session.rollback()
        return False
    finally:
        session.close()

# Function to update user profile
def update_user_profile(user_id, first_name, last_name, username, email, course, major, year_level, profile_picture_url):
    session = Session()
    try:
        user = session.query(User).filter(User.id == user_id).first()  # Assuming you have an 'id' field in User model
        if user:
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.email = email
            user.course = course
            user.major = major
            user.year_level = year_level
            user.profile_picture_url = profile_picture_url
            session.commit()
            return True
    except Exception as e:
        print(f"Error updating user profile: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def allowed_file(filename):
    return Config.allowed_file(filename)
