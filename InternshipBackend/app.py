
import os
from flask import Flask, render_template, request, redirect, session, url_for, send_file, flash
import pandas as pd
import mysql.connector
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime



app = Flask(__name__)
app.secret_key = "your_secret_key"  # We have to this Change before hosting

# Configure Upload Folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database Connection Function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # we have Change this before hosting
        password="Vignesh@123",
        database="internship_db"
    )

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home Route
@app.route('/')
def home():
    return render_template('index.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, prn, password FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['prn'] = user['prn'].strip()
            session['role'] = 'student'  # Hardcode role as student

            return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid email or password", "error")

    return render_template('login.html')






# @app.route('/faculty_login', methods=['GET', 'POST'])
# def faculty_login():
#     if request.method == 'POST':
#         password = request.form['password']
        
#         FACULTY_SECRET_PASSWORD = "siesfaculty@123"

#         if password == FACULTY_SECRET_PASSWORD:
#             session['user'] = 'faculty_user'
#             session['role'] = 'faculty'
#             return redirect(url_for('faculty_dashboard'))
#         else:
#             flash("Invalid faculty password.")
#             return redirect(url_for('faculty_login'))

#     return render_template('faculty_login.html')


@app.route('/faculty_login', methods=['GET', 'POST'])
def faculty_login():
    if request.method == 'POST':
        entered_password = request.form['password']
        correct_password = "sies@faculty"  # You can change this

        if entered_password == correct_password:
            session['user_id'] = 'faculty_admin'
            session['role'] = 'faculty'
            return redirect(url_for('faculty_dashboard'))
        else:
            flash("Incorrect access password", "error")

    return render_template('faculty_login.html')




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        prn = request.form.get('prn') 
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        # role = request.form.get('role')

        if not name or not email or not password or not prn:
            flash("All fields are required!", "error")
            return redirect(url_for('register'))

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (name, email, prn, password, role) VALUES (%s, %s, %s, %s, %s)", 
               (name, email, prn, hashed_password, 'student'))
        db.commit()
        cursor.close()
        db.close()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')



@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != "student":
        return redirect(url_for('login'))

    # ✅ Refresh session if prn or role is missing
    if not session.get('prn') or not session.get('role'):
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT prn, role FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            session['prn'] = user['prn'].strip()
            session['role'] = user['role']

    return render_template('student_dashboard.html')


# Faculty Dashboard
@app.route('/faculty_dashboard')
def faculty_dashboard():
    if 'user_id' not in session or session['role'] != "faculty":
        return redirect(url_for('faculty_login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM internships")
    internships = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('faculty_dashboard.html', internships=internships)

# Internship Upload (Students Only)
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session or session['role'] != "student":
        return redirect(url_for('login'))

    if request.method == 'POST':
        prn = session['prn']
        year = request.form.get('year')
        company_name = request.form.get('company_name')
        location = request.form.get('location')
        work_details = request.form.get('work_details')
        stipend = request.form.get('stipend') or None
        duration = request.form.get('duration')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        internship_type = request.form.get('internship_type')
        internal_details = request.form.get('internal_details') if internship_type == "Internal" else None

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT name FROM users WHERE prn = %s", (prn,))
        student = cursor.fetchone()

        if not student:
            flash("Student not found!", "error")
            return redirect(url_for('upload'))

        student_name = student['name']
        file = request.files.get('certificate')
        filename = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

        cursor.execute("""
            INSERT INTO internships (prn, student_name, year, company_name, location, work_details, stipend, duration, 
                                     from_date, to_date, internship_type, internal_details, certificate_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (prn, student_name, year, company_name, location, work_details, stipend, duration, 
              from_date, to_date, internship_type, internal_details, filename))

        db.commit()
        cursor.close()
        db.close()

        flash("Internship details uploaded successfully!", "success")
        return redirect(url_for('student_dashboard'))

    return render_template('upload.html')




@app.route('/internships', methods=['GET'])
def internships():
    print("SESSION DEBUG:", dict(session))

    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 🛠️ Fix: refresh session if empty
    if not session.get('prn') or not session.get('role'):
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT prn, role FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            session['prn'] = user['prn'].strip()
            session['role'] = user['role']

    prn = session.get('prn')
    role = session.get('role')

    print("DEBUG: Session PRN:", prn)  # 🐞 Add this if needed

    search = request.args.get('search', '').strip()
    year = request.args.get('year', '').strip()
    internship_type = request.args.get('internship_type', '').strip()
    academic_year = request.args.get('academic_year', '').strip()

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Vignesh@123",
        database="internship_db"
    )
    cursor = conn.cursor(dictionary=True)

    # Base query
    query = "SELECT * FROM internships WHERE 1=1"
    params = []

    # If student, restrict data to their own PRN
    if role == 'student' and prn:
        query += " AND prn = %s"
        params.append(prn)

    # Filters
    if search:
        query += " AND (prn LIKE %s OR student_name LIKE %s OR company_name LIKE %s OR location LIKE %s)"
        like_search = f"%{search}%"
        params.extend([like_search] * 4)

    if year:
        query += " AND year = %s"
        params.append(year)

    if internship_type:
        query += " AND internship_type = %s"
        params.append(internship_type)

    cursor.execute(query, params)
    internships = cursor.fetchall()

    cursor.close()
    conn.close()

    # Academic year filtering in Python
    if academic_year:
        def get_academic_year(from_date):
            if isinstance(from_date, datetime):
                year = from_date.year
            elif isinstance(from_date, str):
                from_date = datetime.strptime(from_date, '%Y-%m-%d')
                year = from_date.year
            elif hasattr(from_date, 'year'):  # handles datetime.date
                year = from_date.year
            else:
                return None

            if from_date.month >= 6:
                return f"{year}-{year + 1}"
            else:
                return f"{year - 1}-{year}"

        internships = [
            i for i in internships
            if get_academic_year(i.get('from_date')) == academic_year
        ]

    
    print("🔍 PRN from session:", session.get('prn'))
    print("🔍 PRN sent to template:", prn)

    return render_template(
        'internships.html',
        internships=internships,
        role=role,
        prn=prn,
        current_year=datetime.now().year
    )


#Saala tension hai
@app.route('/edit_internship/<int:id>', methods=['GET', 'POST'])
def edit_internship(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Vignesh@123",
        database="internship_db"
    )
    cursor = conn.cursor(dictionary=True)

    # Fetch existing internship details
    cursor.execute("SELECT * FROM internships WHERE id = %s", (id,))
    internship = cursor.fetchone()

    if request.method == 'POST':
        year = request.form['year']
        company_name = request.form['company_name']
        location = request.form['location']
        work_details = request.form['work_details']

        # Treat 'None' string and empty string as None
        stipend = request.form.get('stipend')
        stipend = int(stipend) if stipend and stipend.strip().lower() != 'none' else None

        duration = request.form.get('duration')
        duration = int(duration) if duration and duration.strip().lower() != 'none' else None

        
        from_date = request.form['from_date']
        to_date = request.form['to_date']
        internship_type = request.form['internship_type']
        internal_details = request.form.get('internal_details') #added this 
        # Get uploaded certificate (optional)
        certificate = request.files.get('certificate')
        if certificate and certificate.filename:
            filename = secure_filename(certificate.filename)
            certificate.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = internship.get('certificate_path')  # fallback to existing

        # Update query
        update_query = """
            UPDATE internships SET
                year = %s,
                company_name = %s,
                location = %s,
                work_details = %s,
                stipend = %s,
                duration = %s,
                from_date = %s,
                to_date = %s,
                internship_type = %s,
                internal_details = %s,
                certificate_path = %s
            WHERE id = %s
        """
        values = (
            year, company_name, location, work_details,
            stipend, duration, from_date, to_date,
            internship_type, internal_details, filename, id
        )

        cursor.execute(update_query, values)
        conn.commit()
        flash("Internship updated successfully!")
        return redirect(url_for('internships'))

    cursor.close()
    conn.close()
    return render_template('edit_internship.html', internship=internship)



@app.route('/delete_internship/<int:id>')
def delete_internship(id):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Vignesh@123",
        database="internship_db"
    )
    cursor = conn.cursor()
    cursor.execute("DELETE FROM internships WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('internships'))




# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect("http://127.0.0.1:5001/")




@app.route('/view_internships')
def view_internships():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    role = session['role']
    # prn = session.get('prn', None)  # Get PRN only if it exists in session
    prn = session.get('prn', '').strip()

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if role == 'faculty':
        cursor.execute("SELECT * FROM internships")
    else:
        cursor.execute("SELECT * FROM internships WHERE prn = %s", (prn,))

    internships = cursor.fetchall()

    # ✅ Clean whitespace from PRNs
    for i in internships:
        i['prn'] = i['prn'].strip()

    cursor.close()
    db.close()

    current_year = datetime.now().year

    return render_template(
        'internships.html',
        internships=internships,
        current_year=current_year,
        prn=prn, # ✅ Pass the prn to the template
        role=role
    )



# new 8/4/25 ko
@app.route('/download_internships')
def download_internships():
    if 'user_id' not in session or session['role'] != "faculty":
        return redirect(url_for('login'))

    search_query = request.args.get('search', '')
    year = request.args.get('year', '')
    internship_type = request.args.get('internship_type', '')
    academic_year = request.args.get('academic_year', '')

    query = "SELECT * FROM internships WHERE 1=1"
    filters = []

    if search_query:
        query += " AND (student_name LIKE %s OR company_name LIKE %s OR location LIKE %s)"
        filters += [f"%{search_query}%"] * 3
    if year:
        query += " AND year = %s"
        filters.append(year)
    if internship_type:
        query += " AND internship_type = %s"
        filters.append(internship_type)
    if academic_year:
        try:
            start, end = academic_year.split('-')
            query += " AND from_date >= %s AND to_date <= %s"
            filters.append(f"{start}-06-01")
            filters.append(f"{end}-05-31")
        except:
            flash("Invalid academic year format. Use YYYY-YYYY", "error")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute(query, tuple(filters))
    data = cursor.fetchall()
    cursor.close()
    db.close()

    df = pd.DataFrame(data)
    excel_path = "static/filtered_internships.xlsx"
    df.to_excel(excel_path, index=False)

    return send_file(excel_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
