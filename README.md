# Feedback App

A simple and elegant user registration flow that sends a confirmation email with a QR code for a feedback form. Includes an admin view to see registered users.

## Features

- User registration with name and email
- Automatic email sending with QR code for feedback form
- Feedback form accessible via QR code or direct link
- Admin dashboard to view registered users and their feedback
- Admin can add users and send them emails automatically

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access the application:
- Registration: http://localhost:5000/register
- Admin Login: http://localhost:5000/admin/login
  - Email: admin@hopes.com
  - Password: admin

## How It Works

1. **User Registration**: Users register with their name and email
2. **Email with QR Code**: Users receive an email containing a QR code that links to their feedback form
3. **Feedback Form**: Users can scan the QR code or click the link to submit feedback
4. **Admin Dashboard**: Admins can view all registered users, see who has submitted feedback, and add new users

## Email Configuration

The app uses Gmail SMTP to send emails. Email credentials are configured in `app.py`.

## Database

The app uses SQLite database (`feedback_app.db`) which is created automatically on first run.

