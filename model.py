from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

# Initialize the Flask application
app = Flask(__name__)

# Configure the SQLite database. 
# 'food_delivery.db' will be created in your project directory.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food_delivery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database object
db = SQLAlchemy(app)

# 1. USERS TABLE
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    # Role can be 'customer', 'restaurant', or 'driver'
    role = db.Column(db.String(20), nullable=False)
    
    # Relationships - Explicit foreign keys for clarity
    orders = db.relationship('Order', backref='customer_user', lazy=True, foreign_keys='Order.customer_id')

# 2. RESTAURANTS TABLE
class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    restaurant_name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    
    # Relationships
    menu_items = db.relationship('MenuItem', backref='restaurant_parent', lazy=True)

# 3. MENU ITEMS TABLE
class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    dish_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)

# 4. CART TABLE (Ensures unique session tracking per user)
class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

# 5. ORDERS TABLE
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) 
    total_amount = db.Column(db.Float, nullable=False)
    # Status: 'pending', 'accepted', 'delivering', 'completed'
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    eta = db.Column(db.String(50), nullable=True)

# MAIN BLOCK: Initializes the database file
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("------------------------------------------")
        print("SUCCESS: 'food_delivery.db' created!")
        print("You can now see the database file in your folder.")
        print("------------------------------------------")