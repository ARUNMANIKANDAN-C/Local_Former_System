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
import re

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
        userexist=True
    else:
        image_exists = False
        image_filename = 'images/logo.png'
        userexist=False
    return dict(image_exists=image_exists, image_filename=image_filename,userexist=userexist)

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
            print(email+"/")
            password = request.form.get('passkey')
            user = db.get_user_by_email(email)
            print(user)
            if user:
                (EmailID, Name, PhoneNumber, Password, Address, CreatedAt, UserType) = user
                if password == Password:
                    flash('Login successful!', 'success')
                    if UserType=="Farmer":
                        session.permanent = True
                        session['user'] = {
                        "email": EmailID,
                        "name": Name,
                        "usertype": UserType,
                        "status": "active"
                            }
                        return redirect(url_for('Farmer_Signup'))
                    elif UserType=="DeliveryPerson":
                        session['user'] = {
                        "email": EmailID,
                        "name": Name,
                        "usertype": UserType,
                        "status": "active"
                            }
                        return redirect(url_for('Delivery_Person'))
                    elif UserType=="Customer":
                        session['user'] = {
                        "email": EmailID,
                        "name": Name,
                        "usertype": UserType,
                        "status": "active"
                            }
                        return redirect(url_for('login'))
                    else:
                        flash('Invalid user type.', 'danger')
                        return redirect(url_for('signup'))
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
                print(user)
                type=user['usertype']
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

@app.route('/Farmer_Signup', methods=['GET', 'POST'])
def Farmer_Signup():
    user = session.get('user')
    if user:
        if user.get('usertype') != 'Farmer':
            flash('Your are not farmer, !Please sigin with different id for purchasing Goods', 'danger')
            return redirect(url_for('dashboard'))
        else:
            print(db.check_farmer_exists(user["email"],de=True))
            if db.check_farmer_exists(user["email"]):
                flash('You are already registered as a farmer!', 'info')
                return redirect(url_for('dashboard'))
       
    if request.method == 'POST':
        aadhar = request.form['aadhar_number']
        db.insert_farmer(user['email'],aadhar)
        return redirect(url_for('dashboard'))
    return render_template('farmer_signup.html')

@app.route('/Delivery_Person', methods=['GET', 'POST'])
def Delivery_Person():
    user = session.get('user')
    
    # Check if user is logged in
    if user:
        # Check if the logged-in user is not a delivery person
        if user.get('usertype') != 'DeliveryPerson':
            flash('You are not a delivery person! Please sign in with a different ID to purchase goods.', 'danger')
            return redirect(url_for('dashboard'))

        # Check if the delivery person is already registered
        if db.check_delivery_person_exists(user.get("email")):
            flash('You are already registered as a delivery person!', 'info')
            return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Get form data
        license = request.form.get('license')
        plate_number = request.form.get('plate_number')
        vehicle_type = request.form.get('vehicle_type')
        available_status = request.form.get('available_status')
        user_email = user.get('email') if user else None
        if not user_email:
            flash('User not logged in or session expired. Please log in again.', 'warning')
            return redirect(url_for('login'))  
        
        db.insert_delivery_person(user_email, license, vehicle_type, plate_number, available_status)
        flash('Delivery person details submitted successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('Delivery_Person_Siginup.html')


@app.route('/Profile', methods=['GET', 'POST'])
@login_required
def view_update_profile():
        user = session.get('user')
        user_type=user['usertype']
        email=user['email']
        if request.method == 'POST' and user_type=="Customer": 
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')

            db.update_3user(user['email'], name, phone, address)
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('view_update_profile'))
        
        elif request.method == 'POST' and user_type=="Farmer":
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            aadhar = request.form.get('aadhar')

            db.update_farmer(user['email'], name, phone, address, aadhar)
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('view_update_profile'))
        
        elif request.method == 'POST' and user_type=="DeliveryPerson":
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            license = request.form.get('license')
            vehicle_type = request.form.get('vehicle_type')
            plate_number = request.form.get('plate_number')
            status=request.form.get('available_status')

            db.update_delivery_person(user['email'], name, phone, address, license, vehicle_type, plate_number,status)
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('view_update_profile'))


        if user_type=="Customer":
            user1 = db.get_user_by_email(user['email'])
            (EmailID, Name, PhoneNumber, Password, Address, CreatedAt, UserType) = user1
            print(user["usertype"])
            return render_template('profile.html', user=user,user_type=user_type,phone=PhoneNumber, email=email, address=Address,name=Name)
        
        elif user_type=="Farmer":
            user1 = db.get_farmer_by_email(user['email'])
            (EmailID, Name, PhoneNumber, Password, Address, CreatedAt, UserType,Aadhar) = user1
            print(user["usertype"])
            return render_template('profile.html', user=user,user_type=user_type,phone=PhoneNumber, email=email, address=Address, name=Name,aadhar=Aadhar)
        elif user_type=="DeliveryPerson":
            user1 = db.get_deliver_person_by_email(user['email'])
            print(user1)
            (EmailID, Name, PhoneNumber, Password, Address, CreatedAt, UserType,license,vehicle_type,vehicle_number,status) = user1
            print(user["usertype"])
            return render_template('profile.html', user=user,user_type=user_type,phone=PhoneNumber, email=email, address=Address, name=Name,license_number=license,vehicle_type=vehicle_type,vehicle_number=vehicle_number,available_status=status) 

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
    {"id": 1, "name": "Product 1", "price": 100, "image": "images/1.jpg", "district": "A"},
    {"id": 2, "name": "Product 2", "price": 200, "image": "images/2.jpg", "district": "B"},
    {"id": 3, "name": "Product 3", "price": 300, "image": "images/3.jpg", "district": "A"},
    {"id": 4, "name": "Product 4", "price": 400, "image": "images/4.jpg", "district": "C"},
    {"id": 5, "name": "Product 5", "price": 500, "image": "images/5.jpg", "district": "B"},
    {"id": 6, "name": "Product 6", "price": 600, "image": "images/6.jpg", "district": "A"},
]


@app.route('/available_products', methods=['GET', 'POST'], endpoint='available_products')
def available_products():
    user = session.get('user')
    if not user:
        flash("User not logged in", "danger")
        return render_template('available_products.html', products=[])

    product_list = db.get_all_crops()
    print("product:", product_list)

    columns = [
        "id", "name", "price", "quantity", "unit", "CreatedAt", "FarmerName", "district", "image", "url"
    ]

    safe_email = user['email'].replace('@', '_at_').replace('.', '_dot_')
    filtered_crops = []

    for row in product_list:
        crop_name = row[1]
        farmer_name = row[6]
        crop_id = str(row[0])
        safe_crop_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', crop_name)
        image_path = f"uploads/{safe_email}/{safe_crop_name}/img.jpg"
        url = url_for('product_detail', FarmerName=farmer_name, product_id=crop_id)

        row_with_image = list(row) + [image_path, url]
        crop_dict = dict(zip(columns, row_with_image))

        filtered_crops.append(crop_dict)

    return render_template('available_products.html', products=filtered_crops)


@app.route('/product_detail/<FarmerName>/<product_id>')
def product_detail(FarmerName, product_id):
    user = session.get('user')
    if not user:
        return "User not logged in", 401

    safe_email = user['email'].replace('@', '_at_').replace('.', '_dot_')
    product_list = db.get_all_crops()
    print("product:", product_list)

    columns = [
        "id", "name", "price", "quantity", "unit", "CreatedAt", "FarmerName", "district", "image", "url", "description"
    ]

    for row in product_list:
        if str(row[0]) == str(product_id) and row[6] == FarmerName:
            crop_name = row[1]
            FarmerName = row[6]
            crop_id = str(row[0])
            crop_name = row[1]
            farmer_name = row[6]
            crop_id = str(row[0])
            safe_crop_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', crop_name)
            image_path = f"uploads/{safe_email}/{safe_crop_name}/img.jpg"
            url = url_for('product_detail', FarmerName=FarmerName, product_id=crop_id)
            
            description_path = f"static/uploads/{safe_email}/{safe_crop_name}/description.txt"

            try:
                with open(description_path, "r") as f:
                    description = f.read()
            except FileNotFoundError:
                description = "No description available."

            row_with_details = list(row) + [image_path, url, description]
            product = dict(zip(columns, row_with_details))
            print(product)
            return render_template('product_detail.html', product=product)

    return "Product not found", 404


@app.route('/process_payment', methods=['GET','POST'])
def process_payment():
    if  request.method == 'GET':
        return render_template('payment.html')
    if  request.method == 'POST':
        card_name = request.form['cardName']
        card_number = request.form['cardNumber']
        expiry = request.form['expiry']
        cvv = request.form['cvv']

        flash('Payment processed successfully!', 'success')
        return redirect(url_for('process_payment'))
    
product_categories = [
    "Leafy Greens",       # e.g., spinach, lettuce
    "Root Vegetables",    # e.g., carrot, beetroot
    "Cruciferous",        # e.g., broccoli, cauliflower
    "Alliums",            # e.g., onion, garlic
    "Marrow",             # e.g., zucchini, cucumber
    "Pods & Seeds",       # e.g., peas, beans
    "Tubers",             # e.g., potato, yam
    "Fungi",              # e.g., mushrooms
    "Nightshades",        # e.g., tomato, eggplant
    "Stems & Shoots"      # e.g., asparagus, celery
]


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    global product_categories
    user = session.get('user')
    if user["usertype"] != "Farmer":
        flash('You are not authorized to add products.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('image')
        category = request.form.get('product_category')
        product_name = request.form.get('product_name')
        description = request.form.get('description')
        pricePerQuantity = request.form.get('pricePerQuantity')
        quantity = request.form.get('quantity')
        unit = request.form.get('unit')
        name=category+"_"+product_name
        k=db.insert_crop(name,pricePerQuantity,user["email"], quantity,unit)
        user= session.get('user')
        # Create upload path

        safe_email = user['email'].replace('@', '_at_').replace('.', '_dot_')  # Optional sanitization
        safe_crop_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
        upload_base = os.path.join("static", "uploads", safe_email, safe_crop_name)
        os.makedirs(upload_base, exist_ok=True)
        

        description_path = f"static/uploads/{safe_email}/{safe_crop_name}/description.txt"
        with open(description_path, "w") as f:
            f.write(description)
        if file:
            filename = "img.jpg"
            filepath = os.path.join(upload_base, filename)
            image = Image.open(file)
            rgb_image = image.convert('RGB')
            rgb_image.save(filepath, 'JPEG')
            flash("Image uploaded success fully")

        flash("uploaded success fully")
        # Add new category if it's not in the list
        if category and category not in product_categories:
            product_categories.append(category)

        return redirect(url_for('add_product'))

    return render_template('add_product.html', categories=product_categories)


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
    return render_template('add_product.html', categories=product_categories)

# ------------------------
# Run App
# ------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
