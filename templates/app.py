from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import FarmManagementDB
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure secret key

db = FarmManagementDB()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.get_customer_by_email(email)
        if user and check_password_hash(user[6], password):  # Secure password check
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))

        flash("Invalid email or password!", "danger")
    
    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        address = request.form.get('address')
        google_location_id = request.form.get('google_location_id')
        password = request.form.get('password')

        # Check if user already exists
        if db.get_customer_by_email(email):
            flash("Email already registered!", "warning")
            return redirect(url_for('signup'))

        # Hash the password before saving
        hashed_password = generate_password_hash(password)

        if db.insert_customer(name, phone_number, email, address, google_location_id, hashed_password):
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for('login'))

        flash("Error creating account. Please try again.", "danger")

    return render_template("sign_in.html")

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    return render_template("dashboard.html", user_name=session['user_name'])

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
