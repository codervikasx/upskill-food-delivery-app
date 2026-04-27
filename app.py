from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from model import db, User, Restaurant, MenuItem  # Import our database models
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'upskill_internship_secret_key' # Required for session and flash messages

# 1. Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'food_delivery.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- HELPER FUNCTIONS ---
def is_logged_in():
    return 'user_id' in session

def get_role():
    return session.get('role')

# --- ROUTES ---

@app.route('/')
def index():
    if is_logged_in():
        if get_role() == 'restaurant':
            return redirect(url_for('dashboard'))
        return "<h1>Welcome Customer!</h1><p>Customer browsing features are coming in Week 4.</p><a href='/logout'>Logout</a>"
    return render_template('register.html')

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login_page'))

# --- AUTHENTICATION LOGIC ---

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

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
        # Store user info in session
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['role'] = user.role
        
        if user.role == 'restaurant':
            return redirect(url_for('dashboard'))
        return redirect(url_for('index'))
    
    flash("Invalid email or password", "danger")
    return redirect(url_for('login_page'))

# --- WEEK 3: RESTAURANT DASHBOARD LOGIC ---

@app.route('/dashboard')
def dashboard():
    if not is_logged_in() or get_role() != 'restaurant':
        flash("Access denied. Please login as a Restaurant Owner.", "danger")
        return redirect(url_for('login_page'))
    
    user_id = session.get('user_id')
    # Check if a restaurant profile exists for this user
    restaurant = Restaurant.query.filter_by(user_id=user_id).first()
    
    if not restaurant:
        # Create a default restaurant profile if it doesn't exist
        restaurant = Restaurant(
            user_id=user_id, 
            restaurant_name=f"{session['user_name']}'s Kitchen", 
            address="Set your address"
        )
        db.session.add(restaurant)
        db.session.commit()
    
    # Get all menu items for this restaurant
    items = MenuItem.query.filter_by(restaurant_id=restaurant.id).all()
    return render_template('dashboard.html', restaurant=restaurant, items=items)

@app.route('/add_item', methods=['POST'])
def add_item():
    if not is_logged_in() or get_role() != 'restaurant':
        return redirect(url_for('login_page'))
    
    dish_name = request.form.get('dish_name')
    price = request.form.get('price')
    description = request.form.get('description')
    restaurant_id = request.form.get('restaurant_id')
    
    new_item = MenuItem(
        restaurant_id=restaurant_id, 
        dish_name=dish_name, 
        price=float(price), 
        description=description
    )
    
    db.session.add(new_item)
    db.session.commit()
    
    flash(f"Added {dish_name} to your menu!", "success")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Ensures tables exist
    app.run(debug=True)