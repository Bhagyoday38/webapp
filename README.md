1. Environment & Dependencies
First, ensure your project environment is isolated and up to date with the new security libraries.

Activate your virtual environment: Ensure you are inside your (venv) before installing anything.

Install the updated requirements: Run pip install -r requirements.txt to install the new packages (Flask-Limiter, Flask-Talisman, SQLAlchemy-Utils, cryptography, and email-validator).

2. Secure Configuration (.env)
You must never hardcode sensitive keys in your Python files. Create a file named exactly .env in the root of your project directory (C:\code\sarwatma_flask\) and add the following configuration:

Code snippet
# Flask Settings
FLASK_APP=run.py
FLASK_DEBUG=False
FLASK_ENV=production

# Security Keys (Change these to long, random strings in production!)
SECRET_KEY=super-secret-flask-session-key-change-me
DB_ENCRYPTION_KEY=your-32-byte-secure-key-for-aes-encryption-exactly!

# Razorpay Credentials
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
SECRET_KEY: Secures your session cookies and CSRF tokens.

DB_ENCRYPTION_KEY: Must be exactly 32 bytes (32 characters) for the AES encryption to work on the donor emails and phone numbers.

Version Control: Ensure your .gitignore file includes .env so you do not accidentally push your passwords to GitHub.

3. Database Reset & Initialization
Because we altered the database schema to include AES encryption and the new donor_phone column, the old database structure is incompatible.

Delete the old database: Delete the instance/sarwatma.db file from your project folder.

Initialize the new setup: Run python run.py. The app will automatically create a fresh, encrypted database and generate the default admin@gmail.com account with the hashed password we configured.
