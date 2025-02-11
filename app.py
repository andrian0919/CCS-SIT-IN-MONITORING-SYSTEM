from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from flask import session
from flask import jsonify
from flask_mail import Mail, Message
import random
import string

app = Flask(__name__)
app.secret_key = "sysarch32"
app.permanent_session_lifetime = timedelta(days=7)

# Configure mail for forgot password functionality
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
mail = Mail(app)

# MSSQL Database Connection String
app.config["SQLALCHEMY_DATABASE_URI"] = "mssql+pyodbc://@LAPTOP-IEKCA1QT\\SQLEXPRESS01/SitInMonitoring?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    firstname = db.Column(db.String(50), nullable=False)
    middlename = db.Column(db.String(50))
    course = db.Column(db.String(50), nullable=True) 
    yearlevel = db.Column(db.String(20), nullable=True) 
    role = db.Column(db.String(20), nullable=False, default="student")



# Define the Sessions model
class SessionRecord(db.Model):
    __tablename__ = "Sessions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    remaining_sessions = db.Column(db.Integer, nullable=False, default=30)  # Default to 10 sessions

class Reservation(db.Model):
    __tablename__ = "Reservation"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(50), db.ForeignKey("Users.student_id"), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)  # Added column for lastname
    firstname = db.Column(db.String(50), nullable=False)  # Added column for firstname
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    purpose = db.Column(db.String(100), nullable=False)
    lab = db.Column(db.String(50), nullable=False)
    available_pc = db.Column(db.String(50), nullable=False)

    student = db.relationship("User", backref="reservations")


class Lab(db.Model):
    __tablename__ = "Labs"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lab_name = db.Column(db.String(50), nullable=False)

class PC(db.Model):
    __tablename__ = "PCs"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lab_id = db.Column(db.Integer, db.ForeignKey("Labs.id"), nullable=False)
    pc_name = db.Column(db.String(50), nullable=False)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
# Create tables if they don't exist
with app.app_context():
    db.create_all()

    fixed_accounts = [
        {"student_id": "admin", "password": "admin123", "email": "admin@example.com", "lastname": "Admin", "firstname": "User", "role": "admin"},
        {"student_id": "staff", "password": "staff123", "email": "staff@example.com", "lastname": "Staff", "firstname": "User", "role": "staff"},
    ]

    for account in fixed_accounts:
        existing_user = User.query.filter_by(student_id=account["student_id"]).first()
        if not existing_user:
            new_user = User(
                student_id=account["student_id"],
                password=account["password"],  # Hash this for security
                email=account["email"],
                lastname=account["lastname"],
                firstname=account["firstname"],
                role=account["role"],
            )
            db.session.add(new_user)

    db.session.commit()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        student_id = request.form.get("username")
        password = request.form.get("password")
        remember_me = 'remember_me' in request.form

        user = User.query.filter_by(student_id=student_id).first()
        if user and user.password == password:
            session["user_id"] = user.id
            session["role"] = user.role  # Store role in session
            
            if remember_me:
                session.permanent = True  # Session lasts longer if 'Remember Me' is checked

            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user.role == "staff":
                return redirect(url_for("staff_dashboard"))
            else:
                return redirect(url_for("student_dashboard"))
        else:
            flash("Invalid ID or password", "error")
            return redirect(url_for("home"))

    return render_template("index.html")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate random token for password reset
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            user.password_reset_token = token
            db.session.commit()

            # Send the token via email
            msg = Message("Password Reset Request", sender="your-email@gmail.com", recipients=[email])
            msg.body = f"Your password reset token is: {token}"
            mail.send(msg)

            flash("Password reset token sent to your email.", "success")
            return redirect(url_for("home"))
        else:
            flash("Email not found!", "error")
            return redirect(url_for("home"))

    return render_template("forgot_password.html")

@app.route("/admin_dashboard")
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Access denied!", "error")
        return redirect(url_for("home"))
    return render_template("admin_dashboard.html")

@app.route("/staff_dashboard")
def staff_dashboard():
    if "user_id" not in session or session.get("role") != "staff":
        flash("Access denied!", "error")
        return redirect(url_for("home"))
    return render_template("staff_dashboard.html")


@app.route("/register", methods=["POST"])
def register():
    try:
        student_id = request.form.get("id")
        password = request.form.get("password")
        repeat_password = request.form.get("repeat_password")

        if password != repeat_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for("home"))

        existing_user = User.query.filter_by(student_id=student_id).first()
        if existing_user:
            flash("Student ID already exists!", "error")
            return redirect(url_for("home"))

        new_user = User(
            student_id=student_id,
            password=password,  # You should hash this for security
            email=request.form.get("email"),
            lastname=request.form.get("lastname"),
            firstname=request.form.get("firstname"),
            middlename=request.form.get("middlename"),
            course=request.form.get("course"),
            yearlevel=request.form.get("yearlevel"),
        )

        db.session.add(new_user)
        db.session.commit()

        # Set remaining sessions based on the course
        if new_user.course in ["BSIT", "BSCS"]:
            remaining_sessions = 30
        else:
            remaining_sessions = 15

        session_record = SessionRecord(user_id=new_user.id, remaining_sessions=remaining_sessions)
        db.session.add(session_record)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("home"))  # Redirect to login page

    except IntegrityError as e:
        db.session.rollback()
        flash("Email or student ID already exists", "error")
        return redirect(url_for("home"))


@app.route("/success")
def success():
    if "user_id" not in session:
        flash("Please log in first!", "error")
        return redirect(url_for("home"))
    
    user = User.query.get(session["user_id"])
    
    return render_template("student_dashboard.html", user=user)

@app.route("/student_dashboard")
def student_dashboard():
    if "user_id" not in session:
        flash("Please log in first!", "error")
        return redirect(url_for("home"))
    
    user = User.query.get(session["user_id"])  # Fetch user details
    if not user:
        flash("User not found!", "error")
        return redirect(url_for("home"))

    # Fetch remaining sessions
    session_record = SessionRecord.query.filter_by(user_id=session["user_id"]).first()
    remaining_sessions = session_record.remaining_sessions if session_record else 0

    return render_template("student_dashboard.html", user=user, remaining_sessions=remaining_sessions)

@app.route("/history")
def history():
    if "user_id" not in session:
        flash("Please log in first!", "error")
        return redirect(url_for("home"))

    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found!", "error")
        return redirect(url_for("home"))

    # Fetch reservation history for the student
    reservations = Reservation.query.filter_by(student_id=user.student_id).all()

    # Get remaining sessions for each student in reservations
    student_ids = [res.student_id for res in reservations]
    session_records = SessionRecord.query.filter(SessionRecord.user_id.in_(
        db.session.query(User.id).filter(User.student_id.in_(student_ids))
    )).all()

    # Create a dictionary to map student_id to remaining sessions
    remaining_sessions = {user.student_id: session.remaining_sessions for session in session_records for user in User.query.filter_by(id=session.user_id)}

    return render_template("history.html", user=user, reservations=reservations, remaining_sessions=remaining_sessions)

@app.route("/edit_record", methods=["GET", "POST"])
def edit_record():
    if "user_id" not in session:
        flash("Please log in first!", "error")
        return redirect(url_for("home"))

    user = User.query.get(session["user_id"])

    if request.method == "POST":
        user.lastname = request.form.get("lastname")
        user.firstname = request.form.get("firstname")
        user.course = request.form.get("course")
        user.yearlevel = request.form.get("yearlevel")
        
        db.session.commit()
        flash("Record updated successfully!", "success")
        return redirect(url_for("success"))

    return render_template("edit_record.html", user=user)

@app.route("/view_sessions")
def view_sessions():
    if "user_id" not in session:
        return redirect(url_for("home"))

    session_record = SessionRecord.query.filter_by(user_id=session["user_id"]).first()
    remaining_sessions = session_record.remaining_sessions if session_record else 0

    return f"You have {remaining_sessions} remaining sessions."

@app.route("/get_available_pcs")
def get_available_pcs():
    lab_id = request.args.get("lab_id")

    if not lab_id:
        return jsonify([])

    try:
        lab_id = int(lab_id)  # Convert to integer
    except ValueError:
        return jsonify([])  # Return empty if invalid ID

    available_pcs = PC.query.filter_by(lab_id=lab_id, is_available=True).all()
    pcs_data = [{"id": pc.id, "pc_name": pc.pc_name} for pc in available_pcs]
    return jsonify(pcs_data)

@app.route("/make_reservation", methods=["GET", "POST"])
def make_reservation():
    if "user_id" not in session:
        flash("Please log in first!", "error")
        return redirect(url_for("home"))

    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found!", "error")
        return redirect(url_for("home"))

    session_record = SessionRecord.query.filter_by(user_id=session["user_id"]).first()
    remaining_sessions = session_record.remaining_sessions if session_record else 0

    labs = Lab.query.all()  # Fetch all labs for dropdown

    if request.method == "POST":
        date = request.form.get("date")
        time = request.form.get("time")
        purpose = request.form.get("purpose")
        lab_id = request.form.get("lab")
        pc_id = request.form.get("available_pc")

        lab = Lab.query.get(lab_id)
        pc = PC.query.get(pc_id)

        if not lab or not pc or not pc.is_available:
            flash("Invalid lab or PC selection!", "error")
            return redirect(url_for("make_reservation"))

        new_reservation = Reservation(
            student_id=user.student_id,
            lastname=user.lastname,  # Store lastname
            firstname=user.firstname,  # Store firstname
            date=date,
            time=time,
            purpose=purpose,
            lab=lab.lab_name,
            available_pc=pc.pc_name
        )
        db.session.add(new_reservation)

        # Mark the PC as unavailable
        pc.is_available = False
        db.session.commit()

        flash("Reservation made successfully!", "success")
        return redirect(url_for("success"))

    return render_template(
        "make_reservation.html",
        user=user,
        remaining_sessions=remaining_sessions,
        labs=labs
    )


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
