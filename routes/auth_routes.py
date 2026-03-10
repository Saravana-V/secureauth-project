from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.db import users_collection
from bson.objectid import ObjectId
from flask import Blueprint, render_template, request, redirect, session, url_for

# auth = Blueprint('auth', __name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        user = users_collection.find_one({'email': email})
        if user:
            flash('User already exists.', 'danger')
            return redirect(url_for('auth.register'))
        users_collection.insert_one({'name': name, 'email': email})
        flash('Registration successful! Login now.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user = users_collection.find_one({'email': email})
        if user:
            # Generate OTP
            import random, datetime
            from database.db import mongo
            otp = str(random.randint(100000, 999999))
            mongo.db.secureauth.delete_many({'email': email})  # Clean old OTPs
            mongo.db.secureauth.insert_one({
                'name': user.get('name', ''),
                'email': email,
                'otp': otp,
                'created_at': datetime.datetime.now()
            })
            from app import send_email
            send_email(email, f"Your OTP is: {otp}")
            flash('✅ OTP sent to your email. Please verify.', 'success')
            session['login_email'] = email
            return redirect(url_for('auth.verify'))
        flash('User not found. Please register.', 'warning')
        return render_template('login.html')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.register'))

@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        email = request.form.get('email') or session.get('login_email')
        entered_otp = request.form['otp']
        from database.db import mongo
        import datetime
        user = mongo.db.secureauth.find_one({'email': email})
        if user and user['otp'] == entered_otp and (datetime.datetime.now() - user['created_at']).seconds <= 300:
            session['user_id'] = str(user.get('_id', ''))
            session['user_name'] = user.get('name', '')
            flash('✅ OTP Verified! Welcome.', 'success')
            return redirect(url_for('shop.shop'))
        else:
            flash('❌ Invalid or expired OTP.', 'danger')
            return render_template('verify.html')
    return render_template('verify.html')

# ✅ Fix for admin login route (previously missing)
@auth_bp.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            flash('Admin logged in successfully!', 'success')
            return redirect(url_for('shop.admin_products'))
        flash('Invalid admin credentials.', 'danger')
        return render_template('admin_login.html')
    return render_template('admin_login.html')



