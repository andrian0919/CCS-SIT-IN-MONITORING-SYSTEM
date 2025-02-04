from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from flask import session

app = Flask(__name__)
app.secret_key = "sysarch32"

# MSSQL Database Connection String
app.config["SQLALCHEMY_DATABASE_URI"] = "mssql+pyodbc://@LAPTOP-IEKCA1QT\\SQLEXPRESS01/SitInMonitoring?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)  # New field for student ID
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    firstname = db.Column(db.String(50), nullable=False)
    middlename = db.Column(db.String(50))
    course = db.Column(db.String(50), nullable=False)
    yearlevel = db.Column(db.String(20), nullable=False)


# Define the Sessions model
class SessionRecord(db.Model):
    __tablename__ = "Sessions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    remaining_sessions = db.Column(db.Integer, nullable=False, default=10)  # Default to 10 sessions

# Define the Reservations model
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)

    student = db.relationship("User", backref="reservations")


# Create tables if they don't exist
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    user = User.query.filter_by(username=username).first()
    if user and user.password == password:  # Direct comparison (consider hashing for security)
        session["user_id"] = user.id
        session["username"] = user.username 
        return redirect(url_for("success"))
    else:
        flash("Invalid username or password", "error")
        return redirect(url_for("home"))


@app.route("/register", methods=["POST"])
def register():
    try:
        new_user = User(
            student_id=request.form.get("id"),  # Save student ID here
            username=request.form.get("username"),
            password=request.form.get("password"),
            email=request.form.get("email"),
            lastname=request.form.get("lastname"),
            firstname=request.form.get("firstname"),
            middlename=request.form.get("middlename"),
            course=request.form.get("course"),
            yearlevel=request.form.get("yearlevel")
        )
        db.session.add(new_user)
        db.session.commit()

        session_record = SessionRecord(user_id=new_user.id, remaining_sessions=10)
        db.session.add(session_record)
        db.session.commit()

        session["user_id"] = new_user.id
        session["username"] = new_user.username

        flash("Registration successful! You are now logged in.", "success")
        return redirect(url_for("success"))

    except IntegrityError:
        db.session.rollback()
        flash("Username, email, or student ID already exists", "error")
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

@app.route("/make_reservation", methods=["GET", "POST"])
def make_reservation():
    if "user_id" not in session:
        flash("Please log in first!", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        date = request.form.get("date")
        time = request.form.get("time")

        # Verify user exists before making reservation
        user = User.query.get(session["user_id"])
        if not user:
            flash("User not found!", "error")
            return redirect(url_for("home"))

        new_reservation = Reservation(student_id=user.id, date=date, time=time)
        db.session.add(new_reservation)
        db.session.commit()

        flash("Reservation made successfully!", "success")
        return redirect(url_for("success"))

    return render_template("make_reservation.html")



@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
