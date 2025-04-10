from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from datetime import datetime, timedelta
from database import FarmManagementDB
import random
import os
from functools import wraps
from otp_sender import GmailSender
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'fallback-hardcoded-key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(weeks=1)

db = FarmManagementDB()
sender = GmailSender()

# ------------------------
# golobal variables
# ------------------------
@app.context_processor
def inject_user_image():
    user = session.get('user')
    if user and user.get("email"):
        safe_email = user.get("email").replace('@', '_at_').replace('.', '_dot_')  # Optional sanitization
        filename = f"{safe_email}.jpg"
        image_exists = True
        image_filename = "uploads/"+filename
    else:
        image_exists = False
        image_filename = 'images/logo.png'
    return dict(image_exists=image_exists, image_filename=image_filename)

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
# Helper
# ------------------------
def get_current_user():
    return session.get('user')

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
        flash('Already logged in!', 'info')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('passkey')
            user = db.get_user_by_email(email)

            if user:
                (EmailID, Name, PhoneNumber, Password, Address, CreatedAt, UserType) = user
                if password == Password:
                    session.permanent = True
                    session['user'] = {
                        "email": EmailID,
                        "name": Name,
                        "usertype": UserType
                    }
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Incorrect password.', 'danger')
            else:
                flash('User not found.', 'danger')
        except Exception as e:
            flash(f'Login error: {e}', 'danger')

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
        photo = request.files.get('photo')

        if photo:
            # Make sure the uploads folder exists
            upload_folder = 'static/uploads'
            os.makedirs(upload_folder, exist_ok=True)

            # Use email as filename (replace special characters to make it safe)
            safe_email = email.replace('@', '_at_').replace('.', '_dot_')  # Optional sanitization
            filename = f"{safe_email}.jpg"

            # Full save path
            save_path = os.path.join(upload_folder, filename)

            # Convert to JPG and save
            image = Image.open(photo)
            rgb_image = image.convert('RGB')
            rgb_image.save(save_path, 'JPEG')
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

@app.route('/Former_Signup', methods=['GET', 'POST'])
def Former_Signup():
    if user := session.get('user'):
        if user.get('usertype') != 'farmer':
            flash('Your are not farmer, !Please sigin with different id for purchasing Goods', 'danger')
            return redirect(url_for('dashboard'))
        else:
            if db.check_farmer_exists(user["email"]):
                flash('You are already registered as a farmer!', 'info')
                return redirect(url_for('dashboard'))
            
    if request.method == 'POST':
        aadhar = request.form['aadhar_number']
        db.insert_farmer(user['email'],aadhar)
        return redirect(url_for('success'))  # Show success page after saving
    return render_template('former_signup.html')

@app.route('/submit_delivery', methods=['POST'])
def submit_delivery():
    license = request.form['license']
    plate_number = request.form['plate_number']
    vehicle_type = request.form['vehicle_type']
    address = request.form['address']
    user_email = session.get('email')  # assuming user is logged in
    
    db.insert_delivery_person(user_email, license, vehicle_type,  plate_number,address)
    flash('Delivery person details submitted successfully!', 'success')
    return redirect(url_for('success'))

@app.route('/Profile', methods=['GET', 'POST'])
def view_update_profile():
    return render_template('profile.html')

# ------------------------
# Main Routes
# ------------------------
@app.route('/')
def index():
    return redirect(url_for("welcome"))

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/wlecome')
def welcome():
    return render_template("welcome.html")
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
    {"id": 1, "name": "Product 1", "price": 100, "image": "1.jpg", "district": "A"},
    {"id": 2, "name": "Product 2", "price": 200, "image": "2.jpg", "district": "B"},
    {"id": 3, "name": "Product 3", "price": 300, "image": "3.jpg", "district": "A"},
    {"id": 4, "name": "Product 4", "price": 400, "image": "4.jpg", "district": "C"},
    {"id": 5, "name": "Product 5", "price": 500, "image": "5.jpg", "district": "B"},
    {"id": 6, "name": "Product 6", "price": 600, "image": "6.jpg", "district": "A"},
]

@app.route('/profile')
def profile():
    user = get_current_user()
    if user:
        return render_template('profile.html', user=user)
    else:
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))

@app.route('/available_products', methods=['GET', 'POST'])
def search_products():

        if request.method == 'POST':
            search_term = request.form.get('search', '').lower()
            product_filter = request.form.get('product', '').lower()
            try:
                price = float(request.form.get('price', 0)) if request.form.get('price') else None
            except ValueError:
                price = None
                flash('Invalid price value', 'danger')

            filtered_crops = [
                crop for crop in filtered_crops
                if (not search_term or search_term in crop['name'].lower()) and
                (not product_filter or product_filter in crop['name'].lower()) and
                (not price or crop['price'] <= price)
            ]

        return render_template('available_products.html', products=filtered_crops)
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
    user = get_current_user()
    return render_template("dashboard.html",
        user=user,
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

@app.route('/choose-delivery', methods=['POST'])
def choose_delivery():
    task_id = request.form.get('task_id')
    flash(f"Delivery {task_id} has been assigned to you.", "success")
    return redirect(url_for('delivery_dashboard'))

@app.route('/delivery-dashboard')
def delivery_dashboard():
    delivery_man = {"name": "Arjun"}
    return render_template("delivery_dashboard.html",
        delivery_man=delivery_man,
        total_deliveries=132,
        pending_deliveries=7,
        today_deliveries=12,
        avg_delivery_time=28,
        status_data=[113, 15, 4],
        weekly_labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        weekly_data=[20, 18, 22, 25, 19, 15, 13],
        recent_deliveries=[
            {"id": "D1234", "customer": "Neha Sharma", "status": "Delivered", "time_taken": 30, "date": "2025-04-07"},
            {"id": "D1235", "customer": "Rahul Verma", "status": "Delivered", "time_taken": 25, "date": "2025-04-07"},
            {"id": "D1236", "customer": "Aarti Singh", "status": "Pending", "time_taken": "-", "date": "2025-04-08"},
        ],
        nearby_deliveries=[
            {"id": "N1001", "pickup": "Sector 22", "drop": "Sector 27", "distance": "2.4 km"},
            {"id": "N1002", "pickup": "MG Road", "drop": "Cyber Park", "distance": "1.1 km"},
        ]
    )

@app.route("/dashboard1")
@login_required
def dashboard1():
    user = get_current_user()

    try:
        # Use actual DB methods to fetch counts
        total_users = db.count_all_users()  # Implement this in FarmManagementDB
        total_farmers = db.count_users_by_type("farmer")
        total_customers = db.count_users_by_type("customer")
        total_delivery_persons = db.count_users_by_type("delivery")
        total_products = db.count_all_crops()  # total crops in market
        total_orders = db.count_all_orders()
        total_feedback = db.count_all_feedbacks()

        return render_template("dashboard.html",
            user=user,
            total_users=total_users,
            total_farmers=total_farmers,
            total_customers=total_customers,
            total_delivery_persons=total_delivery_persons,
            total_products=total_products,
            total_orders=total_orders,
            total_feedback=total_feedback
        )
    except Exception as e:
        flash(f"Error loading dashboard: {e}", "danger")
        return redirect(url_for("home"))

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

@app.route("/test")
def test():
    return render_template("test.html")

# ------------------------
# Run App
# ------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
