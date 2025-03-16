from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure upload folder exists
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Function to get MySQL connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Vignesh@123",  # Ensure this is your actual MySQL password
        database="internship_db"
    )

# Home Route
@app.route('/')
def home():
    return render_template("index.html")

# Registration Route for Students
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return render_template("register.html")

        conn = get_db_connection()
        cursor = conn.cursor()
        # Check if the username already exists
        cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            flash("Username already exists!", "danger")
            conn.close()
            return render_template("register.html")

        # Insert new student user with role 'student'
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, 'student')", (username, password))
        conn.commit()
        conn.close()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["username"] = username
            session["role"] = user[0]
            if user[0] == "faculty":
                return redirect(url_for("view_internships"))
            else:
                return redirect(url_for("upload_internship"))
        else:
            flash("Invalid credentials!", "danger")

    return render_template("login.html")

# Upload Internship (Student)
@app.route("/upload", methods=["GET", "POST"])
def upload_internship():
    if "username" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    if request.method == "POST":
        student_name = session["username"]
        year = request.form["year"]
        company_name = request.form["company_name"]
        location = request.form["location"]
        work_details = request.form["work_details"]
        stipend = request.form["stipend"]
        duration = request.form["duration"]
        from_date = request.form["from_date"]
        to_date = request.form["to_date"]
        internship_type = request.form["internship_type"]
        internal_details = request.form.get("internal_details")

        file = request.files["certificate"]
        certificate_path = None
        if file and file.filename:
            filename = f"{int(time.time())}_{secure_filename(file.filename)}"  # Unique filename
            certificate_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(certificate_path)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO internships 
            (student_name, year, company_name, location, work_details, stipend, duration, from_date, to_date, internship_type, internal_details, certificate_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (student_name, year, company_name, location, work_details, stipend, duration, from_date, to_date, internship_type, internal_details, filename))
        
        conn.commit()
        conn.close()
        
        flash("Internship uploaded successfully!", "success")
        return redirect(url_for("upload_internship"))

    return render_template("upload.html")

# View Internships (Faculty) – now at route "/internships"
@app.route("/internships", methods=["GET", "POST"])
def view_internships():
    if "username" not in session or session["role"] != "faculty":
        return redirect(url_for("login"))

    search_query = request.args.get('search', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if search_query:
        cursor.execute("""
            SELECT * FROM internships 
            WHERE student_name LIKE %s OR company_name LIKE %s OR location LIKE %s
        """, ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
    else:
        cursor.execute("SELECT * FROM internships")
    internships = cursor.fetchall()
    conn.close()

    return render_template("internships.html", internships=internships, search_query=search_query)

# Logout Route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
