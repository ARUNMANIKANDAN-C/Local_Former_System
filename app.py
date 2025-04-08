from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from datetime import datetime, timedelta
from database import FarmManagementDB
import random
import smtplib
import os
from functools import wraps
from otp_sender import GmailSender

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'fallback-hardcoded-key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(weeks=1)

db = FarmManagementDB()
sender = GmailSender()

# ------------------------
# Login Required Decorator
# ------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------------
# Error Handlers
# ------------------------
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# ------------------------
# Authentication
# ------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            phone = request.form.get('phone')
            password = request.form.get('passkey')
            (
                EmailID,
                Name,
                PhoneNumber,
                Password,
                Address,
                CreatedAt,
                UserType
            ) = db.get_user_by_email(phone)

            if phone == PhoneNumber and password == Password:
                session['user'] = phone
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect phone or password.', 'danger')
        except Exception as e:
            flash(f'Invalid phone or password. Error: {e}', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('passkey')
        address = request.form.get('address')
        usertype = request.form.get('usertype')

        otp = str(random.randint(1000, 9999))
        session['pending_user'] = {
            'name': name,
            'email': email,
            'phone': phone,
            'password': password,
            'address': address,
            'usertype': usertype,
            'otp': otp
        }

        try:
            sender.send_email(
                to_email=email,
                subject="OTP for Signup",
                body=f"Your OTP for signup is: {otp}"
            )
            flash("OTP sent to your email. Please verify to complete signup.", "info")
            return redirect(url_for('verify_otp'))
        except Exception as e:
            flash(f"Failed to send OTP: {e}", 'danger')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_input_otp = request.form.get('otp')
        real_otp = session.get('pending_user', {}).get('otp')

        if user_input_otp == real_otp:
            try:
                user = session['pending_user']
                db.insert_user(
                    user['name'],
                    user['email'],
                    user['phone'],
                    user['password'],
                    user['address'],
                    user['usertype'],
                )
                flash('Signup successful! Please log in.', 'success')
                session.pop('pending_user')
                return redirect(url_for('login'))
            except Exception as e:
                flash(f"Signup failed: {e}", 'danger')
                return redirect(url_for('signup'))
        else:
            flash('Incorrect OTP. Please try again.', 'danger')

    return render_template('verify_otp.html')

@app.route('/terms_and_conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')

# ------------------------
# Main Routes
# ------------------------
@app.route('/')
def index():
    return redirect(url_for("home"))

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/details', methods=['GET', 'POST'])
def details():
    if request.method == 'POST':
        try:
            form_data = {
                'name': request.form.get('full-name'),
                'username': request.form.get('username'),
                'email': request.form.get('email'),
                'dob': request.form.get('dob'),
                'phone': request.form.get('address'),
                'message': request.form.get('message')
            }

            if not all(form_data.values()):
                flash('All fields are required!', 'danger')
                return redirect(url_for('details'))

            db.add_details(**form_data)
            flash('Details submitted successfully!', 'success')
        except Exception as e:
            app.logger.error(f"Error in details submission: {str(e)}")
            flash('An error occurred while submitting details.', 'danger')

    return render_template('details.html')

# ------------------------
# Products
# ------------------------
products = [
    {"name": "Tomatoes", "price": 50, "district": "Salem"},
    {"name": "Wheat", "price": 30, "district": "Madurai"},
    {"name": "Mangoes", "price": 80, "district": "Trichy"}
]

@app.route('/available_products', methods=['GET', 'POST'])
def search_products():
    filtered_products = products
    if request.method == 'POST':
        filters = {
            'search': request.form.get('search', '').lower(),
            'product': request.form.get('product', '').lower(),
            'district': request.form.get('district', '').lower(),
            'price': request.form.get('price', '')
        }

        try:
            price = int(filters['price']) if filters['price'] else None
            filtered_products = [
                p for p in products
                if (not filters['search'] or filters['search'] in p["name"].lower())
                and (not filters['product'] or filters['product'] in p["name"].lower())
                and (not filters['district'] or filters['district'] in p["district"].lower())
                and (not price or p["price"] <= price)
            ]
        except ValueError:
            flash('Invalid price value!', 'danger')

    return render_template('available_products.html', products=filtered_products)

# ------------------------
# Product Reviews
# ------------------------
main_product = {
    "name": "Organic Tomatoes",
    "reviews": []
}

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form.get("name")
        comment = request.form.get("comment")

        if name and comment:
            main_product["reviews"].append({
                "name": name,
                "comment": comment,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash("Review submitted successfully!", "success")
        else:
            flash("All fields are required!", "danger")

        return redirect(url_for("home"))

    return render_template("add_product.html", product=main_product)

# ------------------------
# Dashboard
# ------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html",
        user={"name": "Alex"},
        total_products=125,
        total_orders=342,
        monthly_sales=450000,
        top_buyer="John Doe",
        recent_orders=[
            {"id": "ORD001", "product": "Shoes", "buyer": "Alice", "status": "Shipped", "date": "2025-04-06"},
            {"id": "ORD002", "product": "Watch", "buyer": "Bob", "status": "Pending", "date": "2025-04-07"},
        ],
        chart_labels=["Jan", "Feb", "Mar", "Apr"],
        chart_data=[120000, 150000, 130000, 50000],
        product_names=["Shoes", "Watch", "Shirts"],
        product_sales=[150, 100, 200],
        customer_type_data=[70, 30]
    )

# ------------------------
# URL Inspector (Debug)
# ------------------------
@app.route('/urls')
def all_urls():
    endpoints = []
    for rule in app.url_map.iter_rules():
        endpoints.append({
            'endpoint': rule.endpoint,
            'methods': ','.join(rule.methods),
            'url': str(rule)
        })
    return render_template('urls.html', endpoints=endpoints)

# ------------------------
# Test Template (optional)
# ------------------------
@app.route("/test")
def test():
    return render_template("test.html")

# ------------------------
# Run App
# ------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
