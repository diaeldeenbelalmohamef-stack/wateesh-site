import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'wateesh_2026_safe'

# إعدادات القاعدة والمجلدات
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "wateesh.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

db = SQLAlchemy(app)

# --- 1. تعريف النماذج (Models) أولاً ---

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- 2. إنشاء الجداول وإضافة البيانات (خارج الكلاسات) ---

with app.app_context():
    db.create_all()  # ينشئ الجداول بناءً على الكلاسات أعلاه
    
    # إضافة منتج تجريبي إذا كانت القاعدة فارغة
    if not Product.query.first():
        p = Product(name="منتج تجريبي من واتيش", price="5000", description="وصف المنتج الأول")
        db.session.add(p)
        db.session.commit()

# --- 3. المسارات (Routes) ---

@app.route('/')
def home():
    news = [
        {"title": "خصم كبير بمناسبة الافتتاح", "date_posted": "2026-04-24"},
        {"title": "وصلت تشكيلة الصيف الجديدة", "date_posted": "2026-04-23"}
    ]
    return render_template('home.html', news=news)

@app.route('/products')
def products():
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

@app.route('/checkout/<int:product_id>')
def checkout(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('checkout.html', product=product)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # هنا يمكنك إضافة كود حفظ رسائل التواصل في قاعدة البيانات مستقبلاً
        return redirect(url_for('home'))
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/admin')
def admin_panel():
    surveys = Survey.query.all()
    return render_template('admin.html', surveys=surveys) 

@app.route('/manage_gallery')
def show_products():
    return render_template('show_products.html', gallery_items=[])

@app.route('/success')
def success():
    return render_template('order_success.html')

@app.route('/median')
def median():
    return render_template('median.html')

# --- 4. تشغيل السيرفر ---

if __name__ == "__main__":
    # تأكد من أن host هو 0.0.0.0
   app.run(host='0.0.0.0', port=5000, debug=True)