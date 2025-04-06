import sqlite3

class FarmManagementDB:
    def __init__(self, db_name="farm_management.db"):
        self.db_name = db_name
        self.create_tables()

    def connect_db(self):
        return sqlite3.connect(self.db_name)

    def create_tables(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS user (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT,
                password TEXT
            );

            CREATE TABLE IF NOT EXISTS customer (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone_number TEXT,
                email TEXT,
                address TEXT,
                google_location_id TEXT
            );

            CREATE TABLE IF NOT EXISTS farmer (
                farmer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone_number TEXT,
                email TEXT,
                address TEXT,
                google_location_id TEXT
            );

            CREATE TABLE IF NOT EXISTS delivery_person (
                delivery_person_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone_number TEXT,
                email TEXT,
                address TEXT,
                google_location_id TEXT
            );

            CREATE TABLE IF NOT EXISTS customer_to_farmer_feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                feedback_message TEXT,
                farmer_id INTEGER,
                FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
                FOREIGN KEY (farmer_id) REFERENCES farmer(farmer_id)
            );

            CREATE TABLE IF NOT EXISTS customer_to_delivery_feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                feedback_message TEXT,
                delivery_person_id INTEGER,
                FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
                FOREIGN KEY (delivery_person_id) REFERENCES delivery_person(delivery_person_id)
            );

            CREATE TABLE IF NOT EXISTS product_items (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT
            );

            CREATE TABLE IF NOT EXISTS sales_product (
                sales_product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                farmer_id INTEGER,
                quantity_kg REAL,
                available_quantity REAL,
                description TEXT,
                image_url TEXT,
                FOREIGN KEY (product_id) REFERENCES product_items(product_id),
                FOREIGN KEY (farmer_id) REFERENCES farmer(farmer_id)
            );

            CREATE TABLE IF NOT EXISTS add_cart (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                product_id INTEGER,
                FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
                FOREIGN KEY (product_id) REFERENCES product_items(product_id)
            );

            CREATE TABLE IF NOT EXISTS payment (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                amount REAL,
                status TEXT,
                FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
            );
        ''')
        conn.commit()
        conn.close()

    def add_users(self, phone_number, password):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user (phone_number, password)
            VALUES (?, ?)""", (phone_number, password))
        conn.commit()
        conn.close()
        return True
    
    def add_users_detials(self):
        pass
    def insert_customer(self, name, phone_number, email, address, google_location_id):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customer (name, phone_number, email, address, google_location_id)
            VALUES (?, ?, ?, ?, ?)""", (name, phone_number, email, address, google_location_id))
        conn.commit()
        conn.close()

    def get_all_customers(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customer")
        customers = cursor.fetchall()
        conn.close()
        return customers

    def insert_farmer(self, name, phone_number, email, address, google_location_id):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO farmer (name, phone_number, email, address, google_location_id)
            VALUES (?, ?, ?, ?, ?)""", (name, phone_number, email, address, google_location_id))
        conn.commit()
        conn.close()

    def get_all_farmers(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM farmer")
        farmers = cursor.fetchall()
        conn.close()
        return farmers

    def insert_feedback_customer_to_farmer(self, customer_id, feedback_message, farmer_id):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customer_to_farmer_feedback (customer_id, feedback_message, farmer_id)
            VALUES (?, ?, ?)""", (customer_id, feedback_message, farmer_id))
        conn.commit()
        conn.close()

    def insert_feedback_customer_to_delivery(self, customer_id, feedback_message, delivery_person_id):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customer_to_delivery_feedback (customer_id, feedback_message, delivery_person_id)
            VALUES (?, ?, ?)""", (customer_id, feedback_message, delivery_person_id))
        conn.commit()
        conn.close()

    def insert_payment(self, customer_id, amount, status):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO payment (customer_id, amount, status)
            VALUES (?, ?, ?)""", (customer_id, amount, status))
        conn.commit()
        conn.close()

    def get_all_payments(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payment")
        payments = cursor.fetchall()
        conn.close()
        return payments


if __name__ == "__main__":
    db = FarmManagementDB()
    db.insert_customer("John Doe", "1234567890", "johndoe@example.com", "123 Main St", "loc123")
    db.insert_farmer("Alice Smith", "9876543210", "alice@example.com", "456 Farm Rd", "loc456")
    db.insert_feedback_customer_to_farmer(1, "Great produce!", 1)
    db.insert_payment(1, 20.5, "Completed")
    
    print("Customers:", db.get_all_customers())
    print("Farmers:", db.get_all_farmers())
    print("Payments:", db.get_all_payments())
