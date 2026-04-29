import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'wateesh_2026_safe'

# --- 1. إعدادات قاعدة البيانات ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "wateesh.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- 2. النماذج (Models) ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(200))
    description = db.Column(db.Text)

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.String(20))
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- 3. المسارات (Routes) ---

@app.route('/')
def home():
    products = Product.query.limit(4).all()
    return render_template('home.html', products=products, usd_price=1200)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_in = request.form.get('username')
        pass_in = request.form.get('password')
        user = User.query.filter_by(username=user_in).first()
        
        # بنشيك على الباسورد (سواء هاش أو نص عادي للتجربة)
        if user and (check_password_hash(user.password, pass_in) or user.password == pass_in):
            login_user(user)
            return redirect(url_for('admin_panel'))
        else:
            flash('بيانات الدخول غير صحيحة')
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin_panel():
    surveys = Survey.query.order_by(Survey.id.desc()).all()
    return render_template('admin.html', surveys=surveys)

@app.route('/checkout/<int:product_id>', methods=['GET', 'POST'])
def checkout(product_id):
    product = db.session.get(Product, product_id)
    if request.method == 'POST':
        qty = int(request.form.get('quantity', 1))
        total_price = product.price * qty
        return render_template('invoice.html', 
                               product=product, 
                               quantity=qty, 
                               total=total_price,
                               customer=request.form.get('name'),
                               phone=request.form.get('phone'))
    return render_template('checkout.html', product=product)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        new_survey = Survey(
            rating=request.form.get('rating'),
            feedback=request.form.get('feedback')
        )
        db.session.add(new_survey)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('contact.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- 4. تشغيل السيرفر وإنشاء الجداول ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # إنشاء مستخدم أدمن افتراضي لو مش موجود
        if not User.query.filter_by(username="admin").first():
            hashed_pw = generate_password_hash("admin123")
            admin = User(username="admin", password=hashed_pw)
            db.session.add(admin)
            db.session.commit()
            
    app.run(debug=True)