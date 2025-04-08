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

                    CREATE TABLE IF NOT EXISTS User (
                    EmailID TEXT PRIMARY KEY,
                    Name TEXT NOT NULL,
                    PhoneNumber INTEGER CHECK (length(PhoneNumber) = 10),
                    Password TEXT NOT NULL,
                    Address TEXT,
                    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UserType TEXT NOT NULL CHECK (UserType IN ('Farmer', 'Customer', 'DeliveryPerson'))
                );

                    CREATE TABLE IF NOT EXISTS Farmer (
                        FarmerID INTEGER PRIMARY KEY AUTOINCREMENT,
                        UserID TEXT NOT NULL,
                        AadharNumber TEXT UNIQUE NOT NULL CHECK (length(AadharNumber) = 12),
                        FOREIGN KEY (UserID) REFERENCES User(EmailID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS Customer (
                        CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
                        UserID TEXT NOT NULL,
                        FOREIGN KEY (UserID) REFERENCES User(EmailID) ON DELETE CASCADE
                    );
                    
                    CREATE TABLE IF NOT EXISTS DeliveryPerson (
                        DeliveryPersonID INTEGER PRIMARY KEY AUTOINCREMENT,
                        UserID TEXT NOT NULL,
                        LicenseNumber TEXT UNIQUE NOT NULL,
                        VehicleType TEXT NOT NULL,
                        VehicleNumber TEXT UNIQUE NOT NULL,
                        AvailabilityStatus TEXT DEFAULT 'Available',
                        FOREIGN KEY (UserID) REFERENCES User(EmailID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS Crop (
                        CropID INTEGER PRIMARY KEY AUTOINCREMENT,
                        Name TEXT NOT NULL,
                        Price REAL NOT NULL CHECK (Price > 0),
                        FarmerID INTEGER NOT NULL,
                        QuantityAvailable REAL DEFAULT 0 CHECK (QuantityAvailable >= 0),
                        Unit TEXT DEFAULT 'kg',
                        CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (FarmerID) REFERENCES Farmer(FarmerID) ON DELETE CASCADE,
                        UNIQUE(FarmerID, Name)
                    );

                    CREATE TABLE IF NOT EXISTS Orders (
                        OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
                        CustomerID INTEGER NOT NULL,
                        OrderDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        Status TEXT DEFAULT 'Pending',
                        TotalAmount REAL DEFAULT 0,
                        FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS OrderDetails (
                        OrderDetailID INTEGER PRIMARY KEY AUTOINCREMENT,
                        OrderID INTEGER NOT NULL,
                        CropID INTEGER NOT NULL,
                        Quantity INTEGER NOT NULL CHECK (Quantity > 0),
                        UnitPrice REAL NOT NULL CHECK (UnitPrice > 0),
                        SubTotal REAL NOT NULL CHECK (SubTotal > 0),
                        FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE,
                        FOREIGN KEY (CropID) REFERENCES Crop(CropID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS Payment (
                        PaymentID INTEGER PRIMARY KEY AUTOINCREMENT,
                        OrderID INTEGER NOT NULL,
                        Amount REAL NOT NULL CHECK (Amount >= 0),
                        PaymentDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PaymentMethod TEXT DEFAULT 'Cash',
                        TransactionID TEXT UNIQUE,
                        Status TEXT DEFAULT 'Pending',
                        FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS Delivery (
                        DeliveryID INTEGER PRIMARY KEY AUTOINCREMENT,
                        OrderID INTEGER NOT NULL,
                        DeliveryPersonID INTEGER,
                        PickupLocation TEXT NOT NULL,
                        DeliveryLocation TEXT NOT NULL,
                        AssignedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        EstimatedDeliveryTime TIMESTAMP,
                        ActualDeliveryTime TIMESTAMP,
                        Status TEXT DEFAULT 'Pending',
                        FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE,
                        FOREIGN KEY (DeliveryPersonID) REFERENCES DeliveryPerson(DeliveryPersonID) ON DELETE SET NULL
                    );
                    
                    CREATE TABLE IF NOT EXISTS DeliveryHistory (
                        HistoryID INTEGER PRIMARY KEY AUTOINCREMENT,
                        DeliveryID INTEGER NOT NULL,
                        StatusUpdate TEXT NOT NULL,
                        UpdateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        Location TEXT,
                        Notes TEXT,
                        FOREIGN KEY (DeliveryID) REFERENCES Delivery(DeliveryID) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS Feedback (
                        FeedbackID INTEGER PRIMARY KEY AUTOINCREMENT,
                        CustomerID INTEGER NOT NULL,
                        OrderID INTEGER NOT NULL,
                        Comments TEXT,
                        Rating INTEGER CHECK (Rating BETWEEN 1 AND 5),
                        FeedbackDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID) ON DELETE CASCADE,
                        FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE
                    );
                    
                    CREATE TABLE IF NOT EXISTS DeliveryRating (
                        RatingID INTEGER PRIMARY KEY AUTOINCREMENT,
                        DeliveryID INTEGER NOT NULL,
                        DeliveryPersonID INTEGER NOT NULL,
                        CustomerID INTEGER NOT NULL,
                        Rating INTEGER CHECK (Rating BETWEEN 1 AND 5),
                        Comments TEXT,
                        RatingDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (DeliveryID) REFERENCES Delivery(DeliveryID) ON DELETE CASCADE,
                        FOREIGN KEY (DeliveryPersonID) REFERENCES DeliveryPerson(DeliveryPersonID) ON DELETE CASCADE,
                        FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID) ON DELETE CASCADE
                    );
                ''')
        except sqlite3.Error as e:
            print(f"[create_tables] Error: {e}")

    # ---------- INSERT METHODS ----------
    def insert_user(self, name, email_id, phone_number, password, address, user_type):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO User (Name, EmailID, PhoneNumber, Password, Address, UserType) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, email_id, phone_number, password, address, user_type))
                return email_id  # Return the primary key
        except sqlite3.Error as e:
            print(f"[insert_user] Error: {e}")
            return None

    def insert_farmer(self, user_id, aadhar):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Farmer (UserID, AadharNumber) VALUES (?, ?)",
                               (user_id, aadhar))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_farmer] Error: {e}")
            return None

    def insert_customer(self, user_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Customer (UserID) VALUES (?)", (user_id,))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_customer] Error: {e}")
            return None
            
    def insert_delivery_person(self, user_id, license_number, vehicle_type, vehicle_number, current_location=None):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO DeliveryPerson 
                    (UserID, LicenseNumber, VehicleType, VehicleNumber, CurrentLocation) 
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, license_number, vehicle_type, vehicle_number, current_location))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_delivery_person] Error: {e}")
            return None

    def insert_crop(self, name, price, farmer_id, quantity_available=0, unit='kg'):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Crop (Name, Price, FarmerID, QuantityAvailable, Unit) 
                    VALUES (?, ?, ?, ?, ?)
                """, (name, price, farmer_id, quantity_available, unit))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_crop] Error: {e}")
            return None

    def insert_order(self, customer_id, total_amount=0):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Orders (CustomerID, TotalAmount) VALUES (?, ?)", 
                              (customer_id, total_amount))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_order] Error: {e}")
            return None

    def insert_order_detail(self, order_id, crop_id, quantity, unit_price):
        try:
            subtotal = quantity * unit_price
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO OrderDetails (OrderID, CropID, Quantity, UnitPrice, SubTotal) 
                    VALUES (?, ?, ?, ?, ?)
                """, (order_id, crop_id, quantity, unit_price, subtotal))
                
                # Update the total amount in Orders table
                cursor.execute("""
                    UPDATE Orders 
                    SET TotalAmount = TotalAmount + ? 
                    WHERE OrderID = ?
                """, (subtotal, order_id))
                
                # Update crop inventory
                cursor.execute("""
                    UPDATE Crop 
                    SET QuantityAvailable = QuantityAvailable - ? 
                    WHERE CropID = ?
                """, (quantity, crop_id))
                
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_order_detail] Error: {e}")
            return None

    def insert_payment(self, order_id, amount, payment_method='Cash', transaction_id=None):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Payment (OrderID, Amount, PaymentMethod, TransactionID) 
                    VALUES (?, ?, ?, ?)
                """, (order_id, amount, payment_method, transaction_id))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_payment] Error: {e}")
            return None

    def insert_delivery(self, order_id, pickup_location, delivery_location, delivery_person_id=None, estimated_delivery_time=None):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Delivery 
                    (OrderID, DeliveryPersonID, PickupLocation, DeliveryLocation, EstimatedDeliveryTime) 
                    VALUES (?, ?, ?, ?, ?)
                """, (order_id, delivery_person_id, pickup_location, delivery_location, estimated_delivery_time))
                delivery_id = cursor.lastrowid
                
                # Add initial entry to delivery history
                cursor.execute("""
                    INSERT INTO DeliveryHistory (DeliveryID, StatusUpdate, Location) 
                    VALUES (?, ?, ?)
                """, (delivery_id, "Delivery created", pickup_location))
                
                return delivery_id
        except sqlite3.Error as e:
            print(f"[insert_delivery] Error: {e}")
            return None
            
    def insert_delivery_history(self, delivery_id, status_update, location=None, notes=None):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO DeliveryHistory (DeliveryID, StatusUpdate, Location, Notes) 
                    VALUES (?, ?, ?, ?)
                """, (delivery_id, status_update, location, notes))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_delivery_history] Error: {e}")
            return None

    def insert_feedback(self, customer_id, order_id, comments, rating):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Feedback (CustomerID, OrderID, Comments, Rating) 
                    VALUES (?, ?, ?, ?)
                """, (customer_id, order_id, comments, rating))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_feedback] Error: {e}")
            return None
            
    def insert_delivery_rating(self, delivery_id, delivery_person_id, customer_id, rating, comments=None):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO DeliveryRating 
                    (DeliveryID, DeliveryPersonID, CustomerID, Rating, Comments) 
                    VALUES (?, ?, ?, ?, ?)
                """, (delivery_id, delivery_person_id, customer_id, rating, comments))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[insert_delivery_rating] Error: {e}")
            return None

    # ---------- UPDATE METHODS ----------
    def update_user(self, email_id, name=None, phone_number=None, password=None, address=None):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                if name:
                    cursor.execute("UPDATE User SET Name = ? WHERE EmailID = ?", (name, email_id))
                if phone_number:
                    cursor.execute("UPDATE User SET PhoneNumber = ? WHERE EmailID = ?", (phone_number, email_id))
                if password:
                    cursor.execute("UPDATE User SET Password = ? WHERE EmailID = ?", (password, email_id))
                if address:
                    cursor.execute("UPDATE User SET Address = ? WHERE EmailID = ?", (address, email_id))
                return cursor.rowcount
        except sqlite3.Error as e:  
            print(f"[update_user] Error: {e}")
            return None
    
    def update_crop(self, crop_id, name=None, price=None, quantity_available=None, unit=None):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                if name:
                    cursor.execute("UPDATE Crop SET Name = ? WHERE CropID = ?", (name, crop_id))
                if price:
                    cursor.execute("UPDATE Crop SET Price = ? WHERE CropID = ?", (price, crop_id))
                if quantity_available is not None:
                    cursor.execute("UPDATE Crop SET QuantityAvailable = ? WHERE CropID = ?", (quantity_available, crop_id))
                if unit:
                    cursor.execute("UPDATE Crop SET Unit = ? WHERE CropID = ?", (unit, crop_id))
                return cursor.rowcount
        except sqlite3.Error as e:
            print(f"[update_crop] Error: {e}")
            return None
        
    def update_order_status(self, order_id, status):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE Orders SET Status = ? WHERE OrderID = ?", (status, order_id))
                return cursor.rowcount
        except sqlite3.Error as e:
            print(f"[update_order_status] Error: {e}")
            return None
    
    def update_payment_status(self, payment_id, status):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE Payment SET Status = ? WHERE PaymentID = ?", (status, payment_id))
                return cursor.rowcount
        except sqlite3.Error as e:
            print(f"[update_payment_status] Error: {e}")
            return None 
    
    def update_delivery_status(self, delivery_id, status, location=None):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE Delivery SET Status = ? WHERE DeliveryID = ?", (status, delivery_id))
                
                # Add status update to history
                if status == "Delivered":
                    cursor.execute("UPDATE Delivery SET ActualDeliveryTime = CURRENT_TIMESTAMP WHERE DeliveryID = ?", (delivery_id,))
                
                # Add entry to delivery history
                self.insert_delivery_history(delivery_id, status, location)
                
                return cursor.rowcount
        except sqlite3.Error as e:
            print(f"[update_delivery_status] Error: {e}")
            return None
            
    def update_delivery_person_status(self, delivery_person_id, status, current_location=None):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE DeliveryPerson 
                    SET AvailabilityStatus = ? 
                    WHERE DeliveryPersonID = ?
                """, (status, delivery_person_id))
                
                if current_location:
                    cursor.execute("""
                        UPDATE DeliveryPerson 
                        SET CurrentLocation = ? 
                        WHERE DeliveryPersonID = ?
                    """, (current_location, delivery_person_id))
                
                return cursor.rowcount
        except sqlite3.Error as e:
            print(f"[update_delivery_person_status] Error: {e}")
            return None
    
    def update_feedback(self, feedback_id, comments=None, rating=None):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                if comments:
                    cursor.execute("UPDATE Feedback SET Comments = ? WHERE FeedbackID = ?", (comments, feedback_id))
                if rating:
                    cursor.execute("UPDATE Feedback SET Rating = ? WHERE FeedbackID = ?", (rating, feedback_id))
                return cursor.rowcount
        except sqlite3.Error as e:
            print(f"[update_feedback] Error: {e}")
            return None
    
    def assign_delivery_person(self, delivery_id, delivery_person_id, estimated_delivery_time=None):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Delivery 
                    SET DeliveryPersonID = ?, AssignedAt = CURRENT_TIMESTAMP 
                    WHERE DeliveryID = ?
                """, (delivery_person_id, delivery_id))
                
                if estimated_delivery_time:
                    cursor.execute("""
                        UPDATE Delivery 
                        SET EstimatedDeliveryTime = ? 
                        WHERE DeliveryID = ?
                    """, (estimated_delivery_time, delivery_id))
                
                # Update delivery person status to 'Assigned'
                cursor.execute("""
                    UPDATE DeliveryPerson 
                    SET AvailabilityStatus = 'Assigned' 
                    WHERE DeliveryPersonID = ?
                """, (delivery_person_id,))
                
                # Add entry to delivery history
                delivery = self.get_delivery(delivery_id)
                if delivery:
                    delivery_person = self.get_delivery_person(delivery_person_id)
                    if delivery_person:
                        user = self.get_user_by_email(delivery_person[1])  # UserID in DeliveryPerson
                        if user:
                            self.insert_delivery_history(
                                delivery_id, 
                                f"Assigned to {user[1]}",  # User Name
                                delivery_person[6],  # CurrentLocation
                                f"Delivery person assigned with vehicle {delivery_person[3]} {delivery_person[4]}"
                            )
                
                return cursor.rowcount
        except sqlite3.Error as e:
            print(f"[assign_delivery_person] Error: {e}")
            return None

    # ---------- DELETE METHODS ----------
    def delete_user(self, email_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM User WHERE EmailID = ?", (email_id,))
                return cursor.rowcount
        except sqlite3.Error as e:
            print(f"[delete_user] Error: {e}")
            return None
            
    def delete_delivery_person(self, delivery_person_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM DeliveryPerson WHERE DeliveryPersonID = ?", (delivery_person_id,))
                return cursor.rowcount
        except sqlite3.Error as e:
            print(f"[delete_delivery_person] Error: {e}")
            return None

    # ---------- SELECT METHODS ----------
    def get_user_by_email(self, email_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM User WHERE EmailID = ?", (email_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[get_user_by_email] Error: {e}")
            return None
            
    def get_user_by_phone(self, phone_number):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM User WHERE PhoneNumber = ?", (phone_number,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[get_user_by_phone] Error: {e}")
            return None
            
    def get_farmer(self, farmer_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT f.*, u.Name, u.EmailID, u.Address 
                    FROM Farmer f
                    JOIN User u ON f.UserID = u.EmailID
                    WHERE f.FarmerID = ?
                """, (farmer_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[get_farmer] Error: {e}")
            return None
            
    def get_customer(self, customer_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.*, u.Name, u.EmailID, u.Address 
                    FROM Customer c
                    JOIN User u ON c.UserID = u.EmailID
                    WHERE c.CustomerID = ?
                """, (customer_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[get_customer] Error: {e}")
            return None
            
    def get_delivery_person(self, delivery_person_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dp.*, u.Name, u.EmailID, u.Address 
                    FROM DeliveryPerson dp
                    JOIN User u ON dp.UserID = u.EmailID
                    WHERE dp.DeliveryPersonID = ?
                """, (delivery_person_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[get_delivery_person] Error: {e}")
            return None
            
    def get_available_delivery_persons(self, location=None):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                if location:
                    # If location is provided, try to find delivery persons near that location
                    # This is simplified and would need actual geo-location calculation in a real app
                    cursor.execute("""
                        SELECT dp.*, u.Name, u.EmailID, u.Address 
                        FROM DeliveryPerson dp
                        JOIN User u ON dp.UserID = u.EmailID
                        WHERE dp.AvailabilityStatus = 'Available'
                        ORDER BY 
                            CASE 
                                WHEN dp.CurrentLocation = ? THEN 0
                                ELSE 1
                            END
                    """, (location,))
                else:
                    cursor.execute("""
                        SELECT dp.*, u.Name, u.EmailID, u.Address 
                        FROM DeliveryPerson dp
                        JOIN User u ON dp.UserID = u.EmailID
                        WHERE dp.AvailabilityStatus = 'Available'
                    """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[get_available_delivery_persons] Error: {e}")
            return None
            
    def get_delivery(self, delivery_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM Delivery WHERE DeliveryID = ?", (delivery_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[get_delivery] Error: {e}")
            return None
            
    def get_delivery_history(self, delivery_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM DeliveryHistory WHERE DeliveryID = ? ORDER BY UpdateTime", (delivery_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[get_delivery_history] Error: {e}")
            return None
            
    def get_delivery_person_statistics(self, delivery_person_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                
                # Get total deliveries
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM Delivery 
                    WHERE DeliveryPersonID = ?
                """, (delivery_person_id,))
                total_deliveries = cursor.fetchone()[0]
                
                # Get completed deliveries
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM Delivery 
                    WHERE DeliveryPersonID = ? AND Status = 'Delivered'
                """, (delivery_person_id,))
                completed_deliveries = cursor.fetchone()[0]
                
                # Get average rating
                cursor.execute("""
                    SELECT AVG(Rating) 
                    FROM DeliveryRating 
                    WHERE DeliveryPersonID = ?
                """, (delivery_person_id,))
                avg_rating = cursor.fetchone()[0]
                
                return {
                    "total_deliveries": total_deliveries,
                    "completed_deliveries": completed_deliveries,
                    "average_rating": avg_rating if avg_rating else 0
                }
        except sqlite3.Error as e:
            print(f"[get_delivery_person_statistics] Error: {e}")
            return None
            
    def get_order_details_with_delivery(self, order_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT o.*, d.DeliveryID, d.Status as DeliveryStatus, d.DeliveryPersonID,
                           dp.VehicleType, dp.VehicleNumber,
                           u.Name as DeliveryPersonName, u.EmailID as DeliveryPersonEmail
                    FROM Orders o
                    LEFT JOIN Delivery d ON o.OrderID = d.OrderID
                    LEFT JOIN DeliveryPerson dp ON d.DeliveryPersonID = dp.DeliveryPersonID
                    LEFT JOIN User u ON dp.UserID = u.EmailID
                    WHERE o.OrderID = ?
                """, (order_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[get_order_details_with_delivery] Error: {e}")
            return None

    def count_all_users(self):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM User")
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"[count_all_users] Error: {e}")
            return None
    
    def count_users_by_type(self, user_type):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM User WHERE UserType = ?", (user_type,))
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"[count_users_by_type] Error: {e}")
            return None
    
    def count_all_crops(self):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM Crop")
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"[count_all_crops] Error: {e}")
            return None
        
    def count_all_orders(self):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM Orders")
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"[count_all_orders] Error: {e}")
            return None
        
    def count_all_feedbacks(self): 
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM Feedback")
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"[count_all_feedbacks] Error: {e}")
            return None
    
    def get_all_users(self):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM User")
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[get_all_users] Error: {e}")
            return None
    
    def get_all_farmers(self):

        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT f.*, u.Name, u.EmailID, u.Address 
                    FROM Farmer f
                    JOIN User u ON f.UserID = u.EmailID
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[get_all_farmers] Error: {e}")
            return None
        
    def get_all_customers(self):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.*, u.Name, u.EmailID, u.Address 
                    FROM Customer c
                    JOIN User u ON c.UserID = u.EmailID
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[get_all_customers] Error: {e}")
            return None
    def get_products_userid(self, user_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM Crop WHERE FarmerID = ?
                """, (user_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[get_products_userid] Error: {e}")
            return None
        
    def get_all_orders_by_users(self, user_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT o.*, u.Name, u.EmailID, u.Address 
                    FROM Orders o
                    JOIN User u ON o.CustomerID = u.EmailID
                    WHERE o.CustomerID = ?
                """, (user_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[get_all_orders_by_users] Error: {e}")
            return None
    
    def get_monthly_sales_by_user(self, user_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT strftime('%Y-%m', OrderDate) as Month, SUM(TotalAmount) as TotalSales
                    FROM Orders
                    WHERE CustomerID = ?
                    GROUP BY Month
                """, (user_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[get_monthly_sales_by_user] Error: {e}")
            return None
    
    def get_mostamout_spend_by_coustmer_to_farmer(self, customer_id, former_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT SUM(TotalAmount) as TotalSpent
                    FROM Orders o
                    JOIN OrderDetails od ON o.OrderID = od.OrderID
                    WHERE o.CustomerID = ? AND od.CropID IN (
                        SELECT CropID FROM Crop WHERE FarmerID = ?
                    )
                """, (customer_id, former_id))
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"[get_mostamout_spend_by_coustmer_to_farmer] Error: {e}")
            return None
        
    def get_slaes_with_price_over_by_last_5_month_for_former(self, farmer_id, price):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT strftime('%Y-%m', OrderDate) as Month, SUM(TotalAmount) as TotalSales
                    FROM Orders o
                    JOIN OrderDetails od ON o.OrderID = od.OrderID
                    WHERE od.CropID IN (
                        SELECT CropID FROM Crop WHERE FarmerID = ? AND Price > ?
                    )
                    GROUP BY Month
                    ORDER BY Month DESC
                    LIMIT 5
                """, (farmer_id, price))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[get_slaes_with_price_over_by_last_5_month_for_former] Error: {e}")
            return None
        
    def get_top_3_sales_products_with_price_by_farmer(self, farmer_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.Name, SUM(od.SubTotal) as TotalSales
                    FROM Crop c
                    JOIN OrderDetails od ON c.CropID = od.CropID
                    JOIN Orders o ON od.OrderID = o.OrderID
                    WHERE c.FarmerID = ?
                    GROUP BY c.Name
                    ORDER BY TotalSales DESC
                    LIMIT 3
                """, (farmer_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[get_top_3_sales_products_with_price_by_farmer] Error: {e}")
            return None
    
    def get_count_new_coustmers_by_month_for_former(self, farmer_id):
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT strftime('%Y-%m', OrderDate) as Month, COUNT(DISTINCT o.CustomerID) as NewCustomers
                    FROM Orders o
                    JOIN OrderDetails od ON o.OrderID = od.OrderID
                    WHERE od.CropID IN (
                        SELECT CropID FROM Crop WHERE FarmerID = ?
                    )
                    GROUP BY Month
                """, (farmer_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[get_count_new_coustmers_by_month_for_former] Error: {e}")
            return None

# Run this section only when executing directly
if __name__ == "__main__":
    db = FarmManagementDB()
    db.create_tables()
    print("Database and tables created successfully.")
    # Example usage