from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# Define the database name
DATABASE = 'your_database_name.db'  # Replace with your actual database name

def get_database_connection():
    """Creates a database connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DATABASE)
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    """Handles the PDF file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'File type is not PDF'}), 400

    try:
        # Ensure the uploads directory exists
        if not os.path.exists('uploads'):
            os.makedirs('uploads')
        
        # Save the uploaded PDF file
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        return jsonify({'message': 'File uploaded successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-imrad', methods=['POST'])
def generate_imrad():
    """Generates and saves an IMRaD document."""
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Extract necessary fields for IMRaD
    title = data.get('title')
    introduction = data.get('introduction')
    methods = data.get('methods')
    results = data.get('results')
    discussion = data.get('discussion')

    if not all([title, introduction, methods, results, discussion]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_database_connection()
        if conn is None:
            return jsonify({'error': 'Failed to connect to the database'}), 500

        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO imrad (title, introduction, methods, results, discussion) VALUES (?, ?, ?, ?, ?)',
            (title, introduction, methods, results, discussion)
        )
        conn.commit()
        return jsonify({'message': 'IMRaD generated and saved successfully'}), 201
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)
