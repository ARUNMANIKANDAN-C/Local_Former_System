from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
csrf = CSRFProtect(app)

# ------------------------
# Dummy User Data
# ------------------------
users = {
    '1234567890': 'pass1234'
}

# ------------------------
# Sample Data
# ------------------------
main_product = {
    "name": "Sample Product",
    "price": 49.99,
    "description": "This is a great product.",
    "category": "Electronics",
    "stock": 10,
    "image": {"url": "https://via.placeholder.com/300"},
    "reviews": []
}

products = [
    {"id": 1, "name": "Product 1", "price": 100, "district": "District A", "image": "1.jpg"},
    {"id": 2, "name": "Product 2", "price": 200, "district": "District B", "image": "2.jpg"},
    {"id": 3, "name": "Product 3", "price": 300, "district": "District C", "image": "3.jpg"},
    {"id": 4, "name": "Product 4", "price": 400, "district": "District A", "image": "4.jpg"},
    {"id": 5, "name": "Product 5", "price": 500, "district": "District B", "image": "5.jpg"},
    {"id": 6, "name": "Product 6", "price": 600, "district": "District C", "image": "6.jpg"},
]

# ------------------------
# Routes
# ------------------------

@app.route('/')
def index():
    return redirect(url_for('login'))

# ---------- Home & Reviews ----------

@app.route("/home")
def home():
    return render_template("home.html", product=main_product)

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

# ---------- Product Search ----------

@app.route('/available_products', methods=['GET', 'POST'])
def search_products():
    filtered_products = products

    if request.method == 'POST':
        search_query = request.form.get('search', '').lower()
        product_name = request.form.get('product', '').lower()
        district = request.form.get('district', '').lower()
        price_input = request.form.get('price', '')

        try:
            price = int(price_input) if price_input else None
        except ValueError:
            price = None

        filtered_products = [
            p for p in products
            if (not search_query or search_query in p["name"].lower())
            and (not product_name or product_name in p["name"].lower())
            and (not district or district in p["district"].lower())
            and (not price or p["price"] <= price)
        ]

    return render_template('available_products.html', products=filtered_products)

# ---------- Auth ----------

@app.route('/sign_in', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"New user signed up: {username}, {email}, {password}")
    return render_template('sign_in.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('passkey')

        if phone in users and users[phone] == password:
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid phone number or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('Dashboard.html')

# ---------- Product List & Detail ----------

@app.route('/products')
def product_list():
    return render_template('product_list.html', products=products)

@app.route('/products/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return "Product not found", 404
    return render_template('product_detail.html', product=product)

# ------------------------
# Run the App
# ------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
