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
        address = request.form.get('address')

        # Retrieve email from session
        user_email = user.get('email') if user else None
        if not user_email:
            flash('User not logged in or session expired. Please log in again.', 'warning')
            return redirect(url_for('login'))  # assuming you have a login route

        # Insert delivery person details into the DB
        db.insert_delivery_person(user_email, license, vehicle_type, plate_number, address)
        flash('Delivery person details submitted successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('Delivery_Person_Siginup.html')


@app.route('/Profile', methods=['GET', 'POST'])
def view_update_profile():
        user = session.get('user')
        print(user["usertype"])
        return render_template('profile.html', user=user,user_type=user['usertype'])
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
        filtered_crops = []
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
        user = session.get('user')
        product=db.get_all_crops()
        print("product:", product)

        columns = [
            "id",
            "name",
            "price",
            "quantity",
            "unit",
            "CreatedAt",
            "FarmerName",
            "district",
            "image",
            "url"
        ]
        safe_email = user['email'].replace('@', '_at_').replace('.', '_dot_')  # Optional sanitization
        for row in product:
            FarmerName= row[6]  
            name = row[1]       
            id = str(row[0])       
            image_path =  "uploads/"+safe_email+"/"+name+"/img.jpg"
            url ="product_detail/"+FarmerName+"/"+id
            row_with_image = list(row) + [image_path] +[url]
            filtered_crops.append(dict(zip(columns, row_with_image)))

        print(filtered_crops)
        return render_template('available_products.html', products=filtered_crops)

product_categories = ['Onions', 'Tomatoes']

@app.route('/product_detail/<FarmerName>/<name>')
def product_detail(FarmerName, name):
    user = session.get('user')
    filtered_crops = []
    product=db.get_all_crops()
    print("product:", product)

    columns = [
        "id",
        "name",
        "price",
        "quantity",
        "unit",
        "CreatedAt",
        "farmer",
        "district",
        "image",
        "url",
        #"description"
    ]
    safe_email = user['email'].replace('@', '_at_').replace('.', '_dot_')  # Optional sanitization
    for row in product:
        FarmerName= row[6]  
        name = row[1]              
        if name==name and FarmerName==FarmerName:
            image_path =  "static/uploads/"+safe_email+"/"+name+"/img.jpg"
            url ="product_detail/"+FarmerName+name
            #des =  "static/uploads/"+safe_email+"/"+name+"/description.txt"
            #des1 = open(des, "r").read()
            row_with_image = list(row) + [image_path] +[url] #+ [des1]
            filtered_crops.append(dict(zip(columns, row_with_image)))
    product = products.get(name)
    if not product:
        return "Product not found", 404
    return render_template('product_detail.html', product=product)


@app.route('/productdetail')
def productdetail():
    
    product = {
        'name': 'Fresh Organic Oranges',
        'price': '₹80/kg',
        'district': 'Nagpur',
        'quantity': '100 kg',
        'farmer': 'Suresh Patil',
        'description': (
            'Juicy, sweet, and sun-ripened organic oranges directly from the orchards of Nagpur. '
            'These oranges are rich in vitamin C, naturally grown, and harvested without the use of '
            'any synthetic chemicals or pesticides. Perfect for boosting your immunity and refreshing your day!'
        ),
        'image': 'images/1.jpg'
    }
    return render_template('product_detail.html', product=product)

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

        upload_base = os.path.join("static", "uploads", safe_email, str(name))
        os.makedirs(upload_base, exist_ok=True)
 
        with open(upload_base+"/description.txt", "w") as f:
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
