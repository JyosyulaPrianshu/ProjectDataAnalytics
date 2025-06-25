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
        """Initialize database tables"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            
            # Create contacts table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20),
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create login table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS login (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create enrollments table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id SERIAL PRIMARY KEY,
                contact_email VARCHAR(255) NOT NULL,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create course_progress table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_progress (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                course_id VARCHAR(100) NOT NULL,
                resource_id VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_email, course_id, resource_id)
            )
            ''')
            
            # Create quizzes table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS quizzes (
                id SERIAL PRIMARY KEY,
                course_id VARCHAR(100) NOT NULL,
                resource_id VARCHAR(100) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                questions JSONB NOT NULL,
                passing_score INTEGER DEFAULT 70,
                points_reward INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create quiz_attempts table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                quiz_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                answers JSONB NOT NULL,
                passed BOOLEAN NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
            )
            ''')
            
            # Create user_rewards table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_rewards (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                reward_type VARCHAR(50) NOT NULL,
                reward_value INTEGER NOT NULL,
                description TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create tableau_uploads table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tableau_uploads (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                course_id VARCHAR(100) NOT NULL,
                dashboard_title VARCHAR(255) NOT NULL,
                dashboard_description TEXT,
                file_url TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            connection.commit()
            print("✅ Database tables initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            return False
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

    def get_course_progress_percentage(self, user_email, course_id, all_resource_ids):
        """
        Returns the percentage of resources opened by the user for a given course.
        all_resource_ids: list of all resource_ids for the course (from static definition)
        """
        if not all_resource_ids:
            return 0
        opened = set(self.get_course_progress(user_email, course_id))
        total = len(all_resource_ids)
        completed = len([rid for rid in all_resource_ids if rid in opened])
        return int((completed / total) * 100) if total > 0 else 0

    def add_quiz(self, course_id, resource_id, title, description, questions, passing_score=70, points_reward=10):
        """Add a new quiz for a course resource"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            insert_query = '''
            INSERT INTO quizzes (course_id, resource_id, title, description, questions, passing_score, points_reward)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(insert_query, (course_id, resource_id, title, description, questions, passing_score, points_reward))
            connection.commit()
            return True
        except Exception as e:
            print(f"❌ Error adding quiz: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_quiz_by_resource(self, course_id, resource_id):
        """Get quiz for a specific resource"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return None
            cursor = connection.cursor(cursor_factory=extras.DictCursor)
            cursor.execute("SELECT * FROM quizzes WHERE course_id = %s AND resource_id = %s", (course_id, resource_id))
            quiz = cursor.fetchone()
            return dict(quiz) if quiz else None
        except Exception as e:
            print(f"❌ Error fetching quiz: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def save_quiz_attempt(self, user_email, quiz_id, score, answers, passed):
        """Save a quiz attempt"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            insert_query = '''
            INSERT INTO quiz_attempts (user_email, quiz_id, score, answers, passed)
            VALUES (%s, %s, %s, %s, %s)
            '''
            cursor.execute(insert_query, (user_email, quiz_id, score, answers, passed))
            connection.commit()
            return True
        except Exception as e:
            print(f"❌ Error saving quiz attempt: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def add_user_reward(self, user_email, reward_type, reward_value, description):
        """Add a reward for a user"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            insert_query = '''
            INSERT INTO user_rewards (user_email, reward_type, reward_value, description)
            VALUES (%s, %s, %s, %s)
            '''
            cursor.execute(insert_query, (user_email, reward_type, reward_value, description))
            connection.commit()
            return True
        except Exception as e:
            print(f"❌ Error adding user reward: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_user_total_points(self, user_email):
        """Get total points earned by a user"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return 0
            cursor = connection.cursor()
            cursor.execute("SELECT SUM(reward_value) FROM user_rewards WHERE user_email = %s AND reward_type = 'points'", (user_email,))
            result = cursor.fetchone()
            return result[0] if result[0] else 0
        except Exception as e:
            print(f"❌ Error getting user points: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_leaderboard(self, limit=10):
        """Get leaderboard of top users by points"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return []
            cursor = connection.cursor(cursor_factory=extras.DictCursor)
            cursor.execute('''
            SELECT user_email, SUM(reward_value) as total_points, COUNT(*) as rewards_count
            FROM user_rewards 
            WHERE reward_type = 'points'
            GROUP BY user_email 
            ORDER BY total_points DESC 
            LIMIT %s
            ''', (limit,))
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ Error fetching leaderboard: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_achievement_level(self, total_points):
        """Get achievement level based on total points"""
        if total_points >= 100:
            return "Master", "🎓 Master Level - You've mastered the fundamentals!"
        elif total_points >= 75:
            return "Advanced", "🚀 Advanced Level - You're doing amazing!"
        elif total_points >= 50:
            return "Intermediate", "⭐ Intermediate Level - Great progress!"
        elif total_points >= 25:
            return "Beginner", "🌱 Beginner Level - Keep learning!"
        else:
            return "Newcomer", "👋 Newcomer - Welcome to your learning journey!"

    def upload_tableau_dashboard(self, user_email, dashboard_title, dashboard_description, file_url):
        """Upload a Tableau dashboard for review and points"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            
            # Check if user has already uploaded for this course
            cursor.execute("SELECT id FROM tableau_uploads WHERE user_email = %s AND course_id = 'tableau'", (user_email,))
            if cursor.fetchone():
                return False  # Already uploaded
            
            insert_query = '''
            INSERT INTO tableau_uploads (user_email, course_id, dashboard_title, dashboard_description, file_url)
            VALUES (%s, %s, %s, %s, %s)
            '''
            cursor.execute(insert_query, (user_email, 'tableau', dashboard_title, dashboard_description, file_url))
            connection.commit()
            
            # Award points for dashboard upload
            self.add_user_reward(user_email, 'points', 25, f"Tableau dashboard upload: {dashboard_title}")
            
            return True
        except Exception as e:
            print(f"❌ Error uploading tableau dashboard: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_user_tableau_uploads(self, user_email):
        """Get user's tableau dashboard uploads"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return []
            cursor = connection.cursor(cursor_factory=extras.DictCursor)
            cursor.execute("SELECT * FROM tableau_uploads WHERE user_email = %s ORDER BY uploaded_at DESC", (user_email,))
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ Error fetching tableau uploads: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_quiz_by_id(self, quiz_id):
        """Get quiz by ID"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return None
            cursor = connection.cursor(cursor_factory=extras.DictCursor)
            cursor.execute("SELECT * FROM quizzes WHERE id = %s", (quiz_id,))
            quiz = cursor.fetchone()
            return dict(quiz) if quiz else None
        except Exception as e:
            print(f"❌ Error fetching quiz by ID: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def is_course_completed(self, user_email, course_id):
        """Check if user has completed all resources and quizzes for a course"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            
            # Get all resources for the course
            if course_id == 'data_analytics':
                total_resources = ['gfg', 'kaggle']
            elif course_id == 'tableau':
                total_resources = ['tableau']
            else:
                return False
            
            # Check if all resources are opened
            for resource_id in total_resources:
                cursor.execute("SELECT id FROM course_progress WHERE user_email = %s AND course_id = %s AND resource_id = %s", 
                             (user_email, course_id, resource_id))
                if not cursor.fetchone():
                    return False
            
            # Check if all quizzes are passed
            cursor.execute("""
                SELECT q.id FROM quizzes q 
                LEFT JOIN quiz_attempts qa ON q.id = qa.quiz_id AND qa.user_email = %s AND qa.passed = true
                WHERE q.course_id = %s AND qa.id IS NULL
            """, (user_email, course_id))
            
            if cursor.fetchone():
                return False  # At least one quiz not passed
            
            return True
        except Exception as e:
            print(f"❌ Error checking course completion: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

# Initialize database manager
db_manager = DatabaseManager()
