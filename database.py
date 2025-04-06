import sqlite3

class FarmManagementDB:
    def __init__(self, db_name="farm_management.db"):
        self.db_name = db_name
        self.create_tables()

    def connect_db(self):
        return sqlite3.connect(self.db_name)

    def create_tables(self):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.executescript('''
                    CREATE TABLE IF NOT EXISTS user (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        phone_number TEXT,
                        password TEXT
                    );

                    CREATE TABLE IF NOT EXISTS er_Farmer (
                        FarmerID INTEGER PRIMARY KEY AUTOINCREMENT,
                        Name TEXT NOT NULL,
                        AadharNumber TEXT UNIQUE NOT NULL CHECK (length(AadharNumber) = 12),
                        Contact TEXT CHECK (length(Contact) BETWEEN 10 AND 15),
                        Address TEXT
                    );

                    CREATE TABLE IF NOT EXISTS er_Crop (
                        CropID INTEGER PRIMARY KEY AUTOINCREMENT,
                        Name TEXT NOT NULL,
                        Price REAL NOT NULL CHECK (Price > 0),
                        FarmerID INTEGER NOT NULL,
                        FOREIGN KEY (FarmerID) REFERENCES er_Farmer(FarmerID) ON DELETE CASCADE,
                        UNIQUE(FarmerID, Name)
                    );

                    CREATE TABLE IF NOT EXISTS er_Customer (
                        CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
                        Name TEXT NOT NULL,
                        Contact TEXT CHECK (length(Contact) BETWEEN 10 AND 15),
                        Address TEXT
                    );

                    CREATE TABLE IF NOT EXISTS er_Orders (
                        OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
                        CustomerID INTEGER NOT NULL,
                        OrderDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        Status TEXT DEFAULT 'Pending',
                        FOREIGN KEY (CustomerID) REFERENCES er_Customer(CustomerID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS er_OrderDetails (
                        OrderDetailID INTEGER PRIMARY KEY AUTOINCREMENT,
                        OrderID INTEGER NOT NULL,
                        CropID INTEGER NOT NULL,
                        Quantity INTEGER NOT NULL CHECK (Quantity > 0),
                        FOREIGN KEY (OrderID) REFERENCES er_Orders(OrderID) ON DELETE CASCADE,
                        FOREIGN KEY (CropID) REFERENCES er_Crop(CropID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS er_Payment (
                        PaymentID INTEGER PRIMARY KEY AUTOINCREMENT,
                        OrderID INTEGER NOT NULL,
                        Amount REAL NOT NULL CHECK (Amount >= 0),
                        PaymentDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        Status TEXT DEFAULT 'Pending',
                        FOREIGN KEY (OrderID) REFERENCES er_Orders(OrderID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS er_Delivery (
                        DeliveryID INTEGER PRIMARY KEY AUTOINCREMENT,
                        OrderID INTEGER NOT NULL,
                        Location TEXT NOT NULL,
                        DeliveryDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        Status TEXT DEFAULT 'Pending',
                        FOREIGN KEY (OrderID) REFERENCES er_Orders(OrderID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS er_Feedback (
                        FeedbackID INTEGER PRIMARY KEY AUTOINCREMENT,
                        CustomerID INTEGER NOT NULL,
                        OrderID INTEGER NOT NULL,
                        Comments TEXT,
                        Rating INTEGER CHECK (Rating BETWEEN 1 AND 5),
                        FOREIGN KEY (CustomerID) REFERENCES er_Customer(CustomerID) ON DELETE CASCADE,
                        FOREIGN KEY (OrderID) REFERENCES er_Orders(OrderID) ON DELETE CASCADE
                    );
                ''')
                conn.commit()
        except sqlite3.Error as e:
            print("[create_tables] Error:", e)

    # ------------------ INSERT FUNCTIONS ------------------
    def insert_farmer(self, name, aadhar, contact, address):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO er_Farmer (Name, AadharNumber, Contact, Address) VALUES (?, ?, ?, ?)",
                               (name, aadhar, contact, address))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_farmer] Error inserting farmer: {e}")
            return None

    def insert_crop(self, name, price, farmer_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO er_Crop (Name, Price, FarmerID) VALUES (?, ?, ?)",
                               (name, price, farmer_id))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_crop] Error inserting crop: {e}")
            return None

    def insert_customer(self, name, contact, address):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO er_Customer (Name, Contact, Address) VALUES (?, ?, ?)",
                               (name, contact, address))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_customer] Error inserting customer: {e}")
            return None

    def insert_order(self, customer_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO er_Orders (CustomerID) VALUES (?)", (customer_id,))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_order] Error inserting order: {e}")
            return None

    def insert_order_detail(self, order_id, crop_id, quantity):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO er_OrderDetails (OrderID, CropID, Quantity) VALUES (?, ?, ?)",
                               (order_id, crop_id, quantity))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_order_detail] Error inserting order detail: {e}")
            return None

    def insert_payment(self, order_id, amount):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO er_Payment (OrderID, Amount) VALUES (?, ?)",
                               (order_id, amount))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_payment] Error inserting payment: {e}")
            return None

    def insert_delivery(self, order_id, location):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO er_Delivery (OrderID, Location) VALUES (?, ?)",
                               (order_id, location))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_delivery] Error inserting delivery: {e}")
            return None

    def insert_feedback(self, customer_id, order_id, comments, rating):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO er_Feedback (CustomerID, OrderID, Comments, Rating) VALUES (?, ?, ?, ?)",
                               (customer_id, order_id, comments, rating))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_feedback] Error inserting feedback: {e}")
            return None
