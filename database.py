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
                    CREATE TABLE IF NOT EXISTS Person (
                        PersonID INTEGER PRIMARY KEY AUTOINCREMENT,
                        Name TEXT NOT NULL,
                        Contact TEXT CHECK (length(Contact) BETWEEN 10 AND 15),
                        Address TEXT,
                        CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS User (
                        UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                        PhoneNumber TEXT UNIQUE,
                        Password TEXT NOT NULL,
                        PersonID INTEGER,
                        CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (PersonID) REFERENCES Person(PersonID) ON DELETE SET NULL
                    );

                    CREATE TABLE IF NOT EXISTS Farmer (
                        FarmerID INTEGER PRIMARY KEY AUTOINCREMENT,
                        PersonID INTEGER NOT NULL,
                        AadharNumber TEXT UNIQUE NOT NULL CHECK (length(AadharNumber) = 12),
                        FOREIGN KEY (PersonID) REFERENCES Person(PersonID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS Customer (
                        CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
                        PersonID INTEGER NOT NULL,
                        FOREIGN KEY (PersonID) REFERENCES Person(PersonID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS Crop (
                        CropID INTEGER PRIMARY KEY AUTOINCREMENT,
                        Name TEXT NOT NULL,
                        Price REAL NOT NULL CHECK (Price > 0),
                        FarmerID INTEGER NOT NULL,
                        CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (FarmerID) REFERENCES Farmer(FarmerID) ON DELETE CASCADE,
                        UNIQUE(FarmerID, Name)
                    );

                    CREATE TABLE IF NOT EXISTS Orders (
                        OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
                        CustomerID INTEGER NOT NULL,
                        OrderDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        Status TEXT DEFAULT 'Pending',
                        FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS OrderDetails (
                        OrderDetailID INTEGER PRIMARY KEY AUTOINCREMENT,
                        OrderID INTEGER NOT NULL,
                        CropID INTEGER NOT NULL,
                        Quantity INTEGER NOT NULL CHECK (Quantity > 0),
                        FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE,
                        FOREIGN KEY (CropID) REFERENCES Crop(CropID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS Payment (
                        PaymentID INTEGER PRIMARY KEY AUTOINCREMENT,
                        OrderID INTEGER NOT NULL,
                        Amount REAL NOT NULL CHECK (Amount >= 0),
                        PaymentDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        Status TEXT DEFAULT 'Pending',
                        FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS Delivery (
                        DeliveryID INTEGER PRIMARY KEY AUTOINCREMENT,
                        OrderID INTEGER NOT NULL,
                        Location TEXT NOT NULL,
                        DeliveryDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        Status TEXT DEFAULT 'Pending',
                        FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS Feedback (
                        FeedbackID INTEGER PRIMARY KEY AUTOINCREMENT,
                        CustomerID INTEGER NOT NULL,
                        OrderID INTEGER NOT NULL,
                        Comments TEXT,
                        Rating INTEGER CHECK (Rating BETWEEN 1 AND 5),
                        FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID) ON DELETE CASCADE,
                        FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE
                    );
                ''')
        except sqlite3.Error as e:
            print(f"[create_tables] Error: {e}")

    # ---------- INSERT METHODS ----------
    def insert_person(self, name, contact, address):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Person (Name, Contact, Address) VALUES (?, ?, ?)",
                               (name, contact, address))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_person] Error: {e}")
            return None

    def insert_farmer(self, person_id, aadhar):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Farmer (PersonID, AadharNumber) VALUES (?, ?)",
                               (person_id, aadhar))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_farmer] Error: {e}")
            return None

    def insert_customer(self, person_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Customer (PersonID) VALUES (?)", (person_id,))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_customer] Error: {e}")
            return None

    def insert_crop(self, name, price, farmer_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Crop (Name, Price, FarmerID) VALUES (?, ?, ?)",
                               (name, price, farmer_id))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_crop] Error: {e}")
            return None

    def insert_order(self, customer_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Orders (CustomerID) VALUES (?)", (customer_id,))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_order] Error: {e}")
            return None

    def insert_order_detail(self, order_id, crop_id, quantity):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO OrderDetails (OrderID, CropID, Quantity) VALUES (?, ?, ?)",
                               (order_id, crop_id, quantity))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_order_detail] Error: {e}")
            return None

    def insert_payment(self, order_id, amount):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Payment (OrderID, Amount) VALUES (?, ?)",
                               (order_id, amount))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_payment] Error: {e}")
            return None

    def insert_delivery(self, order_id, location):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Delivery (OrderID, Location) VALUES (?, ?)",
                               (order_id, location))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_delivery] Error: {e}")
            return None

    def insert_feedback(self, customer_id, order_id, comments, rating):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Feedback (CustomerID, OrderID, Comments, Rating) VALUES (?, ?, ?, ?)",
                               (customer_id, order_id, comments, rating))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_feedback] Error: {e}")
            return None
    
    #----------- BULK INSERT METHODS ----------
    def insert_many_persons(self, persons):
        """
        persons: List of tuples [(name, contact, address), ...]
        """
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.executemany("INSERT INTO Person (Name, Contact, Address) VALUES (?, ?, ?)", persons)
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_many_persons] Error: {e}")
            return None

    def insert_many_farmers(self, farmers):
        """
        farmers: List of tuples [(person_id, aadhar), ...]
        """
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.executemany("INSERT INTO Farmer (PersonID, AadharNumber) VALUES (?, ?)", farmers)
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_many_farmers] Error: {e}")
            return None

    def insert_many_crops(self, crops):
        """
        crops: List of tuples [(name, price, farmer_id), ...]
        """
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.executemany("INSERT INTO Crop (Name, Price, FarmerID) VALUES (?, ?, ?)", crops)
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_many_crops] Error: {e}")
            return None

    #----------- UPDATE METHODS ----------
    def update_person(self, person_id, name=None, contact=None, address=None):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                if name:
                    cursor.execute("UPDATE Person SET Name = ? WHERE PersonID = ?", (name, person_id))
                if contact:
                    cursor.execute("UPDATE Person SET Contact = ? WHERE PersonID = ?", (contact, person_id))
                if address:
                    cursor.execute("UPDATE Person SET Address = ? WHERE PersonID = ?", (address, person_id))
                return cursor.rowcount
        except sqlite3.Error as e:
            print(f"[update_person] Error: {e}")
            return None
        
    

    # ---------- SELECT METHODS ----------
    def get_person(self, person_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM Person WHERE PersonID = ?", (person_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[get_person] Error: {e}")
            return None

# Run this section only when executing directly
if __name__ == "__main__":
    db = FarmManagementDB()
    print("Database and tables created successfully.")

    # --- Insert Persons (Farmers) ---
    farmer_persons = [
        ("Ravi Kumar", "9990001111", "Village A"),
        ("Meena Singh", "8881112222", "Village B"),
        ("Arun Yadav", "7772223333", "Village C")
    ]
    db.insert_many_persons(farmer_persons)

    # Assuming IDs are 1, 2, 3 (auto-incremented)
    farmer_list = [
        (1, "123456789012"),
        (2, "234567890123"),
        (3, "345678901234")
    ]
    db.insert_many_farmers(farmer_list)

    # --- Insert Crops ---
    crop_list = [
        ("Wheat", 25.0, 1),
        ("Rice", 30.5, 1),
        ("Tomato", 15.0, 2),
        ("Onion", 12.0, 2),
        ("Potato", 18.0, 3),
        ("Carrot", 20.0, 3)
    ]
    db.insert_many_crops(crop_list)

        # --- Insert Persons (Customers) ---
    customer_persons = [
        ("Anjali Verma", "9998887777", "City X"),
        ("Rohan Das", "9998886666", "City Y"),
    ]
    db.insert_many_persons(customer_persons)

    # Assuming person IDs are 4 and 5
    customer_list = [
        (4,),
        (5,)
    ]
    with db.connect_db() as conn:
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO Customer (PersonID) VALUES (?)", customer_list)
        conn.commit()

    # --- Insert Orders for Customer 1 (ID=1) ---
    order_id = db.insert_order(1)

    # --- Add OrderDetails (Cart Items) ---
    db.insert_order_detail(order_id, 1, 5)  # 5kg Wheat
    db.insert_order_detail(order_id, 3, 3)  # 3kg Tomato

    # --- Payment ---
    db.insert_payment(order_id, 25.0 * 5 + 15.0 * 3)

    # --- Delivery ---
    db.insert_delivery(order_id, "City X Main Street")

    # --- Feedback ---
    db.insert_feedback(1, order_id, "Great quality!", 5)
    
    print("Sample data inserted successfully.")