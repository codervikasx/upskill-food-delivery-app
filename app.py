from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from model import db, User, Restaurant, MenuItem, CartItem
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'upskill_internship_secret_key'

# Vercel-friendly Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))

# On Vercel, we MUST use /tmp for SQLite because it's the only writable directory
if os.environ.get('VERCEL'):
    db_path = '/tmp/food_delivery.db'
else:
    db_path = os.path.join(basedir, 'food_delivery.db')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Important for Vercel: Create tables on the first request if they don't exist
@app.before_request
def create_tables():
    # This ensures the database is initialized in the /tmp folder on the cloud
    if not os.path.exists(db_path) or os.environ.get('VERCEL'):
        db.create_all()

# --- AUTH & NAVIGATION ---
@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'restaurant':
            return redirect(url_for('dashboard'))
        return redirect(url_for('explore'))
    return render_template('register.html')

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login_page'))

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    
    if not email or not password:
        flash("Email and Password are required", "danger")
        return redirect(url_for('index'))

    if User.query.filter_by(email=email).first():
        flash("Email already registered!", "danger")
        return redirect(url_for('index'))
        
    hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(name=name, email=email, password_hash=hashed_pw, role=role)
    db.session.add(new_user)
    db.session.commit()
    flash("Registration successful! Please login.", "success")
    return redirect(url_for('login_page'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['role'] = user.role
        return redirect(url_for('dashboard') if user.role == 'restaurant' else url_for('explore'))
    flash("Invalid credentials", "danger")
    return redirect(url_for('login_page'))

# --- RESTAURANT DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != 'restaurant':
        return redirect(url_for('login_page'))
    user_id = session.get('user_id')
    restaurant = Restaurant.query.filter_by(user_id=user_id).first()
    if not restaurant:
        restaurant = Restaurant(user_id=user_id, restaurant_name=f"{session['user_name']}'s Kitchen", address="Default Address")
        db.session.add(restaurant)
        db.session.commit()
    items = MenuItem.query.filter_by(restaurant_id=restaurant.id).all()
    return render_template('dashboard.html', restaurant=restaurant, items=items)

@app.route('/add_item', methods=['POST'])
def add_item():
    if 'user_id' not in session or session.get('role') != 'restaurant':
        return redirect(url_for('login_page'))
    new_item = MenuItem(
        restaurant_id=request.form.get('restaurant_id'),
        dish_name=request.form.get('dish_name'),
        price=float(request.form.get('price')),
        description=request.form.get('description')
    )
    db.session.add(new_item)
    db.session.commit()
    flash("Item added to menu!", "success")
    return redirect(url_for('dashboard'))

# --- CUSTOMER FEATURES ---
@app.route('/explore')
def explore():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    restaurants = Restaurant.query.all()
    return render_template('customer_home.html', restaurants=restaurants)

@app.route('/restaurant/<int:restaurant_id>')
def view_menu(restaurant_id):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    items = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
    return render_template('restaurant_menu.html', restaurant=restaurant, items=items)

@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    user_id = session.get('user_id')
    item = MenuItem.query.get_or_404(item_id)
    cart_item = CartItem.query.filter_by(user_id=user_id, menu_item_id=item_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=user_id, menu_item_id=item_id, quantity=1)
        db.session.add(cart_item)
    db.session.commit()
    flash(f"Added {item.dish_name} to cart!", "success")
    return redirect(url_for('view_menu', restaurant_id=item.restaurant_id))

@app.route('/cart')
def view_cart():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    user_id = session.get('user_id')
    cart_data = db.session.query(CartItem, MenuItem).join(MenuItem).filter(CartItem.user_id == user_id).all()
    total = sum(item.price * cart.quantity for cart, item in cart_data)
    return render_template('cart.html', cart_data=cart_data, total=total)

# This is essential for Vercel to recognize the app
app = app

if __name__ == '__main__':
    app.run(debug=True)
