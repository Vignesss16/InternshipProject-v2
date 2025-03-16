from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",  # Replace with actual password
        database="internship_db"
    )

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/internship-details')
def internship_details():
    return render_template("redirect.html")  # Redirects to the backend's /internships

@app.route('/upload', methods=['GET', 'POST'])
def upload_internship():
    if request.method == 'POST':
        year = request.form['year']
        company_name = request.form['company_name']
        location = request.form['location']
        work_details = request.form['work_details']
        stipend = request.form.get('stipend', 'N/A')
        duration = request.form['duration']
        from_date = request.form['from_date']
        to_date = request.form['to_date']
        internship_type = request.form['internship_type']
        internal_details = request.form.get('internal_details', '')

        # Handling file upload
        certificate = request.files['certificate']
        if certificate:
            cert_path = os.path.join(app.config['UPLOAD_FOLDER'], certificate.filename)
            certificate.save(cert_path)
        else:
            cert_path = None

        # Store details in the database
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO internships (year, company_name, location, work_details, stipend, duration, from_date, to_date, 
                                     internship_type, internal_details, certificate_path) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (year, company_name, location, work_details, stipend, duration, from_date, to_date, internship_type, internal_details, cert_path))
        conn.commit()
        conn.close()

        return redirect(url_for('home'))

    return render_template("upload.html")

if __name__ == "__main__":
    app.run(port=5001, debug=True)
