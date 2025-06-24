import psycopg2
from psycopg2 import sql, extras
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
            self.id = data[0] if len(data) > 0 else None
            self.name = data[1] if len(data) > 1 else None
            self.email = data[2] if len(data) > 2 else None
            self.phone = data[3] if len(data) > 3 else None
            self.created_at = data[4] if len(data) > 4 else None
            self.ip_address = data[5] if len(data) > 5 else None
            self.user_agent = data[6] if len(data) > 6 else None

class DatabaseManager:
    def __init__(self):
        self.config = {
            'host': Config.DB_HOST,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'dbname': Config.DB_NAME,
            'port': Config.DB_PORT
        }
        self.init_database()

    def get_connection(self):
        try:
            connection = psycopg2.connect(**self.config)
            return connection
        except Exception as e:
            print(f"❌ Error connecting to Postgres: {e}")
            return None

    def init_database(self):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return
            cursor = connection.cursor()
            # Create tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                user_agent TEXT
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS login (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id SERIAL PRIMARY KEY,
                contact_email VARCHAR(255) NOT NULL,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_progress (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                course_id VARCHAR(100) NOT NULL,
                resource_id VARCHAR(100) NOT NULL,
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_email, course_id, resource_id)
            )
            ''')
            connection.commit()
            print("✅ Database and tables created successfully!")
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def add_contact(self, name, email, phone, ip_address=None, user_agent=None):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            insert_query = '''
            INSERT INTO contacts (name, email, phone, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
            '''
            cursor.execute(insert_query, (name, email, phone, ip_address, user_agent))
            connection.commit()
            print(f"✅ Contact added successfully.")
            return True
        except Exception as e:
            print(f"❌ Error adding contact: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_all_contacts(self):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return []
            cursor = connection.cursor(cursor_factory=extras.DictCursor)
            cursor.execute("SELECT * FROM contacts ORDER BY created_at DESC")
            results = cursor.fetchall()
            contacts = [Contact(dict(row)) for row in results]
            return contacts
        except Exception as e:
            print(f"❌ Error fetching contacts: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_contact_count(self):
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
        except Exception as e:
            print(f"❌ Error getting contact count: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    # --- User Authentication Methods ---
    def add_user(self, email, password):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            password_hash = generate_password_hash(password)
            insert_query = '''
            INSERT INTO login (email, password_hash) VALUES (%s, %s)
            '''
            cursor.execute(insert_query, (email, password_hash))
            connection.commit()
            print(f"✅ User registered: {email}")
            return True
        except Exception as e:
            print(f"❌ Error adding user: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_user_by_email(self, email):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return None
            cursor = connection.cursor(cursor_factory=extras.DictCursor)
            cursor.execute("SELECT * FROM login WHERE email = %s", (email,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            print(f"❌ Error fetching user: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def check_user_credentials(self, email, password):
        user = self.get_user_by_email(email)
        if not user or not isinstance(user, dict):
            return False
        if 'password_hash' in user and check_password_hash(user['password_hash'], password):
            return True
        return False

    def enroll_user(self, email):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM enrollments WHERE contact_email = %s", (email,))
            if cursor.fetchone():
                return True  # Already enrolled
            cursor.execute("INSERT INTO enrollments (contact_email) VALUES (%s)", (email,))
            connection.commit()
            print(f"✅ User enrolled: {email}")
            return True
        except Exception as e:
            print(f"❌ Error enrolling user: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def is_user_enrolled(self, email):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM enrollments WHERE contact_email = %s", (email,))
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"❌ Error checking enrollment: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def mark_resource_opened(self, user_email, course_id, resource_id):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            insert_query = '''
            INSERT INTO course_progress (user_email, course_id, resource_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_email, course_id, resource_id) DO NOTHING
            '''
            cursor.execute(insert_query, (user_email, course_id, resource_id))
            connection.commit()
            return True
        except Exception as e:
            print(f"❌ Error marking resource opened: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_course_progress(self, user_email, course_id):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return []
            cursor = connection.cursor()
            select_query = '''
            SELECT resource_id FROM course_progress WHERE user_email = %s AND course_id = %s
            '''
            cursor.execute(select_query, (user_email, course_id))
            results = cursor.fetchall()
            return [row[0] for row in results]
        except Exception as e:
            print(f"❌ Error fetching course progress: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

# Initialize database manager
db_manager = DatabaseManager()
