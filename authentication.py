from flask import render_template, request, session, redirect, url_for
from user_management import register_user as reg_user, register_admin as reg_admin, authenticate_user as auth_user, authenticate_admin as auth_admin, admin_count, change_user_password, update_user_profile, allowed_file
from werkzeug.utils import secure_filename
from connect import get_database_connection
import uuid as uuid
from flask import current_app as app
import os


# Register page for users
def user_register():
    if request.method == 'POST':
        student_ID = request.form.get('student_ID')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check for required fields
        if not student_ID or not email or not password:
            return render_template('user_register.html', error="All fields are required.")

        # Validate and register the user
        try:
            reg_user(student_ID, email, password)
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Error registering user: {e}")
            return render_template('user_register.html', error=str(e))

    # Render the registration form for GET requests
    return render_template('user_register.html')


# Register page for admins
def admin_register():
    if admin_count() >= 2:
        return render_template('admin_register.html', error="Admin registration limit reached.")

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Call the registration function
        register_success = reg_admin(username, email, password)  # Correct function call
        
        print("Register Success:", register_success)  # Debugging line

        if register_success:
            return redirect(url_for('admin_login'))
        else:
            return render_template('admin_register.html', error="Username or email already exists.")

    return render_template('admin_register.html')



# Function to get user ID from student_ID
def get_user_id_from_student_ID(student_ID):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE student_ID = %s", (student_ID,))
    user_id = cursor.fetchone()
    conn.close()
    if user_id:
        return user_id[0]
    return None

# Function to get admin ID from username
def get_admin_id_from_username(username):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT admin_id FROM admins WHERE username = %s", (username,))
    admin_id = cursor.fetchone()
    conn.close()
    if admin_id:
        return admin_id[0]
    return None

# Login page
def login():
    if request.method == 'POST':
        student_ID = request.form.get('student_ID')
        password = request.form.get('password')

        if not student_ID or not password:
            return render_template('login.html', error="All fields are required.")

        if auth_user(student_ID, password):
            conn = get_database_connection()
            cursor = conn.cursor()

            # Update user status to 'active' in the database
            cursor.execute("UPDATE users SET status = 'active', last_active = NOW() WHERE student_ID = %s", (student_ID,))
            conn.commit()

            cursor.close()
            conn.close()

            user_id = get_user_id_from_student_ID(student_ID)
            session['user_id'] = user_id
            session['student_ID'] = student_ID
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid student ID or password. Please try again.")

    return render_template('login.html')


# Admin ogin page
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('admin_login.html', error="All fields are required.")

        if auth_admin(username, password):
            admin_id = get_admin_id_from_username(username)
            session['user_id'] = admin_id
            session['username'] = username
            session['logged_in'] = True
            return redirect(url_for('admin_index'))
        else:
            return render_template('admin_login.html', error="Invalid username or password. Please try again.")

    return render_template('admin_login.html')

# Logout
def logout():
     # Clear user status in the database
    if 'student_ID' in session:
        username = session['student_ID']

        conn = get_database_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET status = NULL WHERE student_ID = %s", (username,))
        conn.commit()

        cursor.close()
        conn.close()

        # Clear session variables
        session.pop('user_id', None)
        session.pop('student_ID', None)
        session.pop('logged_in', None)
        
    return redirect(url_for('index'))

#Admin Logout
def logout_admin():
    # Clear admin session data
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# Function to get user-specific saved project IDs
def get_user_saved_project_ids(user_id):
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT project_id FROM user_library WHERE user_id = %s", (user_id,))
        saved_project_ids = [row[0] for row in cursor.fetchall()]
        return saved_project_ids
    finally:
        cursor.close()
        conn.close()

# Change Password
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_password or not new_password or not confirm_password:
            return render_template('change_password.html', error="All fields are required.")

        if new_password != confirm_password:
            return render_template('change_password.html', error="New password and confirm password do not match.")

        student_ID = session.get('student_ID')
        if not student_ID:
            return redirect(url_for('login'))

        # Verify current password
        if not auth_user(student_ID, current_password):
            return render_template('change_password.html', error="Current password is incorrect.")

        # Change password in the database
        if change_user_password(student_ID, new_password):
            return render_template('change_password.html', success="Password changed successfully.")
        else:
            return render_template('change_password.html', error="Failed to change password. Please try again.")

    return render_template('change_password.html')


def get_user_by_id(user_id):
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)  # Enable dictionary cursor
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    print(f"User ID in edit_profile: {user_id}")  # Debugging line

    if request.method == 'POST':
        email = request.form.get('email')
        
        # Initialize profile_picture_url
        profile_picture_url = request.form.get('profile_picture_url')

        # Handle file upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + "_" + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                profile_picture_url = os.path.join('static/images', unique_filename)

        # Update user profile
        success = update_user_profile(user_id, email, profile_picture_url)
        if success:
            return redirect(url_for('user_profile'))
        else:
            return render_template('edit_profile.html', error="Failed to update profile. Please try again.", user=get_user_by_id(user_id))

    user = get_user_by_id(user_id)
    print(f"User fetched in edit_profile: {user}")  # Debugging line
    if not user:
        return redirect(url_for('login'))  # Handle case where user is None
    return render_template('edit_profile.html', user=user)
