import mysql.connector
from mysql.connector import Error
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
from config import Config

class Contact:
    """Contact object to make database results more consistent"""
    def __init__(self, data):
        if isinstance(data, dict):
            self.id = data.get('id')
            self.name = data.get('name')
            self.email = data.get('email')
            self.phone = data.get('phone')
            self.created_at = data.get('created_at')
            self.ip_address = data.get('ip_address')
            self.user_agent = data.get('user_agent')
        else:
            # Handle tuple/list data from cursor
            self.id = data[0] if len(data) > 0 else None
            self.name = data[1] if len(data) > 1 else None
            self.email = data[2] if len(data) > 2 else None
            self.phone = data[3] if len(data) > 3 else None
            self.created_at = data[4] if len(data) > 4 else None
            self.ip_address = data[5] if len(data) > 5 else None
            self.user_agent = data[6] if len(data) > 6 else None

class DatabaseManager:
    def __init__(self):
        # Use environment variables or config.py for credentials
        self.config = {
            'host': Config.DB_HOST,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME,
            'port': Config.DB_PORT
        }
        
        # Debug: Print configuration (without password)
        print(f"🔧 Database Config:")
        print(f"   Host: {self.config['host']}")
        print(f"   User: {self.config['user']}")
        print(f"   Database: {self.config['database']}")
        print(f"   Port: {self.config['port']}")
        print(f"   Password: {'***' if self.config['password'] else 'NOT SET'}")
        
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        try:
            connection = mysql.connector.connect(**self.config)
            return connection
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            return None
    
    def init_database(self):
        """Initialize database and create tables"""
        connection = None
        cursor = None
        
        try:
            # First, connect without specifying database to create it
            temp_config = self.config.copy()
            temp_config.pop('database')
            
            print(f"🔗 Connecting to MySQL server...")
            connection = mysql.connector.connect(**temp_config)
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config['database']}")
            print(f"✅ Database '{self.config['database']}' created/verified")
            
            cursor.execute(f"USE {self.config['database']}")
            
            # Create contacts table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS contacts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                user_agent TEXT
            )
            """
            cursor.execute(create_table_query)
            
            # Create login table
            create_login_table_query = """
            CREATE TABLE IF NOT EXISTS login (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_login_table_query)
            
            # Create enrollments table
            create_enrollments_table_query = """
            CREATE TABLE IF NOT EXISTS enrollments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contact_email VARCHAR(255) NOT NULL,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_enrollments_table_query)
            
            # Create course_progress table
            create_progress_table_query = """
            CREATE TABLE IF NOT EXISTS course_progress (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                course_id VARCHAR(100) NOT NULL,
                resource_id VARCHAR(100) NOT NULL,
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_progress (user_email, course_id, resource_id)
            )
            """
            cursor.execute(create_progress_table_query)
            
            connection.commit()
            
            print("✅ Database and tables created successfully!")
            
        except Error as e:
            print(f"❌ Error initializing database: {e}")
            
            # Provide specific help for common errors
            if "Access denied" in str(e):
                print("💡 Fix suggestions:")
                print("   1. Check your MySQL password")
                print("   2. Make sure MySQL service is running")
                print("   3. Try: mysql -u root -p")
                print("   4. If password is wrong, reset it")
                
            elif "Can't connect to MySQL server" in str(e):
                print("💡 Fix suggestions:")
                print("   1. Start MySQL service")
                print("   2. Check if MySQL is running on port 3306")
                
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
    
    def add_contact(self, name, email, phone, ip_address=None, user_agent=None):
        """Add a new contact to the database"""
        connection = None
        cursor = None
        
        try:
            connection = self.get_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            insert_query = """
            INSERT INTO contacts (name, email, phone, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (name, email, phone, ip_address, user_agent))
            connection.commit()
            
            contact_id = cursor.lastrowid
            print(f"✅ Contact added successfully with ID: {contact_id}")
            return True
            
        except Error as e:
            print(f"❌ Error adding contact: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
    
    def get_all_contacts(self):
        """Get all contacts from database - returns Contact objects"""
        connection = None
        cursor = None
        
        try:
            connection = self.get_connection()
            if not connection:
                return []
                
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM contacts ORDER BY created_at DESC")
            results = cursor.fetchall()
            
            # Convert dictionary results to Contact objects
            contacts = [Contact(row) for row in results]
            return contacts
            
        except Error as e:
            print(f"❌ Error fetching contacts: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
    
    def get_contact_count(self):
        """Get total number of contacts"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return 0
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM contacts")
            result = cursor.fetchone()
            count = result[0] if result else 0
            return count
        except Error as e:
            print(f"❌ Error getting contact count: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    # --- User Authentication Methods ---
    def add_user(self, email, password):
        """Add a new user to the login table (with hashed password)"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            password_hash = generate_password_hash(password)
            insert_query = """
            INSERT INTO login (email, password_hash) VALUES (%s, %s)
            """
            cursor.execute(insert_query, (email, password_hash))
            connection.commit()
            print(f"✅ User registered: {email}")
            return True
        except Error as e:
            print(f"❌ Error adding user: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def get_user_by_email(self, email):
        """Get user row by email from login table"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return None
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM login WHERE email = %s", (email,))
            user = cursor.fetchone()
            return user
        except Error as e:
            print(f"❌ Error fetching user: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def check_user_credentials(self, email, password):
        """Check if email/password is valid (returns True/False)"""
        user = self.get_user_by_email(email)
        if not user or not isinstance(user, dict):
            return False
        if 'password_hash' in user and check_password_hash(user['password_hash'], password):
            return True
        return False

    def enroll_user(self, email):
        """Enroll a user in the course by email (if not already enrolled)"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            # Check if already enrolled
            cursor.execute("SELECT id FROM enrollments WHERE contact_email = %s", (email,))
            if cursor.fetchone():
                return True  # Already enrolled
            cursor.execute("INSERT INTO enrollments (contact_email) VALUES (%s)", (email,))
            connection.commit()
            print(f"✅ User enrolled: {email}")
            return True
        except Error as e:
            print(f"❌ Error enrolling user: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def is_user_enrolled(self, email):
        """Check if a user is enrolled in the course by email"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM enrollments WHERE contact_email = %s", (email,))
            return cursor.fetchone() is not None
        except Error as e:
            print(f"❌ Error checking enrollment: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def mark_resource_opened(self, user_email, course_id, resource_id):
        """Mark a resource as opened for a user in a course"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            insert_query = """
            INSERT IGNORE INTO course_progress (user_email, course_id, resource_id)
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (user_email, course_id, resource_id))
            connection.commit()
            return True
        except Error as e:
            print(f"❌ Error marking resource opened: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def get_course_progress(self, user_email, course_id):
        """Get list of opened resource_ids for a user and course"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return []
            cursor = connection.cursor()
            select_query = """
            SELECT resource_id FROM course_progress WHERE user_email = %s AND course_id = %s
            """
            cursor.execute(select_query, (user_email, course_id))
            results = cursor.fetchall()
            return [row[0] for row in results]
        except Error as e:
            print(f"❌ Error fetching course progress: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

# Initialize database manager
db_manager = DatabaseManager()