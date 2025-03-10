from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from flask import session
from flask import jsonify
from flask_mail import Mail, Message
import random
import string
import pandas as pd
from sqlalchemy import func
import os
from reports import generate_purpose_report, generate_year_level_report
from database import db
from sqlalchemy import text
from flask_wtf.csrf import generate_csrf


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

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root@localhost/SitInMonitoring"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database with the app
db.init_app(app)

REPORTS_DIR = os.path.join("static", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

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
    date_registered = db.Column(db.DateTime, default=datetime.utcnow) 


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
    status = db.Column(db.String(50), default="Pending")
    time_out = db.Column(db.String(20))

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

class Announcement(db.Model):
    __tablename__ = "Announcements"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    announcement_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Feedback(db.Model):
    __tablename__ = "Feedback"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(50), nullable=False)
    feedback_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

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

    # Fetch active sessions with Purpose, Lab, and Status
    active_sessions = (
        db.session.query(
            User.student_id,
            User.firstname,
            User.lastname,
            Reservation.purpose,
            Reservation.lab,
            Reservation.status,
            SessionRecord.remaining_sessions
        )
        .join(SessionRecord, User.id == SessionRecord.user_id)
        .join(Reservation, User.student_id == Reservation.student_id)
        .filter(Reservation.status == "Approved")
        .all()
    )

        # Fetch all students
    all_students = (
        db.session.query(
            User.student_id,
            User.firstname,
            User.lastname,
            User.yearlevel,
            User.course,
            User.date_registered
        )
        .all()
    )

        # Fetch current sit-ins
    current_sit_ins = (
        db.session.query(
            Reservation.id,
            User.student_id,
            User.firstname,
            User.lastname,
            Reservation.purpose,
            Reservation.lab,
            Reservation.time
        )
        .join(User, User.student_id == Reservation.student_id)
        .filter(Reservation.status == "Sit-in")
        .all()
    )

        # Fetch sit-in records
    sit_in_records = (
        db.session.query(
            Reservation.id,
            User.student_id,
            User.firstname,
            User.lastname,
            Reservation.purpose,
            Reservation.lab,
            Reservation.time,
            Reservation.date
        )
        .join(User, User.student_id == Reservation.student_id)
        .filter(Reservation.status == "Ended")
        .all()
    )

     # Fetch pending reservations
    pending_reservations = (
        db.session.query(
            Reservation.id,
            User.student_id,
            User.firstname,
            User.lastname,
            Reservation.lab,
            Reservation.purpose,
            Reservation.date,
            Reservation.time
        )
        .join(User, User.student_id == Reservation.student_id)
        .filter(Reservation.status == "Pending")  # Only show pending reservations
        .all()
    )

    # Fetch report data
    report_data = (
        db.session.query(User.yearlevel, Reservation.purpose, func.count(Reservation.id).label("count"))
        .join(User, User.student_id == Reservation.student_id)
        .group_by(User.yearlevel, Reservation.purpose)
        .all()
    )

    # Fetch feedback data
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()

    return render_template(
        "admin_dashboard.html",
        all_students=all_students,
        current_sit_ins=current_sit_ins,
        sit_in_records=sit_in_records,
        active_sessions=active_sessions,
        report_data=report_data,
        feedbacks=feedbacks  # Pass feedback data to the template
    )

@app.route('/download_report/<report_type>')
def download_report(report_type):
    filename = f"report_{report_type}.xlsx"
    file_path = os.path.join(REPORTS_DIR, filename)

    if report_type == "purpose":
        data = (
            db.session.query(Reservation.purpose, func.count(Reservation.id).label("count"))
            .group_by(Reservation.purpose)
            .all()
        )
        df = pd.DataFrame(data, columns=["Purpose", "Count"])

    elif report_type == "year_level":
        data = (
            db.session.query(User.yearlevel, func.count(User.id).label("count"))
            .group_by(User.yearlevel)
            .all()
        )
        df = pd.DataFrame(data, columns=["Year Level", "Count"])

    else:
        return jsonify({"error": "Invalid report type"}), 400

    df.to_excel(file_path, index=False)
    return jsonify({"file_url": f"/reports/{filename}", "file_name": filename})

@app.route('/reports/<filename>')
def serve_report(filename):
    return send_from_directory(REPORTS_DIR, filename, as_attachment=True)

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
    
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found!", "error")
        return redirect(url_for("home"))

    session_record = SessionRecord.query.filter_by(user_id=session["user_id"]).first()
    remaining_sessions = session_record.remaining_sessions if session_record else 0

    # Define the uploads folder path
    uploads_folder = os.path.join("static", "uploads")

    # Get all available image files (.png and .jpg)
    available_images = [f for f in os.listdir(uploads_folder) if f.endswith((".png", ".jpg"))]

    # If images exist, randomly select one. Otherwise, use default.
    if available_images:
        profile_pic_filename = random.choice(available_images)
    else:
        profile_pic_filename = "default.png"

    profile_pic_url = url_for('static', filename=f'uploads/{profile_pic_filename}')

    return render_template("student_dashboard.html", user=user, remaining_sessions=remaining_sessions, profile_pic=profile_pic_url)

@app.route('/static/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('static/uploads', filename)


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
        user.lastname = request.form.get("lastname", user.lastname)
        user.firstname = request.form.get("firstname", user.firstname)
        user.course = request.form.get("course", user.course)
        user.yearlevel = request.form.get("yearlevel", user.yearlevel)

        db.session.commit()

        # 🔹 **Fix Remaining Sessions Disappearing**
        session_record = SessionRecord.query.filter_by(user_id=session["user_id"]).first()
        remaining_sessions = session_record.remaining_sessions if session_record else 0

        # 🔹 **Fix Profile Picture Disappearing**
        uploads_folder = os.path.join("static", "uploads")
        available_images = [f for f in os.listdir(uploads_folder) if f.endswith((".png", ".jpg"))]

        if available_images:
            profile_pic_filename = random.choice(available_images)  # Random profile pic per login
        else:
            profile_pic_filename = "default.png"

        profile_pic_url = url_for('static', filename=f'uploads/{profile_pic_filename}')

        flash("Record updated successfully!", "success")

        # 🔹 **Return updated dashboard without pressing Home**
        return render_template("student_dashboard.html", user=user, remaining_sessions=remaining_sessions, profile_pic=profile_pic_url)

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
    labs = Lab.query.all()

    if request.method == "POST":
        date = request.form.get("date")
        time = request.form.get("time")
        purpose = request.form.get("purpose")
        lab_id = request.form.get("lab")
        pc_input = request.form.get("available_pc")

        lab = Lab.query.get(lab_id)
        if not lab:
            flash("Invalid laboratory selection!", "error")
            return redirect(url_for("make_reservation"))

        if not pc_input:
            flash("Please enter a valid PC number.", "error")
            return redirect(url_for("make_reservation"))

        # Debugging: Print collected data
        print(f"Saving reservation: {user.student_id}, {user.lastname}, {user.firstname}, {date}, {time}, {purpose}, {lab.lab_name}, {pc_input}")

        # Save reservation
        new_reservation = Reservation(
            student_id=user.student_id,
            lastname=user.lastname,
            firstname=user.firstname,
            date=date,
            time=time,
            purpose=purpose,
            lab=lab.lab_name,
            available_pc=pc_input,
            status="Pending"  # Default status
        )
        
        db.session.add(new_reservation)
        db.session.commit()
        flash("Reservation made successfully!", "success")
        return redirect(url_for("success"))

    return render_template(
        "make_reservation.html",
        user=user,
        remaining_sessions=remaining_sessions,
        labs=labs
    )

@app.route("/admin_reservations")
def admin_reservations():
    reservations = Reservation.query.all()
    print("Fetched reservations:", reservations)  # Debugging
    return render_template("Reservation_Actions.html", reservations=reservations)


@app.route("/end_session/<student_id>", methods=["POST"])
def end_session(student_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({"success": False, "error": "Student not found"}), 404

    session_record = SessionRecord.query.filter_by(user_id=user.id).first()
    if not session_record or session_record.remaining_sessions <= 0:
        return jsonify({"success": False, "error": "No remaining sessions"}), 400

    # Deduct one session
    session_record.remaining_sessions -= 1

    # Free up the PC
    latest_reservation = Reservation.query.filter_by(student_id=student_id).order_by(Reservation.id.desc()).first()
    if latest_reservation:
        pc = PC.query.filter_by(pc_name=latest_reservation.available_pc).first()
        if pc:
            pc.is_available = True  # Make the PC available again

    db.session.commit()

    return jsonify({"success": True, "remaining_sessions": session_record.remaining_sessions})

@app.route("/admin/post_announcement", methods=["POST"])
def post_announcement():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    announcement_text = request.form.get("announcement_text")
    if not announcement_text:
        return jsonify({"success": False, "error": "Announcement text is required"}), 400

    new_announcement = Announcement(announcement_text=announcement_text)
    db.session.add(new_announcement)
    db.session.commit()

    return jsonify({"success": True, "message": "Announcement posted successfully"})

@app.route("/get_announcements")
def get_announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    announcements_data = [{"id": ann.id, "text": ann.announcement_text, "created_at": ann.created_at} for ann in announcements]
    return jsonify(announcements_data)

@app.route("/edit_announcement/<int:id>", methods=["POST"])
def edit_announcement(id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    announcement = Announcement.query.get(id)
    if not announcement:
        return jsonify({"success": False, "error": "Announcement not found"}), 404

    new_text = request.json.get("text")
    if not new_text:
        return jsonify({"success": False, "error": "Announcement text is required"}), 400

    announcement.announcement_text = new_text
    db.session.commit()

    return jsonify({"success": True, "message": "Announcement updated successfully"})

@app.route("/delete_announcement/<int:id>", methods=["DELETE"])
def delete_announcement(id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    announcement = Announcement.query.get(id)
    if not announcement:
        return jsonify({"success": False, "error": "Announcement not found"}), 404

    db.session.delete(announcement)
    db.session.commit()

    return jsonify({"success": True, "message": "Announcement deleted successfully"})

@app.route("/announcements")
def announcements():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Access denied!", "error")
        return redirect(url_for("home"))

    return render_template("announcements.html")

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.get_json()
    student_id = data.get("student_id")
    feedback_text = data.get("feedback_text")

    if not student_id or not feedback_text:
        return jsonify({"success": False, "error": "Missing data"}), 400

    new_feedback = Feedback(student_id=student_id, feedback_text=feedback_text)
    db.session.add(new_feedback)
    db.session.commit()

    return jsonify({"success": True, "message": "Feedback submitted successfully"})

@app.route("/feedback")
def feedback():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Access denied!", "error")
        return redirect(url_for("home"))

    # Fetch feedback data
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()

    return render_template("feedback.html", feedbacks=feedbacks)

@app.route("/reset_session/<student_id>", methods=["POST"])
def reset_session(student_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({"success": False, "error": "Student not found"}), 404

    session_record = SessionRecord.query.filter_by(user_id=user.id).first()
    if not session_record:
        return jsonify({"success": False, "error": "Session record not found"}), 404

    # Reset the remaining sessions to the default value
    if user.course in ["BSIT", "BSCS"]:
        session_record.remaining_sessions = 30  # Default for BSIT and BSCS
    else:
        session_record.remaining_sessions = 15  # Default for other courses

    db.session.commit()

    return jsonify({"success": True, "remaining_sessions": session_record.remaining_sessions})

@app.route("/sit_in/<student_id>", methods=["POST"])
def sit_in(student_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({"success": False, "error": "Student not found"}), 404

    session_record = SessionRecord.query.filter_by(user_id=user.id).first()
    if not session_record or session_record.remaining_sessions <= 0:
        return jsonify({"success": False, "error": "No remaining sessions"}), 400

    # Deduct one session
    session_record.remaining_sessions -= 1

    # Mark the student as "Sit-in" in their latest reservation
    latest_reservation = Reservation.query.filter_by(student_id=student_id).order_by(Reservation.id.desc()).first()
    if latest_reservation:
        latest_reservation.status = "Sit-in"
        db.session.commit()

    return jsonify({"success": True, "remaining_sessions": session_record.remaining_sessions})

@app.route("/update_status")
def update_status():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    reservations = Reservation.query.all()
    for reservation in reservations:
        reservation.status = "Active"  # Set default status
    db.session.commit()

    return jsonify({"success": True, "message": "Status updated successfully!"})

@app.route("/accept_reservation/<int:reservation_id>", methods=["POST"])
def accept_reservation(reservation_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return jsonify({"success": False, "error": "Reservation not found"}), 404

    # Update the reservation status to "Approved"
    reservation.status = "Approved"
    db.session.commit()

    return jsonify({"success": True})

@app.route("/decline_reservation/<int:reservation_id>", methods=["POST"])
def decline_reservation(reservation_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return jsonify({"success": False, "error": "Reservation not found"}), 404

    # Update the reservation status to "Declined"
    reservation.status = "Declined"
    db.session.commit()

    return jsonify({"success": True})

@app.route('/Reservation_Actions')
def reservation_actions():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Access denied!", "error")
        return redirect(url_for("home"))
    reservations = Reservation.query.all()
    
    return render_template("Reservation_Actions.html", reservations=reservations)

@app.after_request
def add_csrf_cookie(response):
    response.set_cookie("csrf_token", generate_csrf())
    return response

@app.route("/end_sit_in/<int:sit_in_id>", methods=["POST"])
def end_sit_in(sit_in_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    reservation = Reservation.query.get(sit_in_id)
    if not reservation:
        return jsonify({"success": False, "error": "Sit-in session not found"}), 404

    # Update the status to "Ended" and set the time-out
    reservation.status = "Ended"
    reservation.time_out = datetime.now().strftime("%H:%M")
    db.session.commit()

    return jsonify({"success": True})


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
