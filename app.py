from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import qrcode
import io
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Email configuration
EMAIL_USER = 'jmanishkumar.2003@gmail.com'
EMAIL_PASS = 'xhmq lbjb lobi eyqd'.replace(' ', '')  # Remove spaces from app password
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587

# Admin credentials
ADMIN_EMAIL = 'admin@hopes.com'
ADMIN_PASSWORD = 'admin'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    registration_token = db.Column(db.String(100), unique=True, nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    feedback_submitted = db.Column(db.Boolean, default=False)
    feedback_submitted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<User {self.email}>'


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('feedbacks', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Feedback {self.id}>'


def generate_qr_code(url):
    """Generate QR code as base64 image"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str


def send_email(to_email, subject, html_body, qr_code_base64=None):
    """Send email with optional QR code as attachment"""
    try:
        # Use 'related' type to embed images inline
        msg = MIMEMultipart('related')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = to_email

        # Create HTML email with QR code
        if qr_code_base64:
            # Decode base64 to get image bytes
            qr_image_bytes = base64.b64decode(qr_code_base64)
            
            # Use base64 data URI for better email client compatibility
            # This works in most email clients including Gmail
            qr_data_uri = f"data:image/png;base64,{qr_code_base64}"
            
            # Replace QR code placeholder with embedded image and download option
            # Handle both {{QR_CODE}} and {QR_CODE} patterns
            qr_image_html = f'''
                <div style="text-align: center; margin: 20px 0;">
                    <img src="{qr_data_uri}" alt="QR Code" style="max-width: 280px; border: 4px solid white; padding: 15px; background: white; border-radius: 12px; display: block; margin: 0 auto; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
                    <div style="margin-top: 20px;">
                        <div style="display: inline-block; background: white; color: #667eea; padding: 10px 20px; border-radius: 6px; font-weight: 600; font-size: 14px; border: 2px solid white; margin-top: 10px;">
                            📥 Download QR Code (Check Attachments)
                        </div>
                        <p style="margin-top: 15px; color: rgba(255,255,255,0.9); font-size: 13px;">The QR code image "feedback-qr-code.png" is attached to this email for easy download</p>
                    </div>
                </div>
            '''
            
            # Replace the placeholder
            if '{{QR_CODE}}' in html_body:
                html_content = html_body.replace('{{QR_CODE}}', qr_image_html)
                print("✓ Replaced {{QR_CODE}} placeholder")
            elif '{QR_CODE}' in html_body:
                html_content = html_body.replace('{QR_CODE}', qr_image_html)
                print("✓ Replaced {QR_CODE} placeholder")
            else:
                html_content = html_body
                print("⚠ Warning: QR_CODE placeholder not found in email body")
            
            # Also attach as downloadable attachment
            qr_attachment = MIMEImage(qr_image_bytes)
            qr_attachment.add_header('Content-Disposition', 'attachment; filename="feedback-qr-code.png"')
            msg.attach(qr_attachment)
        else:
            html_content = html_body

        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        print(f"\n{'='*60}")
        print(f"Attempting to send email to {to_email}...")
        print(f"From: {EMAIL_USER}")
        print(f"Connecting to {EMAIL_HOST}:{EMAIL_PORT}...")
        
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=30) as server:
            print("✓ Connected to SMTP server")
            server.starttls()
            print("✓ TLS encryption started")
            print("Attempting login...")
            server.login(EMAIL_USER, EMAIL_PASS)
            print("✓ Login successful")
            print("Sending email message...")
            server.send_message(msg)
            print(f"✓ Email sent successfully to {to_email}")
            print(f"{'='*60}\n")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ SMTP Authentication Error: {e}")
        print(f"Error Code: {e.smtp_code if hasattr(e, 'smtp_code') else 'N/A'}")
        print(f"Error Message: {e.smtp_error.decode() if hasattr(e, 'smtp_error') and e.smtp_error else str(e)}")
        print("\nPossible solutions:")
        print("1. Verify you're using an App Password (not your regular Gmail password)")
        print("2. If 2FA is enabled, generate a new App Password at:")
        print("   https://myaccount.google.com/apppasswords")
        print("3. Make sure the password has no spaces (16 characters)")
        print("4. If 2FA is disabled, try enabling 'Less secure app access'")
        print(f"{'='*60}\n")
        return False
    except smtplib.SMTPServerDisconnected as e:
        print(f"\n❌ SMTP Server Disconnected: {e}")
        print("The server closed the connection unexpectedly.")
        print("This might be due to network issues or server problems.")
        print(f"{'='*60}\n")
        return False
    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP Error: {e}")
        print(f"Error details: {type(e).__name__}")
        print(f"{'='*60}\n")
        return False
    except TimeoutError as e:
        print(f"\n❌ Connection Timeout: {e}")
        print("The server took too long to respond.")
        print("Check your internet connection and try again.")
        print(f"{'='*60}\n")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {type(e).__name__}: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        print(f"{'='*60}\n")
        return False


@app.route('/')
def index():
    return redirect(url_for('register'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        if not name or not email:
            return render_template('register.html', error='Please fill in all fields')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('register.html', error='Email already registered')
        
        # Create new user with unique token
        token = secrets.token_urlsafe(32)
        user = User(name=name, email=email, registration_token=token)
        db.session.add(user)
        db.session.commit()
        
        # Generate QR code URL
        feedback_url = url_for('feedback_form', token=token, _external=True)
        qr_code_base64 = generate_qr_code(feedback_url)
        
        # Send email with QR code
        email_subject = "Welcome! Your Feedback Form QR Code"
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px;">
                <!-- Header -->
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #4CAF50; margin: 0; font-size: 28px;">Welcome, {name}!</h1>
                    <p style="color: #666; margin-top: 10px; font-size: 16px;">Thank you for registering with us</p>
                </div>
                
                <!-- Introduction -->
                <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
                    <p style="margin: 0; color: #333; font-size: 15px;">
                        We're excited to have you on board! Your feedback is valuable to us and helps us improve our services. 
                        Below you'll find your personalized QR code that will take you directly to your feedback form.
                    </p>
                </div>
                
                <!-- QR Code Section -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px; margin: 30px 0;">
                    <h3 style="color: white; text-align: center; margin: 0 0 20px 0; font-size: 20px;">Scan to Access Your Feedback Form</h3>
                    <div style="text-align: center;">
                        {{QR_CODE}}
                    </div>
                </div>
                
                <!-- Instructions -->
                <div style="background-color: #fff9e6; padding: 20px; border-left: 4px solid #ff9800; border-radius: 4px; margin: 30px 0;">
                    <h4 style="margin: 0 0 10px 0; color: #333; font-size: 16px;">📱 How to Use:</h4>
                    <ul style="margin: 10px 0; padding-left: 20px; color: #555;">
                        <li style="margin-bottom: 8px;">Scan the QR code above with your smartphone camera</li>
                        <li style="margin-bottom: 8px;">Or click the direct link below to access your feedback form</li>
                        <li style="margin-bottom: 8px;">Share your thoughts and help us serve you better!</li>
                    </ul>
                </div>
                
                <!-- Direct Link -->
                <div style="text-align: center; margin: 30px 0;">
                    <p style="color: #666; margin-bottom: 15px;">Or click the link below:</p>
                    <a href="{feedback_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px;">Go to Feedback Form</a>
                </div>
                
                <!-- Footer -->
                <div style="border-top: 1px solid #e0e0e0; padding-top: 20px; margin-top: 30px; text-align: center;">
                    <p style="color: #999; font-size: 12px; margin: 5px 0;">This is an automated message. Please do not reply.</p>
                    <p style="color: #999; font-size: 12px; margin: 5px 0;">If you have any questions, please contact our support team.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        email_sent = send_email(email, email_subject, email_body, qr_code_base64)
        
        if not email_sent:
            print(f"Warning: Email failed to send to {email}, but user was registered successfully.")
        
        # Show success page with form
        return render_template('registration_success.html', 
                             name=name, 
                             email=email,
                             feedback_url=feedback_url,
                             qr_code_base64=qr_code_base64)
    
    return render_template('register.html')


@app.route('/feedback/<token>', methods=['GET', 'POST'])
def feedback_form(token):
    user = User.query.filter_by(registration_token=token).first()
    
    if not user:
        return render_template('error.html', message='Invalid or expired link')
    
    if request.method == 'POST':
        rating = request.form.get('rating')
        comments = request.form.get('comments', '')
        
        if not rating:
            return render_template('feedback_form.html', user=user, error='Please provide a rating')
        
        # Create feedback entry
        feedback = Feedback(user_id=user.id, rating=int(rating), comments=comments)
        db.session.add(feedback)
        
        # Update user status
        user.feedback_submitted = True
        user.feedback_submitted_at = datetime.utcnow()
        
        db.session.commit()
        
        return render_template('feedback_success.html', name=user.name)
    
    return render_template('feedback_form.html', user=user)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # Get statistics
    total_users = User.query.count()
    users_with_feedback = User.query.filter_by(feedback_submitted=True).count()
    users_without_feedback = total_users - users_with_feedback
    
    # Get all users with their feedback
    users = User.query.order_by(User.registered_at.desc()).all()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         users_with_feedback=users_with_feedback,
                         users_without_feedback=users_without_feedback,
                         users=users)


@app.route('/admin/add-user', methods=['POST'])
def add_user():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        
        if not name or not email:
            return jsonify({'error': 'Name and email are required'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        token = secrets.token_urlsafe(32)
        user = User(name=name, email=email, registration_token=token)
        db.session.add(user)
        db.session.commit()
        
        print(f"User created successfully: {name} ({email})")
        
        # Generate QR code and send email
        feedback_url = url_for('feedback_form', token=token, _external=True)
        qr_code_base64 = generate_qr_code(feedback_url)
        
        email_subject = "Welcome! Your Feedback Form QR Code"
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px;">
                <!-- Header -->
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #4CAF50; margin: 0; font-size: 28px;">Welcome, {name}!</h1>
                    <p style="color: #666; margin-top: 10px; font-size: 16px;">Thank you for registering with us</p>
                </div>
                
                <!-- Introduction -->
                <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
                    <p style="margin: 0; color: #333; font-size: 15px;">
                        We're excited to have you on board! Your feedback is valuable to us and helps us improve our services. 
                        Below you'll find your personalized QR code that will take you directly to your feedback form.
                    </p>
                </div>
                
                <!-- QR Code Section -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px; margin: 30px 0;">
                    <h3 style="color: white; text-align: center; margin: 0 0 20px 0; font-size: 20px;">Scan to Access Your Feedback Form</h3>
                    <div style="text-align: center;">
                        {{QR_CODE}}
                    </div>
                </div>
                
                <!-- Instructions -->
                <div style="background-color: #fff9e6; padding: 20px; border-left: 4px solid #ff9800; border-radius: 4px; margin: 30px 0;">
                    <h4 style="margin: 0 0 10px 0; color: #333; font-size: 16px;">📱 How to Use:</h4>
                    <ul style="margin: 10px 0; padding-left: 20px; color: #555;">
                        <li style="margin-bottom: 8px;">Scan the QR code above with your smartphone camera</li>
                        <li style="margin-bottom: 8px;">Or click the direct link below to access your feedback form</li>
                        <li style="margin-bottom: 8px;">Share your thoughts and help us serve you better!</li>
                    </ul>
                </div>
                
                <!-- Direct Link -->
                <div style="text-align: center; margin: 30px 0;">
                    <p style="color: #666; margin-bottom: 15px;">Or click the link below:</p>
                    <a href="{feedback_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px;">Go to Feedback Form</a>
                </div>
                
                <!-- Footer -->
                <div style="border-top: 1px solid #e0e0e0; padding-top: 20px; margin-top: 30px; text-align: center;">
                    <p style="color: #999; font-size: 12px; margin: 5px 0;">This is an automated message. Please do not reply.</p>
                    <p style="color: #999; font-size: 12px; margin: 5px 0;">If you have any questions, please contact our support team.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        email_sent = send_email(email, email_subject, email_body, qr_code_base64)
        
        if email_sent:
            return jsonify({'success': True, 'message': 'User added and email sent successfully'})
        else:
            return jsonify({'success': True, 'message': 'User added but email failed to send. Check server logs for details.'})
    except Exception as e:
        db.session.rollback()
        print(f"Error adding user: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to add user: {str(e)}'}), 500


@app.route('/admin/user/<int:user_id>/feedback')
def view_user_feedback(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    user = User.query.get_or_404(user_id)
    feedbacks = Feedback.query.filter_by(user_id=user_id).order_by(Feedback.submitted_at.desc()).all()
    
    return render_template('user_feedback.html', user=user, feedbacks=feedbacks)


@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_name = user.name
        user_email = user.email
        
        print(f"Attempting to delete user: {user_name} (ID: {user_id})")
        
        # Delete all feedback entries for this user first
        feedbacks = Feedback.query.filter_by(user_id=user_id).all()
        print(f"Found {len(feedbacks)} feedback entries to delete")
        
        for feedback in feedbacks:
            db.session.delete(feedback)
        
        # Then delete the user
        db.session.delete(user)
        db.session.commit()
        
        print(f"User {user_name} deleted successfully")
        return jsonify({'success': True, 'message': f'User {user_name} has been deleted successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to delete user: {str(e)}'}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)

