from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from model import db, User # Note: I renamed 'models' to 'model' to match your file in the screenshot
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'upskill_internship_secret_key' # Needed for flashing messages

# Configure Database path
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'food_delivery.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# 1. HOME / REGISTRATION PAGE
@app.route('/')
def index():
    return render_template('register.html')

# 2. LOGIN PAGE
@app.route('/login_page')
def login_page():
    return render_template('login.html')

# 3. BACKEND REGISTRATION LOGIC
@app.route('/register', methods=['POST'])
def register():
    # Check if request is from HTML form or JSON
    if request.is_json:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
    else:
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

    if User.query.filter_by(email=email).first():
        flash("Email already exists!", "danger")
        return redirect(url_for('index'))
    
    hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(name=name, email=email, password_hash=hashed_pw, role=role)
    
    db.session.add(new_user)
    db.session.commit()
    
    flash(f"Account created successfully for {name}!", "success")
    return redirect(url_for('login_page'))

# 4. BACKEND LOGIN LOGIC
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password_hash, password):
        flash(f"Welcome back, {user.name}! You are logged in as a {user.role}.", "success")
        return f"<h1>Success!</h1><p>You are logged in as a {user.role}.</p><a href='/'>Go Back</a>"
    
    flash("Invalid credentials", "danger")
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)