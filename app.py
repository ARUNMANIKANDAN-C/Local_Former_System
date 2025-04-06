from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from databasetest import FarmManagementDB
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
#csrf = CSRFProtect(app)
db = FarmManagementDB()

# Mock user data for login (replace with db calls in production)
users = {
    "9876543210": "password123",
    "9123456789": "pass456"
}

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
        phone = request.form.get('phone')
        password = request.form.get('passkey')

        if phone in users and users[phone] == password:
            session['user'] = phone
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid phone number or password.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/sign_in', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get('phone')
        password = request.form.get('passkey')
        db.add_users(username, password)
        flash('Sign up successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('sign_in.html')

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
@login_required
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

# Dummy product list for demo
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
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template(
        'dashboard.html',
        user={"name": "Ravi Kumar"},
        total_products=12,
        total_orders=34,
        monthly_sales=5400,
        top_buyer="Ramesh Traders",
        recent_orders=[
            {"id": "ORD001", "product": "Tomatoes", "buyer": "Ramesh", "status": "Shipped", "date": "2025-04-04"},
            {"id": "ORD002", "product": "Wheat", "buyer": "Sita", "status": "Pending", "date": "2025-04-03"},
        ],
        chart_labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        chart_data=[800, 900, 1200, 1100, 1300, 1400, 1000]
    )

# ------------------------
# URL Inspector (Debug)
# ------------------------
@app.route('/urls')
@login_required
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
    app.run(debug=True)
