from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "sysarch32"

# MSSQL Database Connection String (Update with your credentials)
app.config["SQLALCHEMY_DATABASE_URI"] = "mssql+pyodbc://@LAPTOP-IEKCA1QT\SQLEXPRESS01/SitInMonitoring?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Store hashed passwords
    email = db.Column(db.String(100), unique=True, nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    firstname = db.Column(db.String(50), nullable=False)
    middlename = db.Column(db.String(50))
    course = db.Column(db.String(50), nullable=False)
    yearlevel = db.Column(db.String(20), nullable=False)

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
    if user and check_password_hash(user.password, password):
        return redirect(url_for("success"))
    else:
        flash("Invalid username or password", "error")
        return redirect(url_for("home"))

@app.route("/register", methods=["POST"])
def register():
    try:
        new_user = User(
            username=request.form.get("username"),
            password = request.form.get("password"),
            email=request.form.get("email"),
            lastname=request.form.get("lastname"),
            firstname=request.form.get("firstname"),
            middlename=request.form.get("middlename"),
            course=request.form.get("course"),
            yearlevel=request.form.get("yearlevel")
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Username or email already exists", "error")
    
    return redirect(url_for("home"))

@app.route("/success")
def success():
    return "Login Successful!"

if __name__ == "__main__":
    app.run(debug=True)
