from connect import get_database_connection
import mysql.connector
import bcrypt
from config import Config


from flask import request, flash, redirect, url_for
import bcrypt
import mysql.connector


# Function to add a new user
def admin_add_user():
    conn = get_database_connection()
    cursor = conn.cursor()

    # Retrieve form data
    student_ID = request.form.get('student_ID')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    course = request.form.get('course')

    # Validate inputs
    if not all([student_ID, first_name, last_name, course]):
        flash("All fields are required.", "danger")
        return redirect(url_for('add_user'))  # Replace with your route name

    try:
        # Query 1: Check for duplicate user details
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE first_name = %s AND last_name = %s
            AND course_ID = %s;
        """, (first_name, last_name, course))
        user_exists = cursor.fetchone()[0]

        if user_exists:
            flash("A user with the same details already exists.", "danger")
            return redirect(url_for('add_user'))

        # Query 2: Check if the student_ID already exists
        cursor.execute("""
            SELECT COUNT(*) FROM users WHERE student_ID = %s;
        """, (student_ID,))
        student_id_exists = cursor.fetchone()[0]

        if student_id_exists:
            flash("Student ID already exists.", "danger")
            return redirect(url_for('add_user'))

        # Insert user data into the database
        cursor.execute("""
            INSERT INTO users (student_ID, first_name, last_name, course_ID)
            VALUES (%s, %s, %s, %s)
        """, (student_ID, first_name, last_name, course))
        conn.commit()

        flash("User added successfully!", "success")
        return redirect(url_for('add_user'))  # Replace with your admin dashboard route

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
        conn.rollback()
        return redirect(url_for('add_user'))

    finally:
        cursor.close()
        conn.close()


def register_user(student_ID, email, password):
    conn = get_database_connection()
    cursor = conn.cursor()

    # Step 1: Verify if the student_ID exists in the database
    cursor.execute("""
        SELECT COUNT(*) FROM users WHERE student_ID = %s;
    """, (student_ID,))
    student_exists = cursor.fetchone()[0]

    if not student_exists:
        raise Exception("Invalid Student ID. Please ensure you are a registered CCS student.")

    # Step 2: Check if the email is already registered
    cursor.execute("""
        SELECT COUNT(*) FROM users WHERE email = %s;
    """, (email,))
    email_exists = cursor.fetchone()[0]

    if email_exists:
        raise Exception("Email already exists. Please use a different email.")

    # Step 3: Hash the password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Step 4: Update user details with email and password
    try:
        cursor.execute("""
            UPDATE users 
            SET email = %s, password_hash = %s 
            WHERE student_ID = %s;
        """, (email, password_hash, student_ID))
        conn.commit()
        print("User registered successfully!")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
        raise Exception("Failed to register user. Please try again.")
    finally:
        cursor.close()
        conn.close()


# Function to register a new admin
def register_admin(username=None, email=None, password=None):
    conn = get_database_connection()
    cursor = conn.cursor()

    # Check if the username or email already exists
    cursor.execute("SELECT COUNT(*) FROM admins WHERE username = %s OR email = %s", (username, email))
    admin_exists = cursor.fetchone()[0]

    if admin_exists:
        return False  # Username or email already exists

    # Hash the password
    password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insert admin data into the database
    try:
        cursor.execute("""
        INSERT INTO admins (username, email, password)
        VALUES (%s, %s, %s)
        """, (username, email, password))
        conn.commit()
        print("Admin registered successfully!")
        return True  # Successful registration
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
        return False  # Failed registration due to DB error
    finally:
        cursor.close()
        conn.close()


# Function to check the number of admins
def admin_count():
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM admins")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    return count

# Function to authenticate a user
def authenticate_user(student_ID, password):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE student_ID = %s", (student_ID,))
    user_data = cursor.fetchone()
    
    if user_data:
        stored_password_hash = user_data[0]
        if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            cursor.close()
            conn.close()
            return True

# Function to authenticate admin
def authenticate_admin(username, password):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM admins WHERE username = %s", (username,))
    admin_data = cursor.fetchone()
    
    if admin_data:
        stored_password = admin_data[0]
        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            cursor.close()
            conn.close()
            return True


def change_user_password(student_ID, new_password):
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        # Hash the new password
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # Update the password in the database
        cursor.execute("UPDATE users SET password_hash = %s WHERE student_ID = %s", (new_password_hash, student_ID))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def update_user_profile(user_id, email, profile_picture_url):
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE users
            SET email = %s, profile_picture_url = %s
            WHERE user_id = %s
        """, (email, profile_picture_url, user_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def allowed_file(filename):
    return Config.allowed_file(filename)
