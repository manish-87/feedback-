# Deployment Guide for Feedback App

This guide will help you deploy your Flask feedback app to various hosting platforms.

## Option 1: Render (Recommended - Free & Easy)

### Steps:
1. **Create a Render account** at https://render.com
2. **Connect your GitHub repository** (or push code to GitHub first)
3. **Create a New Web Service**:
   - Connect your repository
   - Name: `feedback-app` (or any name)
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Plan: Free

4. **Add Environment Variables** (if needed):
   - `PYTHON_VERSION`: `3.11`
   
5. **Update requirements.txt** to include gunicorn:
   ```
   Flask==3.0.0
   Flask-SQLAlchemy==3.1.1
   qrcode[pil]==7.4.2
   Werkzeug==3.0.1
   gunicorn==21.2.0
   ```

6. **Important Notes**:
   - Render uses ephemeral file systems, so your SQLite database will reset on each deploy
   - For production, consider using PostgreSQL (free on Render)
   - Update `app.py` to use environment variables for sensitive data

## Option 2: Railway

### Steps:
1. **Create account** at https://railway.app
2. **New Project** → **Deploy from GitHub repo**
3. **Add PostgreSQL** (optional but recommended)
4. Railway auto-detects Python and installs dependencies
5. Your app will be live at `your-app.railway.app`

## Option 3: Heroku

### Steps:
1. **Install Heroku CLI**: https://devcenter.heroku.com/articles/heroku-cli
2. **Login**: `heroku login`
3. **Create app**: `heroku create your-app-name`
4. **Create Procfile**:
   ```
   web: gunicorn app:app
   ```
5. **Deploy**: `git push heroku main`
6. **Add PostgreSQL** (optional): `heroku addons:create heroku-postgresql:mini`

## Option 4: PythonAnywhere (Free Tier Available)

### Steps:
1. **Sign up** at https://www.pythonanywhere.com
2. **Upload your files** via Files tab
3. **Create a new Web App**:
   - Choose Flask
   - Python 3.10
   - Point to your `app.py`
4. **Configure WSGI** file to import your app
5. **Reload** your web app

## Option 5: DigitalOcean App Platform

### Steps:
1. **Create account** at https://www.digitalocean.com
2. **Create App** → **Connect GitHub**
3. **Configure**:
   - Build: `pip install -r requirements.txt`
   - Run: `gunicorn app:app`
4. **Deploy**

## Important Configuration Changes for Production

### 1. Update app.py for production:

```python
import os

# Use environment variables for sensitive data
EMAIL_USER = os.getenv('EMAIL_USER', 'jmanishkumar.2003@gmail.com')
EMAIL_PASS = os.getenv('EMAIL_PASS', 'your-app-password')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@hopes.com')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')

# For production, use PostgreSQL
if os.getenv('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL').replace('postgres://', 'postgresql://')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback_app.db'

# Disable debug mode in production
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
```

### 2. Update requirements.txt:

Add gunicorn for production:
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
qrcode[pil]==7.4.2
Werkzeug==3.0.1
gunicorn==21.2.0
psycopg2-binary==2.9.9  # For PostgreSQL (optional)
```

### 3. Create Procfile (for Heroku/Render):

```
web: gunicorn app:app
```

### 4. Set Environment Variables:

- `EMAIL_USER`: Your Gmail address
- `EMAIL_PASS`: Your Gmail app password
- `ADMIN_EMAIL`: Admin email
- `ADMIN_PASSWORD`: Admin password
- `DATABASE_URL`: (If using PostgreSQL)

## Security Recommendations

1. **Never commit sensitive data** to Git
2. **Use environment variables** for all credentials
3. **Enable HTTPS** (most platforms do this automatically)
4. **Use strong admin passwords** in production
5. **Consider using PostgreSQL** instead of SQLite for production

## Testing After Deployment

1. Visit your deployed URL
2. Test user registration
3. Test admin login
4. Test email sending
5. Test feedback submission

## Need Help?

- Check platform-specific documentation
- Review error logs in your hosting platform
- Ensure all environment variables are set correctly
- Verify email credentials are working

