from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
import socket
import subprocess
import threading
import time
import requests
import os
import sys
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import db_manager
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = 'ToyCraft2024!DataViz#Analytics$SecureKey789'

# Email Configuration (Update these with your email settings)
EMAIL_CONFIG = {
    'SMTP_SERVER': 'smtp.gmail.com',  # For Gmail
    'SMTP_PORT': 587,
    'EMAIL': os.getenv('EMAIL_USER'),  # Loaded from environment
    'PASSWORD': os.getenv('EMAIL_PASS'),   # Loaded from environment
    'FROM_NAME': 'ToyCraft Tales'
}

# --- Login credentials (for demo) ---
ADMIN_USER = 'admin@example.com'
ADMIN_PASS = 'password123'
ADMIN_EMAIL = 'admin@example.com'

# Define static resource IDs for each course (for progress calculation)
DATA_ANALYTICS_RESOURCES = [
    'gfg',  # GeeksforGeeks
    'kaggle'  # Kaggle Learn
]
TABLEAU_RESOURCES = [
    'tableau'  # Tableau Official
]

# Course resource mapping for easy access
COURSE_RESOURCES = {
    'data_analytics': DATA_ANALYTICS_RESOURCES,
    'tableau': TABLEAU_RESOURCES
}

COURSE_CATALOG = [
    {
        'id': 'data_analytics',
        'name': 'Data Analytics and Visualizations',
        'image': '/static/img/Data Analytics and Visualizations.png',
        'description': 'Learn the essentials of Data Analytics and Data Visualization, including hands-on Tableau skills and practical analytics techniques.',
        'resources': [
            {
                'id': 'gfg',
                'title': 'GeeksforGeeks: Data Science & Analytics',
                'desc': 'Hundreds of free, well-structured tutorials on Data Analytics, Python, Pandas, and more. No login required.',
                'url': 'https://www.geeksforgeeks.org/data-science-tutorial/'
            },
            {
                'id': 'kaggle',
                'title': 'Kaggle Learn: Data Science Micro-courses',
                'desc': 'Free, interactive micro-courses on Python, Pandas, Data Visualization, and more. No login required to read lessons.',
                'url': 'https://www.kaggle.com/learn/overview'
            },
            {
                'id': 'tableau',
                'title': 'Tableau Official Free Training Videos',
                'desc': 'Official Tableau video tutorials. No certificate, but always free and up-to-date.',
                'url': 'https://www.tableau.com/learn/training/20211'
            }
        ]
    }
]

class NgrokManager:
    def __init__(self):
        self.tunnel_url = None
        self.tunnel_process = None
        self.ngrok_started = False
    
    def start_ngrok(self, port=5000):
        """Start ngrok tunnel"""
        try:
            print("🚀 Starting ngrok tunnel...")
            
            self.tunnel_process = subprocess.Popen(
                ['ngrok', 'http', str(port), '--log=stdout'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(4)
            
            try:
                response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
                if response.status_code == 200:
                    tunnels_data = response.json()
                    if tunnels_data.get('tunnels'):
                        for tunnel in tunnels_data['tunnels']:
                            if tunnel['proto'] == 'https':
                                self.tunnel_url = tunnel['public_url']
                                self.ngrok_started = True
                                return self.tunnel_url
                        
                        self.tunnel_url = tunnels_data['tunnels'][0]['public_url']
                        self.ngrok_started = True
                        return self.tunnel_url
                        
            except requests.exceptions.RequestException as e:
                print(f"❌ Error connecting to ngrok API: {e}")
                
        except FileNotFoundError:
            print("❌ ngrok not found! Please install ngrok first")
            return None
        except Exception as e:
            print(f"❌ Failed to start ngrok: {e}")
            return None
    
    def stop_tunnel(self):
        """Stop the ngrok tunnel"""
        if self.tunnel_process:
            try:
                self.tunnel_process.terminate()
                self.tunnel_process.wait(timeout=5)
                print("🛑 Ngrok tunnel stopped")
            except:
                self.tunnel_process.kill()

def get_local_ip():
    """Get the local IP address"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def test_database_connection():
    """Test database connection and display status"""
    try:
        count = db_manager.get_contact_count()
        print(f"✅ Database connected successfully! Current contacts: {count}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def validate_email(email):
    """Validate email format"""
    if not email or '@' not in email:
        return False, "Invalid email format"
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    return True, "Valid email"

def validate_phone(phone):
    """Validate 10-digit phone number"""
    if not phone:
        return False, "Phone number is required"
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    if len(digits_only) != 10:
        return False, "Phone number must be exactly 10 digits"
    
    # Check if it starts with valid digits (not 0 or 1)
    if digits_only[0] in ['0', '1']:
        return False, "Phone number cannot start with 0 or 1"
    
    return True, "Valid phone number"

def send_welcome_email(name, email):
    """Send welcome email to new contact"""
    try:
        if not all([EMAIL_CONFIG['EMAIL'], EMAIL_CONFIG['PASSWORD']]):
            print("⚠️ Email configuration not set up")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['FROM_NAME']} <{EMAIL_CONFIG['EMAIL']}>"
        msg['To'] = email
        msg['Subject'] = "🎉 Welcome to ToyCraft Tales Community!"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #667eea; margin-bottom: 10px;">🎯 Welcome to ToyCraft Tales!</h1>
                    <p style="font-size: 18px; color: #666;">Hi {name}! 👋</p>
                </div>
                
                <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 30px; border-radius: 15px; margin-bottom: 20px;">
                    <h2 style="color: #2d3748; margin-bottom: 15px;">✨ Thank you for joining us!</h2>
                    <p style="margin-bottom: 15px;">We're excited to have you as part of our ToyCraft Tales community. You'll now receive updates about:</p>
                    <ul style="margin-bottom: 20px;">
                        <li>🎨 Latest toy craft ideas and tutorials</li>
                        <li>📊 Interactive data visualizations and insights</li>
                        <li>🎪 Fun stories and creative content</li>
                        <li>🎁 Exclusive community benefits</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="font-size: 16px; color: #666;">
                        Stay tuned for amazing content and updates!<br>
                        <strong>The ToyCraft Tales Team</strong> 🚀
                    </p>
                </div>
                
                <div style="text-align: center; padding: 20px; background: #f8fafc; border-radius: 10px; margin-top: 20px;">
                    <p style="font-size: 14px; color: #999; margin: 0;">
                        This email was sent to {email}<br>
                        © 2025 ToyCraft Tales. All rights reserved.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT'])
        server.starttls()
        server.login(EMAIL_CONFIG['EMAIL'], EMAIL_CONFIG['PASSWORD'])
        server.send_message(msg)
        server.quit()
        
        print(f"📧 Welcome email sent to {email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email to {email}: {e}")
        return False

# Initialize ngrok manager
ngrok = NgrokManager()

def display_startup_info():
    """Display comprehensive startup information"""
    ip = get_local_ip()
    
    print("=" * 70)
    print("🎯 TOYCRAFT TALES DASHBOARD STARTING...")
    print("=" * 70)
    
    db_connected = test_database_connection()
    
    print(f"💻 Local Access:")
    print(f"   🏠 Homepage: http://127.0.0.1:5000")
    print(f"   📊 Dashboard: http://127.0.0.1:5000/dashboard")
    print(f"   📈 Charts: http://127.0.0.1:5000/charts")
    print(f"   📖 Story: http://127.0.0.1:5000/story")
    print(f"   📝 Admin: http://127.0.0.1:5000/contacts")
    
    print(f"\n📱 Network Access (Same WiFi):")
    print(f"   🌐 Homepage: http://{ip}:5000")
    print(f"   📊 Admin Panel: http://{ip}:5000/contacts")
    
    print(f"\n💾 Database Status:")
    print(f"   📊 PostgreSQL: {'✅ Connected' if db_connected else '❌ Disconnected'}")
    print(f"   📝 Contact Count: {db_manager.get_contact_count() if db_connected else 'N/A'}")
    
    print(f"\n📧 Email Status:")
    email_configured = bool(EMAIL_CONFIG['EMAIL'] and EMAIL_CONFIG['PASSWORD'])
    print(f"   📧 Configuration: {'✅ Ready' if email_configured else '❌ Not configured'}")
    if not email_configured:
        print(f"   ⚠️  Update EMAIL_CONFIG in app.py to enable email features")
    
    print("=" * 70)

@app.route('/', methods=['GET', 'POST'])
def index():
    user_email = session.get('user_email')
    is_community_member = False
    if user_email:
        contacts = db_manager.get_all_contacts()
        for contact in contacts:
            if contact.email and contact.email.lower() == user_email:
                is_community_member = True
                break
    
    # If already logged in or skipped, always show main homepage content
    if session.get('logged_in') or session.get('skipped'):
        show_course_banner = False
        if user_email and db_manager.get_user_by_email(user_email):
            # Show banner only if community member and not enrolled
            if is_community_member and not db_manager.is_user_enrolled(user_email):
                show_course_banner = True
        return render_template('index.html', show_auth=False, show_course_banner=show_course_banner, is_community_member=is_community_member)
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        
        if form_type == 'login':
            if db_manager.check_user_credentials(email, password):
                session['logged_in'] = True
                session['user_email'] = email
                session.pop('skipped', None)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid email or password. Please try again.', 'error')
        elif form_type == 'signup':
            if db_manager.get_user_by_email(email):
                flash('Email already registered. Please log in.', 'error')
            else:
                if len(password) < 6:
                    flash('Password must be at least 6 characters.', 'error')
                else:
                    db_manager.add_user(email, password)
                    session['logged_in'] = True
                    session['user_email'] = email
                    session.pop('skipped', None)
                    flash('Signup successful! You are now logged in.', 'success')
                    return redirect(url_for('index'))
    
    # Only show auth card if not logged in and not skipped
    return render_template('index.html', show_auth=True, show_course_banner=False, is_community_member=is_community_member)

@app.route('/skip')
def skip():
    session['skipped'] = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    """Handle contact form submission with enhanced validation"""
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        
        # Validate all fields are present
        if not name or not email or not phone:
            flash('All fields are required!', 'error')
            return redirect(url_for('index'))
        
        # Validate name
        if len(name) < 2:
            flash('Name must be at least 2 characters long!', 'error')
            return redirect(url_for('index'))
        
        if len(name) > 50:
            flash('Name cannot exceed 50 characters!', 'error')
            return redirect(url_for('index'))
        
        # Validate email format
        email_valid, email_message = validate_email(email)
        if not email_valid:
            flash(f'Email validation failed: {email_message}', 'error')
            return redirect(url_for('index'))
        
        # Validate phone
        phone_valid, phone_message = validate_phone(phone)
        if not phone_valid:
            flash(f'Phone validation failed: {phone_message}', 'error')
            return redirect(url_for('index'))
        
        # Clean phone number (keep only digits)
        phone_clean = re.sub(r'\D', '', phone)
        
        # Check if email already exists - FIXED VERSION
        try:
            existing_contacts = db_manager.get_all_contacts()
            for contact in existing_contacts:
                # Now contact is a Contact object, so we can use .email
                if contact.email and contact.email.lower() == email.lower():
                    flash(f'Welcome back {name}! This email is already registered with us.', 'success')
                    return redirect(url_for('index'))
        except Exception as e:
            print(f"⚠️ Warning: Could not check for existing contacts: {e}")
            # Continue with registration even if we can't check for duplicates
        
        # Get additional info
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Add contact to database
        success = db_manager.add_contact(
            name=name,
            email=email,
            phone=phone_clean,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if success:
            # Send welcome email
            email_sent = send_welcome_email(name, email)
            
            if email_sent:
                flash(f'🎉 Welcome {name}! Your details have been submitted successfully and a welcome email has been sent to {email}.', 'success')
            else:
                flash(f'✅ Thank you {name}! Your details have been submitted successfully.', 'success')
            
            print(f"📝 New contact added: {name} ({email}) - Phone: {phone_clean}")
        else:
            flash('Sorry, there was a database error. Please try again.', 'error')
            
    except Exception as e:
        print(f"❌ Error in submit_contact: {e}")
        flash('An unexpected error occurred. Please try again later.', 'error')
    
    return redirect(url_for('index'))

@app.route('/contacts')
def view_contacts():
    """View all contacts (admin page)"""
    # Only allow admin user
    if session.get('user_email') != ADMIN_EMAIL:
        flash('You are not authorized to access the admin page.', 'error')
        return redirect(url_for('index'))
    try:
        contacts = db_manager.get_all_contacts()
        return render_template('admin_contacts.html', contacts=contacts)
    except Exception as e:
        print(f"❌ Error fetching contacts: {e}")
        flash('Error loading contacts', 'error')
        return redirect(url_for('index'))

@app.route('/send-bulk-email', methods=['POST'])
def send_bulk_email():
    """Send bulk email to all contacts"""
    try:
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        if not subject or not message:
            flash('Subject and message are required!', 'error')
            return redirect(url_for('view_contacts'))
        
        contacts = db_manager.get_all_contacts()
        sent_count = 0
        failed_count = 0
        
        for contact in contacts:
            try:
                # Now contact is a Contact object
                if not contact.email:
                    failed_count += 1
                    continue
                
                msg = MIMEMultipart()
                msg['From'] = f"{EMAIL_CONFIG['FROM_NAME']} <{EMAIL_CONFIG['EMAIL']}>"
                msg['To'] = contact.email
                msg['Subject'] = subject
                
                html_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #667eea;">🎯 ToyCraft Tales</h1>
                            <p style="font-size: 18px; color: #666;">Hi {contact.name}! 👋</p>
                        </div>
                        
                        <div style="background: #f8fafc; padding: 30px; border-radius: 15px; margin-bottom: 20px;">
                            {message.replace(chr(10), '<br>')}
                        </div>
                        
                        <div style="text-align: center; padding: 20px; background: #f8fafc; border-radius: 10px; margin-top: 20px;">
                            <p style="font-size: 14px; color: #999; margin: 0;">
                                © 2025 ToyCraft Tales. All rights reserved.
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(html_body, 'html'))
                
                server = smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT'])
                server.starttls()
                server.login(EMAIL_CONFIG['EMAIL'], EMAIL_CONFIG['PASSWORD'])
                server.send_message(msg)
                server.quit()
                
                sent_count += 1
                print(f"📧 Email sent to {contact.email}")
                
            except Exception as e:
                failed_count += 1
                print(f"❌ Failed to send email to {contact.email}: {e}")
        
        if sent_count > 0:
            flash(f'✅ Successfully sent {sent_count} emails! {failed_count} failed.', 'success')
        else:
            flash('❌ Failed to send any emails. Check your email configuration.', 'error')
            
    except Exception as e:
        print(f"❌ Error in bulk email: {e}")
        flash('Error sending bulk emails.', 'error')
    
    return redirect(url_for('view_contacts'))

@app.route('/api/contact-count')
def contact_count_api():
    """API endpoint to get contact count"""
    try:
        count = db_manager.get_contact_count()
        return jsonify({'count': count, 'status': 'success'})
    except Exception as e:
        print(f"❌ Error getting contact count: {e}")
        return jsonify({'count': 0, 'status': 'error'})

@app.route('/dashboard')
def dashboard():
    user_email = session.get('user_email')
    is_community_member = False
    if user_email:
        contacts = db_manager.get_all_contacts()
        for contact in contacts:
            if contact.email and contact.email.lower() == user_email:
                is_community_member = True
                break
    return render_template('dashboard.html', is_community_member=is_community_member)

@app.route('/test-email')
def test_email():
    success = send_welcome_email("Test User", "test@example.com")
    return f"Email test: {'Success' if success else 'Failed'}"

@app.route('/charts')
def charts():
    user_email = session.get('user_email')
    is_community_member = False
    if user_email:
        contacts = db_manager.get_all_contacts()
        for contact in contacts:
            if contact.email and contact.email.lower() == user_email:
                is_community_member = True
                break
    return render_template('charts.html', is_community_member=is_community_member)

@app.route('/story')
def story():
    user_email = session.get('user_email')
    is_community_member = False
    if user_email:
        contacts = db_manager.get_all_contacts()
        for contact in contacts:
            if contact.email and contact.email.lower() == user_email:
                is_community_member = True
                break
    return render_template('story.html', is_community_member=is_community_member)

@app.route('/status')
def status():
    """System status page"""
    try:
        db_status = "Connected" if test_database_connection() else "Disconnected"
        contact_count = db_manager.get_contact_count()
        
        status_info = {
            'database': db_status,
            'contacts': contact_count,
            'ngrok_url': ngrok.tunnel_url if ngrok.ngrok_started else 'Not started',
            'local_ip': get_local_ip(),
            'email_configured': bool(EMAIL_CONFIG['EMAIL'] and EMAIL_CONFIG['PASSWORD'])
        }
        
        return jsonify(status_info)
    except Exception as e:
        return jsonify({'error': str(e)})

def start_ngrok_tunnel():
    """Start ngrok tunnel in background"""
    tunnel_url = ngrok.start_ngrok(5000)
    if tunnel_url:
        print("=" * 70)
        print("🌐 NGROK TUNNEL ACTIVE!")
        print("=" * 70)
        print(f"🔗 Public URL: {tunnel_url}")
        print(f"📤 Share this URL with anyone worldwide!")
        print(f"📊 Admin Panel: {tunnel_url}/contacts")
        print("=" * 70)
    else:
        print("❌ Ngrok not available - only local access")

@app.route('/send-course-email')
def send_course_email():
    # Only admin can trigger this
    if session.get('user_email') != ADMIN_EMAIL:
        flash('You are not authorized to send course emails.', 'error')
        return redirect(url_for('index'))
    
    contacts = db_manager.get_all_contacts()
    sent_count = 0
    for contact in contacts:
        if not contact.email:
            continue
        
        enroll_link = url_for('enroll', email=contact.email, _external=True)
        subject = "🎓 New Learning Course Available!"
        html_body = f"""
        <html>
        <body style='font-family: Arial, sans-serif; background: #f8fafc; color: #333;'>
            <div style='max-width: 600px; margin: 0 auto; padding: 30px; background: #fff; border-radius: 12px; box-shadow: 0 2px 8px #e2e8f0;'>
                <h1 style='color: #667eea; text-align: center;'>🎓 New Learning Course!</h1>
                <p style='font-size: 18px; color: #666; text-align: center;'>Hi {contact.name or contact.email}! 👋</p>
                <div style='background: #e8f5e9; padding: 24px; border-radius: 10px; margin: 24px 0;'>
                    <h2 style='color: #2e7d32;'>Ready to learn something new?</h2>
                     <p>We are excited to announce a new learning course for our ToyCraft Tales community members. Click below to enroll and unlock exclusive content!</p>
                    <div style='text-align: center; margin: 30px 0;'>
                        <a href='{enroll_link}' style='display: inline-block; background: #43a047; color: #fff; padding: 16px 32px; border-radius: 8px; font-size: 1.2rem; text-decoration: none; font-weight: bold;'>Enroll Now</a>
                    </div>
                </div>
                <footer style='text-align: center; font-size: 13px; color: #999; margin-top: 30px;'>
                    This email was sent to {contact.email}<br>© 2025 ToyCraft Tales. All rights reserved.
                </footer>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['FROM_NAME']} <{EMAIL_CONFIG['EMAIL']}>"
        msg['To'] = contact.email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))
        
        try:
            server = smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT'])
            server.starttls()
            server.login(EMAIL_CONFIG['EMAIL'], EMAIL_CONFIG['PASSWORD'])
            server.send_message(msg)
            server.quit()
            sent_count += 1
        except Exception as e:
            print(f"❌ Failed to send course email to {contact.email}: {e}")
    
    flash(f'Course announcement sent to {sent_count} community members.', 'success')
    return redirect(url_for('index'))

@app.route('/enroll', methods=['GET', 'POST'])
def enroll():
    # If GET with email param, allow email-based enrollment
    email_param = request.args.get('email')
    if request.method == 'GET' and email_param:
        # If not logged in, prompt login
        if not session.get('logged_in') or session.get('user_email') != email_param:
            flash('Please log in with your community account to enroll.', 'info')
            return redirect(url_for('index'))
        
        user_email = session.get('user_email')
        contacts = db_manager.get_all_contacts()
        is_community_member = any(contact.email and contact.email.lower() == user_email for contact in contacts)
        
        if not is_community_member:
            flash('You must join the community to enroll.', 'error')
            return redirect(url_for('index'))
        
        if db_manager.is_user_enrolled(user_email):
            flash('You are already enrolled in the course.', 'info')
            return redirect(url_for('index'))
        
        db_manager.enroll_user(user_email)
        flash('You have successfully enrolled in the new learning course!', 'success')
        return redirect(url_for('course'))
    
    # POST from modal
    if not session.get('logged_in'):
        flash('You must be logged in to enroll.', 'error')
        return redirect(url_for('index'))
    
    user_email = session.get('user_email')
    contacts = db_manager.get_all_contacts()
    is_community_member = any(contact.email and contact.email.lower() == user_email for contact in contacts)
    
    if not is_community_member:
        flash('You must join the community to enroll.', 'error')
        return redirect(url_for('index'))
    
    if db_manager.is_user_enrolled(user_email):
        flash('You are already enrolled in the course.', 'info')
        return redirect(url_for('index'))
    
    db_manager.enroll_user(user_email)
    flash('You have successfully enrolled in the new learning course!', 'success')
    return redirect(url_for('course'))

@app.route('/course')
def course():
    user_email = session.get('user_email')
    is_community_member = False
    user_obj = {'name': None, 'email': user_email}
    
    contacts = db_manager.get_all_contacts()
    for contact in contacts:
        if contact.email and contact.email.lower() == user_email:
            is_community_member = True
            user_obj = {'name': contact.name, 'email': contact.email}
            break
    
    if not is_community_member:
        flash('You must join the community to access the course.', 'error')
        return render_template('course.html', is_community_member=is_community_member, user=user_obj)
    
    if not db_manager.is_user_enrolled(user_email):
        flash('You must enroll in the course to access it.', 'error')
        return render_template('course.html', is_community_member=is_community_member, user=user_obj)
    
    # Calculate progress for each course section
    analytics_progress = db_manager.get_course_progress_percentage(user_email, 'data_analytics', DATA_ANALYTICS_RESOURCES)
    tableau_progress = db_manager.get_course_progress_percentage(user_email, 'tableau', TABLEAU_RESOURCES)
    
    # Get user's total points for rewards banner
    total_points = db_manager.get_user_total_points(user_email)

    # Determine completion flags for banners
    opened_analytics = set(db_manager.get_course_progress(user_email, 'data_analytics'))
    data_analytics_completed = all(r in opened_analytics for r in DATA_ANALYTICS_RESOURCES)
    tableau_uploaded = bool(db_manager.get_user_tableau_uploads(user_email))
    course_completed = data_analytics_completed and tableau_uploaded

    return render_template(
        'course.html',
        is_community_member=is_community_member,
        user=user_obj,
        analytics_progress=analytics_progress,
        tableau_progress=tableau_progress,
        total_points=total_points,
        course_completed=course_completed,
        courses=COURSE_CATALOG
    )

@app.route('/data-analytics')
def data_analytics():
    user_email = session.get('user_email')
    is_community_member = False
    user_obj = {'name': None, 'email': user_email}
    
    contacts = db_manager.get_all_contacts()
    for contact in contacts:
        if contact.email and contact.email.lower() == user_email:
            is_community_member = True
            user_obj = {'name': contact.name, 'email': contact.email}
            break
    
    if not is_community_member:
        flash('You must join the community to access the course.', 'error')
        return render_template('data-analytics.html', is_community_member=is_community_member, user=user_obj)
    
    if not db_manager.is_user_enrolled(user_email):
        flash('You must enroll in the course to access it.', 'error')
        return render_template('data-analytics.html', is_community_member=is_community_member, user=user_obj)
    
    # Calculate progress for each course section
    analytics_progress = db_manager.get_course_progress_percentage(user_email, 'data_analytics', DATA_ANALYTICS_RESOURCES)
    tableau_progress = db_manager.get_course_progress_percentage(user_email, 'tableau', TABLEAU_RESOURCES)
    
    # Get user's total points for rewards banner
    total_points = db_manager.get_user_total_points(user_email)

    # Determine completion flags for banners
    opened_analytics = set(db_manager.get_course_progress(user_email, 'data_analytics'))
    data_analytics_completed = all(r in opened_analytics for r in DATA_ANALYTICS_RESOURCES)
    tableau_uploaded = bool(db_manager.get_user_tableau_uploads(user_email))
    course_completed = data_analytics_completed and tableau_uploaded

    return render_template(
        'data-analytics.html',
        is_community_member=is_community_member,
        user=user_obj,
        analytics_progress=analytics_progress,
        tableau_progress=tableau_progress,
        total_points=total_points,
        data_analytics_completed=data_analytics_completed,
        course_completed=course_completed
    )

@app.route('/api/mark-resource-opened', methods=['POST'])
def mark_resource_opened():
    try:
        data = request.get_json()
        course_id = data.get('course_id')
        resource_id = data.get('resource_id')
        user_email = session.get('user_email')
        
        if not course_id or not resource_id:
            return jsonify({'success': False, 'error': 'Missing course_id or resource_id'}), 400
        
        success = db_manager.mark_resource_opened(user_email, course_id, resource_id)
        return jsonify({'success': success})
    except Exception as e:
        print(f"❌ Error marking resource opened: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/course-progress', methods=['GET'])
def get_course_progress():
    try:
        course_id = request.args.get('course_id')
        user_email = session.get('user_email')
        
        if not course_id:
            return jsonify({'success': False, 'error': 'Missing course_id'}), 400
        
        opened_resources = db_manager.get_course_progress(user_email, course_id)
        return jsonify({'success': True, 'opened_resources': opened_resources})
    except Exception as e:
        print(f"❌ Error getting course progress: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/rewards')
def rewards():
    try:
        user_email = session.get('user_email')
        total_points = db_manager.get_user_total_points(user_email)
        tableau_uploads = db_manager.get_user_tableau_uploads(user_email)

        # Check for achievement unlocked (resource completion)
        achievement_message = session.pop('achievement_message', None)

        # Check for course completion
        course_completed = False
        course_completion_points = 0
        all_resources = ['gfg', 'kaggle', 'tableau']
        opened = set(db_manager.get_course_progress(user_email, 'data_analytics')) | set(db_manager.get_course_progress(user_email, 'tableau'))
        if all(r in opened for r in all_resources):
            course_completed = True
            course_completion_points = 50
            # Award points if not already awarded
            if not db_manager.has_user_reward(user_email, 'points', 50, 'Course completion: All resources'):
                db_manager.add_user_reward(user_email, 'points', 50, 'Course completion: All resources')
                total_points = db_manager.get_user_total_points(user_email)

        # Data Analytics milestone (including Tableau dashboard)
        data_analytics_resources = ['gfg', 'kaggle', 'tableau']
        data_analytics_completed = all(r in opened for r in data_analytics_resources)
        tableau_uploaded = bool(tableau_uploads)

        # Course completion requires all resources opened AND Tableau uploaded
        course_completed = data_analytics_completed and tableau_uploaded
        course_completion_points = 50 if course_completed else 0
        if course_completed:
            if not db_manager.has_user_reward(user_email, 'points', 50, 'Course completion: All resources'):
                db_manager.add_user_reward(user_email, 'points', 50, 'Course completion: All resources')
                total_points = db_manager.get_user_total_points(user_email)
        else:
            # If user was previously rewarded but now doesn't meet requirements (shouldn't happen), do not show the reward
            course_completion_points = 0

        return render_template('rewards.html',
                             total_points=total_points,
                             tableau_uploads=tableau_uploads,
                             achievement_message=achievement_message,
                             course_completed=course_completed,
                             course_completion_points=course_completion_points,
                             data_analytics_completed=data_analytics_completed)
    except Exception as e:
        print(f"❌ Error loading rewards page: {e}")
        flash('Error loading rewards page.', 'error')
        return redirect(url_for('course'))

@app.route('/upload-tableau', methods=['GET', 'POST'])
def upload_tableau():
    user_email = session.get('user_email')
    
    if request.method == 'POST':
        try:
            dashboard_title = request.form.get('dashboard_title', '').strip()
            dashboard_description = request.form.get('dashboard_description', '').strip()
            file_url = request.form.get('file_url', '').strip()  # For now, just a URL field
            
            if not all([dashboard_title, dashboard_description, file_url]):
                flash('All fields are required.', 'error')
            else:
                success = db_manager.upload_tableau_dashboard(user_email, dashboard_title, dashboard_description, file_url)
                if success:
                    flash('🎉 Dashboard uploaded successfully! You earned 25 points!', 'success')
                    return redirect(url_for('rewards'))
                else:
                    flash('You have already uploaded a dashboard for this course.', 'info')
        except Exception as e:
            print(f"❌ Error uploading tableau dashboard: {e}")
            flash('Error uploading dashboard. Please try again.', 'error')
    
    return render_template('upload_tableau.html')

@app.route('/profile')
def profile():
    """User profile page"""
    try:
        user_email = session.get('user_email')
        total_points = db_manager.get_user_total_points(user_email)
        level, level_description = db_manager.get_achievement_level(total_points)
        # Only show basic profile info
        return render_template('profile.html',
                             user=session,
                             total_points=total_points,
                             level=level,
                             level_description=level_description)
    except Exception as e:
        print(f"❌ Error loading profile: {e}")
        flash('Error loading profile.', 'error')
        return redirect(url_for('course'))

@app.route('/courses')
def courses_catalog():
    return render_template('courses.html', courses=COURSE_CATALOG)

@app.route('/course/<course_id>')
def course_detail(course_id):
    user_email = session.get('user_email')
    is_community_member = False
    user_obj = {'name': None, 'email': user_email}
    contacts = db_manager.get_all_contacts()
    for contact in contacts:
        if contact.email and contact.email.lower() == user_email:
            is_community_member = True
            user_obj = {'name': contact.name, 'email': contact.email}
            break
    if not is_community_member:
        flash('You must join the community to access the course.', 'error')
        return redirect(url_for('courses_catalog'))
    if not db_manager.is_user_enrolled(user_email):
        flash('You must enroll in the course to access it.', 'error')
        return redirect(url_for('courses_catalog'))
    course = next((c for c in COURSE_CATALOG if c['id'] == course_id), None)
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('courses_catalog'))
    # Progress and reward logic
    if course_id == 'data_analytics':
        analytics_progress = db_manager.get_course_progress_percentage(user_email, 'data_analytics', [r['id'] for r in course['resources']])
        tableau_progress = 0
    elif course_id == 'tableau':
        analytics_progress = 0
        tableau_progress = db_manager.get_course_progress_percentage(user_email, 'tableau', [r['id'] for r in course['resources']])
    else:
        analytics_progress = 0
        tableau_progress = 0
    total_points = db_manager.get_user_total_points(user_email)
    opened_analytics = set(db_manager.get_course_progress(user_email, 'data_analytics'))
    data_analytics_completed = all(r['id'] in opened_analytics for r in COURSE_CATALOG[0]['resources'])
    tableau_uploaded = bool(db_manager.get_user_tableau_uploads(user_email))
    course_completed = data_analytics_completed and tableau_uploaded
    return render_template(
        'course.html',
        is_community_member=is_community_member,
        user=user_obj,
        course=course,
        analytics_progress=analytics_progress,
        tableau_progress=tableau_progress,
        total_points=total_points,
        data_analytics_completed=data_analytics_completed,
        course_completed=course_completed
    )

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Initialize database first
    print("🔄 Initializing database...")
    db_success = db_manager.init_database()
    if db_success:
        print("✅ Database initialized successfully")
    else:
        print("⚠️ Database initialization had issues, but continuing...")
    
    # Display startup information
    display_startup_info()
    
    # Start ngrok tunnel
    try:
        start_ngrok_tunnel()
    except Exception as e:
        print(f"❌ Failed to start ngrok tunnel: {e}")
    
    # Start the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)