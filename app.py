import os
import random
import datetime
import smtplib
import ssl
from flask import Flask, render_template, request, redirect, url_for, flash, Response, session
from dotenv import load_dotenv
from database.db import init_db, mongo

from routes import auth_bp, shop_bp  # ✅ Direct import of blueprints

# Load environment variables
load_dotenv()

# App setup
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change_this_in_production')

# MongoDB setup
# app.config["MONGO_URI"] = "mongodb://localhost:27017/cyper"

app.config["MONGO_URI"] = os.environ.get(
    "MONGO_URI",
    "mongodb://localhost:27017/cyper"
)
# Flask-PyMongo requires a default database name when the URI does not
# include one.  The cluster connection string in .env currently lacks
# a database path, so mongo.db would be None until this is provided.
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME", "cyper")


init_db(app)

# Register blueprints (ONLY ONCE)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(shop_bp, url_prefix='/shop')

# ------------------- Context Processor -------------------
# Make user_name available to all templates automatically
@app.context_processor
def inject_user():
    return {'name': session.get('user_name', None)}

# ------------------- Helper Functions -------------------

def send_email(to_email, message_content):
    sender_email = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    subject = "SecureAuth Notification"
    message = f"Subject: {subject}\n\n{message_content}"

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, message)
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

def is_suspicious(email, ip):
    threshold = datetime.datetime.now() - datetime.timedelta(minutes=10)
    failures = mongo.db.login_attempts.count_documents({
        'email': email,
        'ip': ip,
        'success': False,
        'timestamp': {'$gte': threshold}
    })
    return failures >= 3

# ------------------- OTP Routes -------------------

@app.route('/')
def home():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        mongo.db.secureauth.delete_many({'email': email})  # Clean old OTPs

        otp = str(random.randint(100000, 999999))
        mongo.db.secureauth.insert_one({
            'name': name,
            'email': email,
            'otp': otp,
            'created_at': datetime.datetime.now()
        })

        send_email(email, f"Your OTP is: {otp}")
        flash('✅ OTP sent to your email. Please verify.', 'success')
        return redirect(url_for('verify'))

    return render_template('register.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        email = request.form['email']
        entered_otp = request.form['otp']
        ip = request.remote_addr

        if is_suspicious(email, ip):
            flash('⚠️ Too many failed attempts. Try later.', 'danger')
            send_email(os.getenv("ADMIN_EMAIL", "admin@example.com"),
                       f"Suspicious login attempt from {ip} for {email}")
            return redirect(url_for('verify'))

        user = mongo.db.secureauth.find_one({'email': email})
        if not user or user['otp'] != entered_otp or            (datetime.datetime.now() - user['created_at']).seconds > 300:
            mongo.db.login_attempts.insert_one({
                'email': email,
                'ip': ip,
                'timestamp': datetime.datetime.now(),
                'success': False
            })
            flash('❌ Invalid or expired OTP.', 'danger')
            return redirect(url_for('verify'))

        # Success
        mongo.db.login_attempts.insert_one({
            'email': email,
            'ip': ip,
            'timestamp': datetime.datetime.now(),
            'success': True
        })

        flash('✅ OTP Verified! Welcome.', 'success')
        return redirect(url_for('login_success', name=user['name']))

    return render_template('verify.html')

@app.route('/login-success')
def login_success():
    name = request.args.get('name', 'User')
    products = list(mongo.db.products.find())
    return render_template('home.html', name=name, products=products)


# ------------------- Run App -------------------

if __name__ == '__main__':
    app.run(debug=True)


# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 10000))
#     app.run(host="0.0.0.0", port=port)