from flask import render_template, request, session, redirect, url_for
from user_management import register_user as reg_user, register_admin as reg_admin, authenticate_user as auth_user, authenticate_admin as auth_admin
from flask import current_app as app
import uuid
import os
from models import User, Admin  # Make sure to import your User and Admin models
from database import db  # Assuming db is your SQLAlchemy instance

# Register page for users
def user_register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        course = request.form.get('course')
        major = request.form.get('major')
        year_level = request.form.get('year_level')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check for required fields
        if not username or not email or not password:
            return render_template('user_register.html', error="All fields are required.")

        # Call register_user function to insert user into database
        try:
            reg_user(first_name, last_name, course, major, year_level, username, password, email)
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Error registering user: {e}")
            error_message = str(e)
            if "A user with the same details already exists." in error_message:
                return render_template('user_register.html', error="A user with the same details already exists.")
            elif "Username already exists." in error_message:
                return render_template('user_register.html', error="Username already exists. Please choose a different one.")
            return render_template('user_register.html', error="Registration failed. Please try again.")

    return render_template('user_register.html')


# Register page for admins
def admin_register():
    if Admin.query.count() >= 2:  # Assuming you have a count method or use query.count()
        return render_template('admin_register.html', error="Admin registration limit reached.")

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Call the registration function
        register_success = reg_admin(username, email, password)
        print("Register Success:", register_success)

        if register_success:
            return redirect(url_for('admin_login'))
        else:
            return render_template('admin_register.html', error="Username or email already exists.")

    return render_template('admin_register.html')


# Function to get user ID from username
def get_user_id_from_username(username):
    user = User.query.filter_by(username=username).first()  # Use SQLAlchemy ORM
    return user.id if user else None

# Function to get admin ID from username
def get_admin_id_from_username(username):
    admin = Admin.query.filter_by(username=username).first()  # Use SQLAlchemy ORM
    return admin.id if admin else None

# Login page
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error="All fields are required.")

        if auth_user(username, password):
            user = User.query.filter_by(username=username).first()
            if user:
                user.status = 'active'  # Update user status to 'active'
                user.last_active = datetime.utcnow()  # Update last active time
                db.session.commit()  # Commit the changes

                session['user_id'] = user.id
                session['username'] = username
                session['logged_in'] = True
                return redirect(url_for('home'))

        return render_template('login.html', error="Invalid username or password. Please try again.")

    return render_template('login.html')


# Admin login page
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('admin_login.html', error="All fields are required.")

        if auth_admin(username, password):
            admin = Admin.query.filter_by(username=username).first()  # Use SQLAlchemy ORM
            if admin:
                session['user_id'] = admin.id
                session['username'] = username
                session['logged_in'] = True
                return redirect(url_for('admin_index'))

        return render_template('admin_login.html', error="Invalid username or password. Please try again.")

    return render_template('admin_login.html')


# Logout
def logout():
    if 'username' in session:
        username = session['username']
        user = User.query.filter_by(username=username).first()  # Use SQLAlchemy ORM

        if user:
            user.status = None  # Clear user status
            db.session.commit()  # Commit the changes

        session.pop('user_id', None)
        session.pop('username', None)
        session.pop('logged_in', None)

    return redirect(url_for('index'))


# Admin Logout
def logout_admin():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


# Function to get user-specific saved project IDs
def get_user_saved_project_ids(user_id):
    user = User.query.get(user_id)  # Get user by ID
    if user:
        return [project.id for project in user.saved_projects]  # Assuming relationship is set up
    return []


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

        username = session.get('username')
        if not username:
            return redirect(url_for('login'))

        # Verify current password
        if not auth_user(username, current_password):
            return render_template('change_password.html', error="Current password is incorrect.")

        # Change password in the database
        user = User.query.filter_by(username=username).first()
        if user:
            user.password = new_password  # Update password
            db.session.commit()  # Commit the changes
            return render_template('change_password.html', success="Password changed successfully.")
        else:
            return render_template('change_password.html', error="Failed to change password. Please try again.")

    return render_template('change_password.html')


def get_user_by_id(user_id):
    return User.query.get(user_id)  # Use SQLAlchemy ORM to get user by ID

def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    print(f"User ID in edit_profile: {user_id}")  # Debugging line

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')
        course = request.form.get('course')
        major = request.form.get('major')
        year_level = request.form.get('year_level')

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
        user = User.query.get(user_id)  # Use SQLAlchemy ORM to get user
        if user:
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.email = email
            user.course = course
            user.major = major
            user.year_level = year_level
            user.profile_picture_url = profile_picture_url

            db.session.commit()  # Commit the changes
            return redirect(url_for('user_profile'))
        else:
            return render_template('edit_profile.html', error="Failed to update profile. Please try again.", user=get_user_by_id(user_id))

    user = get_user_by_id(user_id)
    print(f"User fetched in edit_profile: {user}")  # Debugging line
    if not user:
        return redirect(url_for('login'))  # Handle case where user is None
    return render_template('edit_profile.html', user=user)
