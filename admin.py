from flask import render_template, flash, request, redirect, url_for, jsonify, send_file, abort, session
from connect import get_database_connection
from user import get_project_details
from pdf import PDFConfig
import io
import google.generativeai as genai
import fitz
import bcrypt
from datetime import datetime
from google.oauth2 import service_account
import google.generativeai as genai

# Set the path to your JSON credentials file
credentials_file_path = "config/generator-441311-f6c4bae822dc.json"  # Replace with the correct path to your credentials JSON file

# Create credentials from the JSON file
credentials = service_account.Credentials.from_service_account_file(credentials_file_path)

# Use the credentials with the genai module or any other Google API requiring authentication
genai.configure(credentials=credentials)

# Set up the model
project_id = "generator-441311"
location = "us-central1"
model = genai.GenerativeModel("gemini-1.5-flash-002")

def update_last_active():
    conn = get_database_connection()
    cursor = conn.cursor()

    # Update last_active for active users where it is NULL
    cursor.execute("UPDATE users SET last_active = NOW() WHERE last_active IS NULL AND status = 'active'")
    conn.commit()

    cursor.close()
    conn.close()

    return "Last active timestamps updated for active users.", 200

def admin_index():
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute('SELECT COUNT(*) FROM project_details WHERE is_deleted = FALSE;')
        count_projects = cursor.fetchone()['COUNT(*)']

        cursor.execute('SELECT COUNT(*) FROM project_details WHERE is_deleted = TRUE;')
        count_archive_projects = cursor.fetchone()['COUNT(*)']

        cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active';")
        count_active_users = cursor.fetchone()['COUNT(*)']

        cursor.execute('SELECT COUNT(*) FROM users;')
        count_users = cursor.fetchone()['COUNT(*)']

        cursor.execute('''
        SELECT 
            project_details.project_id, 
            project_details.Title, 
            project_details.Authors, 
            course.course_code, 
            major.major_code, 
            project_details.Publication_Year, 
            COUNT(user_library.project_id) AS save_count
        FROM 
            project_details
        JOIN 
            course 
            ON project_details.course_id = course.course_id
        JOIN 
            major 
            ON project_details.major_id = major.major_id
        INNER JOIN 
            user_library 
            ON user_library.project_id = project_details.project_id
        WHERE 
            project_details.is_deleted = FALSE  -- Exclude archived projects
        GROUP BY 
            project_details.project_id, 
            project_details.Title, 
            project_details.Authors, 
            course.course_code, 
            major.major_code, 
            project_details.Publication_Year
        ORDER BY 
            save_count DESC;
    ''')

        projects = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    
    return render_template('admin_index.html', count_projects=count_projects, count_archive_projects=count_archive_projects, count_active_users=count_active_users, count_users=count_users, projects=projects)


def admin_view_project(project_id):
    project = get_project_details(project_id)
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('library'))
        
    # Generate the URL to view the PDF
    pdf_url = url_for('view_pdf', identifier=project_id)

    return render_template('admin_view_project.html', project=project, pdf_url=pdf_url)

def view_pdf(identifier):
    project = get_project_details(identifier)
    
    if project and project['pdf_file']:
        pdf_data = project['pdf_file']  # Binary data of the PDF
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=False,  # Do not prompt for download
            download_name=f"{identifier}.pdf"  # Use download_name instead of attachment_filename
        )
    else:
        abort(404, description="PDF file not found.")
    
def library():
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            project_details.*, 
            course.course_code, 
            major.major_code
        FROM 
            project_details
        JOIN 
            course 
            ON project_details.course_id = course.course_id
        JOIN 
            major 
            ON project_details.major_id = major.major_id
        WHERE 
            project_details.is_deleted = FALSE
    """)

    projects = cursor.fetchall()
  
    return render_template('capstone_projects.html', projects=projects)

def archive():
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            project_details.*, 
            course.course_code, 
            major.major_code
        FROM 
            project_details
        JOIN 
            course 
            ON project_details.course_id = course.course_id
        LEFT JOIN 
            major 
            ON project_details.major_id = major.major_id
        WHERE 
            project_details.is_deleted = TRUE
    """)
    projects = cursor.fetchall()
  
    return render_template('archive.html', projects=projects)

def update_last_active():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_database_connection()
        cursor = conn.cursor()

        # Update the last_active field for the current user
        cursor.execute("UPDATE users SET last_active = %s WHERE user_id = %s", 
                       (datetime.now(), user_id))
        conn.commit()

        cursor.close()
        conn.close()

def active_users():
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)

    # Query to get active users with their last active timestamp
    cursor.execute('''
        SELECT 
            users.*, 
            course.course_code, 
            major.major_code
        FROM 
            users
        JOIN 
            major 
            ON users.major_ID = major.major_ID
        JOIN 
            course 
            ON users.course_ID = course.course_ID
        WHERE 
            status = 'active' 
        ORDER BY 
            last_active DESC
    ''')
    active_users = cursor.fetchall()

    cursor.close()
    conn.close()

    # Pass the active users data to the template
    return render_template('active_users.html', active_users=active_users)


def users():
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('''
        SELECT 
            users.*, 
            course.course_code, 
            major.major_code
        FROM 
            users
        JOIN 
            major 
            ON users.major_ID = major.major_ID
        JOIN 
            course 
            ON users.course_ID = course.course_ID;
    ''')
    users = cursor.fetchall()
  
    return render_template('users.html', users=users)

def reset_password(user_id):
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch the specific user by user_id
    cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
    users = cursor.fetchone()

    if not users:
        flash('User not found.', 'danger')
        return redirect(url_for('users'))

    if request.method == 'POST':
        new_password = request.form['new_password']

        # Hash the password with bcrypt
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        # Update the user's password in the database
        cursor.execute('UPDATE users SET password_hash = %s WHERE user_id = %s', (hashed_password, user_id))
        conn.commit()

        flash('Password reset successfully.', 'info')
    return render_template('reset_password.html', users=users)

def restore_project_in_db(project_id):
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check if the project exists in the `project_details` table and is archived
        cursor.execute("SELECT * FROM project_details WHERE project_id = %s AND is_deleted = TRUE", (project_id,))
        project = cursor.fetchone()

        if not project:
            return jsonify({'status': 'error', 'message': 'Project not found or already active'}), 404

        # Restore the project by setting is_deleted to FALSE
        cursor.execute("UPDATE project_details SET is_deleted = FALSE WHERE project_id = %s", (project_id,))
        conn.commit()

        return jsonify({'status': 'success', 'message': 'Project restored successfully'}), 200

    except Exception as e:
        print(f"Error: {e}")  # Log error for debugging
        conn.rollback()  # Rollback transaction on error
        return jsonify({'status': 'error', 'message': 'An internal server error occurred'}), 500

    finally:
        cursor.close()
        conn.close()

def restore_project_route():
    data = request.json
    project_id = data.get('project_id')

    if not project_id:
        return jsonify({'status': 'error', 'message': 'Project ID is required'}), 400

    # Call the renamed function and pass project_id
    return restore_project_in_db(project_id)

def archive_project():
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Parse JSON data from the request
        data = request.json
        project_id = data.get('project_id')

        if not project_id:
            return jsonify({'status': 'error', 'message': 'Project ID is required'}), 400

        # Check if the project exists
        cursor.execute("SELECT * FROM project_details WHERE project_id = %s AND is_deleted = FALSE", (project_id,))
        project = cursor.fetchone()

        if not project:
            return jsonify({'status': 'error', 'message': 'Project not found'}), 404

        # Archive the project by setting is_deleted to TRUE
        cursor.execute("UPDATE project_details SET is_deleted = TRUE WHERE project_id = %s", (project_id,))
        conn.commit()

        return jsonify({'status': 'success', 'message': 'Project archived successfully'}), 200

    except Exception as e:
        print(f"Error: {e}")  # Log the error for debugging
        conn.rollback()  # Rollback the transaction on error
        return jsonify({'status': 'error', 'message': 'An internal server error occurred'}), 500

    finally:
        cursor.close()
        conn.close()



def delete_user():
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)
    user_id = request.form['user_id']

    try:
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        cursor.close()
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Route for uploading projects
def upload_project():
    conn = get_database_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        # Check for uploaded file
        if "pdf" not in request.files:
            return "No file part"
        file = request.files["pdf"]
        if file.filename == "":
            return "No selected file"

        # Get form data
        title = request.form["title"]
        authors = request.form["authors"]
        course = request.form["course"]
        major = request.form["major"]
        year = request.form["year"]
        keywords = request.form["keywords"]
        abstract = request.form["abstract"]

        query = """
            SELECT COUNT(*) FROM project_details
            WHERE Title = %s 
            AND Authors = %s 
            AND course_ID = %s 
            AND major_ID = %s 
            AND Publication_Year = %s 
            AND Keywords = %s 
            AND Abstract = %s
        """

        cursor.execute(query, (title, authors, course, major, year, keywords, abstract))
        project_exists = cursor.fetchone()[0]

        if project_exists:
            flash("Project already exists", 'danger')
            return redirect(request.url)


        # Extract text from the uploaded PDF
        text = extract_text_from_pdf(file)

        # Save the capstone project details and PDF to the database
        save_result = save_pdf_to_db(title, authors, course, major, year, keywords, abstract, file)
        if save_result != "Success":
            return save_result

        # Generate the IMRaD format using a single prompt
        imrad_response = generate_imrad(text)

        # Save IMRaD format and text with line spacing to the database
        save_imrad_result = save_generated_imrad_and_spacing(title, imrad_response)
        if save_imrad_result != "Success":
            return save_imrad_result

        return render_template(
            "upload_project.html",
            message="Project uploaded successfully!"
        )

    return render_template("upload_project.html")

def extract_text_from_pdf(file):
    try:
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")
        full_text = ""

        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            full_text += page.get_text()

        return full_text
    
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def generate_imrad(text):
    prompt = "Summarize the attached PDF in IMRaD format (Introduction, Method, Results, and Discussion) without using section headers like 'Introduction,' 'Method,' 'Results,' and 'Discussion.' Structure the summary in detailed paragraphs, with each paragraph being long enough to fill at least one full page of a 5-page, short coupon bond. Ensure each paragraph is dense with information, capturing key points and details that are critical to understanding the study's background, research methodology, core findings, and implications or analysis. Include any specific terminology, data, or notable quotes from the original text to ensure that each section is comprehensive and maintains the depth of the original work. Do not limit the generated IMRaD format into 4 paragraphs only."
    response = model.generate_content(f"{prompt}: {text}")
    
    return response.text

def save_generated_imrad_and_spacing(title, imrad_text):
    try:
        # Replace line breaks with <br> tags for proper HTML rendering
        imrad_with_spacing = imrad_text.replace("\n", "<br>")

        connection = get_database_connection()
        if connection is None:
            return "Database connection failed"
        
        cursor = connection.cursor()

        # Update the project details to include the generated IMRaD with HTML line breaks
        query = """
        UPDATE project_details 
        SET generated_imrad = %s 
        WHERE Title = %s
        """
        cursor.execute(query, (imrad_with_spacing, title))

        connection.commit()
        cursor.close()
        connection.close()

        return "Success"
    
    except Exception as e:
        return f"Error saving IMRaD to database: {str(e)}"
    
def generate_citation_authors(authors):
    """Generate formatted authors for citation using AI."""
    prompt = (
        f"Format the following list of authors for citation purposes. "
        f"Format the names as follows: Last name, followed by a comma, then the first name initial and middle initial (each followed by a period). Add a comma after each author's name except the last one. Include an ampersand (&) before the final author's name. If an author has multiple first names, represent each with an initial and include all initials."
        f"Authors: {authors}"
    )
    response = model.generate_content(prompt)
    return response.text.strip()

def generate_citation_title(title):
    """Generate formatted title for citation using AI."""
    prompt = (
        f"Format the following title for citation in APA style. Enclose the title in double quotes. the Title of the work should be written in sentence case."
        f"Title: {title}"
    )
    response = model.generate_content(prompt)
    return response.text.strip()


def save_pdf_to_db(title, authors, course, major, year, keywords, abstract, file):
    """Save PDF and project details into the database."""
    try:
        connection = get_database_connection()
        if connection is None:
            return "Database connection failed"

        cursor = connection.cursor()

        file.seek(0)
        file_data = file.read()

        # Generate Citation_Title and Citation_Authors using AI
        citation_authors = generate_citation_authors(authors)
        citation_title = generate_citation_title(title)

        query = """
        INSERT INTO project_details (
            Title, Authors, Publication_Year, course_ID, major_ID, Keywords, Abstract, 
            pdf_file, Citation_Authors, Citation_Title
        ) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (title, authors, year, course, major, keywords, abstract, file_data, citation_authors, citation_title))

        connection.commit()
        cursor.close()
        connection.close()

        return "Success"
    
    except Exception as e:
        return f"Error saving PDF to database: {str(e)}"


# Route for editing a project
def edit_project(project_id):
    project = get_project_details(project_id)  # Fetch the project details from the database using the ID
    conn = get_database_connection()
    cursor = conn.cursor()

    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('library'))

    if request.method == 'POST':
        # Collect updated project details from the form
        title = request.form.get('title')
        authors = request.form.get('authors')
        course = request.form.get('course')
        major = request.form.get('major')
        year = request.form.get('year')
        keywords = request.form.get('keywords')
        abstract = request.form.get('abstract')

        # Default to the existing PDF file if no new file is uploaded
        pdf_data = project.get('pdf_file', b'')

        # Check if the project already exists
        query = """
            SELECT COUNT(*) FROM project_details
            WHERE Title = %s 
            AND Authors = %s 
            AND course_ID = %s 
            AND major_ID = %s 
            AND Publication_Year = %s 
            AND Keywords = %s 
            AND Abstract = %s
            """

        cursor.execute(query, (title, authors, course, major, year, keywords, abstract))
        project_exists = cursor.fetchone()[0]

        if project_exists:
            flash("Project already exists", 'danger')
            return redirect(request.url)

        # Check if a new file is uploaded
        if 'pdf' in request.files:
            file = request.files['pdf']
            if file.filename != '':
                if PDFConfig.allowed_upload_file(file.filename):
                    pdf_data = file.read()  # Read the new PDF file content
                else:
                    flash('Invalid file type.', 'danger')
                    return redirect(request.url)

        # Update the project details in the database
        success = update_project_details({
            'project_id': project_id,
            'pdf_file': pdf_data,
            'Title': title,
            'Authors': authors,
            'course_ID': course,
            'major_ID': major,
            'Publication_Year': year,
            'Keywords': keywords,
            'Abstract': abstract
        })

        if success:
            flash('Project details updated successfully!', 'info')
            return redirect(url_for('admin_view_project', project_id=project_id))
        else:
            flash('Failed to update project details. Please try again.', 'danger')

    cursor.close()
    conn.close()
    
    # Ensure Publication_Year is available
    year = project.get('Publication_Year', None)

    # Generate a range of years (you can adjust this range as needed)
    year_options = list(range(2021, 2025))

    return render_template('edit_project.html', project=project, year=year, year_options=year_options)


def update_project_details(project_details):
    conn = get_database_connection()
    cursor = conn.cursor()

    try:
        # Corrected update query
        sql = '''UPDATE project_details
                 SET pdf_file = %s,
                     Title = %s,
                     Authors = %s,
                     Publication_Year = %s,
                     course_ID = %s,
                     major_ID = %s,
                     Keywords = %s,
                     Abstract = %s
                 WHERE project_id = %s'''
        
        # Execute the query with provided details
        cursor.execute(sql, (
            project_details['pdf_file'],
            project_details['Title'],
            project_details['Authors'],
            project_details['Publication_Year'],
            project_details['course_ID'],
            project_details['major_ID'],
            project_details['Keywords'],
            project_details['Abstract'],
            project_details['project_id']
        ))
        
        # Commit the changes
        conn.commit()
        return True  # Indicate success
    except Exception as e:
        # Log the error for debugging
        print(f"Error updating project details: {e}")
        conn.rollback()
        return False  # Indicate failure
    finally:
        cursor.close()
        conn.close()
