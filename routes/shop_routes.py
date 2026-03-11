from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.db import mongo
from bson.objectid import ObjectId
import datetime

shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/shop')
def shop():
    products = list(mongo.db.products.find())
    user_name = session.get('user_name', None)
    return render_template('home.html', products=products, name=user_name)

# Admin Upload Product
@shop_bp.route('/admin/products', methods=['GET', 'POST'])
def admin_products():
    if not session.get('admin'):
        return redirect(url_for('auth.admin_login'))

    if request.method == 'POST':
        name = request.form['name']
        price = int(request.form['price'])
        description = request.form['description']
        image_url = request.form['image_url']

        mongo.db.products.insert_one({
            'name': name,
            'price': price,
            'description': description,
            'image_url': image_url
        })
        flash('✅ Product added.', 'success')
        return redirect(url_for('shop.admin_products'))

    products = list(mongo.db.products.find())
    return render_template('admin_products.html', products=products)

@shop_bp.route('/admin/delete-product', methods=['POST'])
def delete_product():
    if not session.get('admin'):
        return redirect(url_for('auth.admin_login'))

    product_id = request.form.get('product_id')
    mongo.db.products.delete_one({'_id': ObjectId(product_id)})
    flash('🗑️ Product deleted.', 'info')
    return redirect(url_for('shop.admin_products'))

@shop_bp.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        flash('Please log in to add items to your cart.', 'warning')
        return redirect(url_for('auth.login'))

    product_id = request.form.get('product_id')
    product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('shop.shop'))

    cart = session.get('cart', [])
    found = False
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += 1
            found = True
            break
    if not found:
        cart.append({
            'product_id': product_id,
            'name': product['name'],
            'price': product['price'],
            'image_url': product.get('image_url', ''),
            'quantity': 1
        })
    session['cart'] = cart
    flash('Added to cart!', 'success')
    return redirect(url_for('shop.shop'))

@shop_bp.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Please log in to view your cart.', 'warning')
        return redirect(url_for('auth.login'))
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart=cart_items, total=total, name=session.get('user_name'))

@shop_bp.route('/update-cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        flash('Please log in to update your cart.', 'warning')
        return redirect(url_for('auth.login'))
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', [])
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] = max(1, quantity)
            break
    session['cart'] = cart
    flash('Cart updated.', 'success')
    return redirect(url_for('shop.cart'))

@shop_bp.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        flash('Please log in to update your cart.', 'warning')
        return redirect(url_for('auth.login'))
    product_id = request.form.get('product_id')
    cart = session.get('cart', [])
    cart = [item for item in cart if item['product_id'] != product_id]
    session['cart'] = cart
    flash('Item removed from cart.', 'info')
    return redirect(url_for('shop.cart'))

@shop_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        email = request.form['email']
        phone = request.form['phone']

        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'name': name,
                'address': address,
                'email': email,
                'phone': phone
            }}
        )
        session['user_name'] = name  # Update session as well
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('shop.profile'))

    # Fetch user's order history
    orders = list(mongo.db.orders.find({'user_id': user_id}).sort('created_at', -1))
    return render_template('profile.html', user=user, orders=orders, name=session.get('user_name'))

@shop_bp.route('/orders')
def orders_history():
    if 'user_id' not in session:
        flash('Please log in to view your orders.', 'warning')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    orders = list(mongo.db.orders.find({'user_id': user_id}).sort('created_at', -1))
    return render_template('orders.html', orders=orders, name=session.get('user_name'))

@shop_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Please log in to checkout.', 'warning')
        return redirect(url_for('auth.login'))
    cart = session.get('cart', [])
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('shop.cart'))
    total = sum(item['price'] * item['quantity'] for item in cart)
    if request.method == 'POST':
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        zip_code = request.form['zip']
        phone = request.form['phone']
        
        # Store order in orders collection
        order_doc = {
            'user_id': session['user_id'],
            'user_name': session.get('user_name', 'User'),
            'products': cart,
            'total': total,
            'address': address,
            'city': city,
            'state': state,
            'zip': zip_code,
            'phone': phone,
            'status': 'Placed',
            'created_at': datetime.datetime.now()
        }
        result = mongo.db.orders.insert_one(order_doc)
        order_id = result.inserted_id
        
        # Update user's address in database
        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'address': address, 'phone': phone, 'city': city, 'state': state, 'zip': zip_code}}
        )
        
        session['cart'] = []  # Clear cart
        flash('Order placed successfully!', 'success')
        
        # Pass the created order to template
        return render_template('order_summary.html', order=order_doc, name=session.get('user_name'))
    return render_template('checkout.html', cart=cart, total=total, name=session.get('user_name'))

@shop_bp.route('/signout')
def signout():
    session.clear()
    flash('👋 You have been signed out.', 'info')
    return redirect(url_for('shop.shop'))

@shop_bp.route('/search', methods=['GET', 'POST'])
def search():
    query = request.form.get('query', '').strip() if request.method == 'POST' else request.args.get('query', '').strip()
    
    if not query:
        flash('Please enter a search term.', 'warning')
        return redirect(url_for('shop.shop'))
    
    # Search products by name or description using regex for case-insensitive search
    import re
    search_pattern = re.compile(query, re.IGNORECASE)
    
    products = list(mongo.db.products.find({
        '$or': [
            {'name': search_pattern},
            {'description': search_pattern}
        ]
    }))
    
    if not products:
        flash(f'No products found matching "{query}".', 'info')
    
    return render_template('search_results.html', 
                         products=products, 
                         query=query, 
                         name=session.get('user_name'),
                         result_count=len(products))
