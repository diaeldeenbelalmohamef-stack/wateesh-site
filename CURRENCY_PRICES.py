import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_login import LoginManager
from flask_login import login_required
from flask_login import UserMixin
from flask_login import login_user
from flask_login import logout_user
from flask import request, render_template


app = Flask(__name__)
app.secret_key = 'wateesh_2026_safe'

# إعدادات القاعدة والمجلدات
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "wateesh.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# تحديد الصفحة التي يتم توجيه المستخدم إليها إذا حاول الدخول وهو غير مسجل
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False) # تأكد من تشفيرها مستقبلاً
@login_manager.user_loader   
def load_user(user_id):
    # بدلاً من User.query.get
    return db.session.get(User, int(user_id))  

# --- 1. تعريف النماذج (Models) أولاً ---

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.Text)
    file_url = db.Column(db.String(200), nullable=False)
    is_video = db.Column(db.Boolean, default=False)    

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- 2. إنشاء الجداول وإضافة البيانات (خارج الكلاسات) ---

with app.app_context():
    db.create_all()
    # إضافة مستخدم أدمن تجريبي
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password="123") # يفضل تشفيرها لاحقاً
        db.session.add(admin)
        db.session.commit()
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
def old_checkout(product_id):
    # بدلاً من Product.query.get_or_404
    product = db.session.get(Product, product_id)
    if not product:
        return "المنتج غير موجود", 404
    return render_template('checkout.html', product=product)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        # 1. استقبال البيانات من الـ Form
        name = request.form.get('name')
        phone = request.form.get('phone')
        payment_method = request.form.get('payment') # استلام طريقة الدفع
        
        # 2. تعيين سعر افتراضي (بما أن السعر لم يرسل من الـ HTML حالياً)
        subtotal = 1000 # يمكنك تغييره لاحقاً ليكون ديناميكياً
        
        # 3. الحسابات
        tax_rate = 0.15
        tax_amount = subtotal * tax_rate
        total_price = subtotal + tax_amount
        
        # 4. التوجيه لصفحة نجاح بدلاً من إرجاع نص جاف
        # يفضل إنشاء ملف success.html بسيط
        return f"شكراً يا {name}! تم استلام طلبك عبر ({payment_method}). الإجمالي: {total_price} ريال. سنتواصل معك على {phone}."

    return render_template('checkout.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # 1. استلام البيانات من حقول الـ HTML (تأكد أن الـ name في HTML مطابق)
        user_feedback = request.form.get('message') # أو اسم الحقل عندك
        
        # 2. إنشاء سجل جديد في قاعدة البيانات
        new_message = Survey(feedback=user_feedback)
        
        # 3. حفظ البيانات
        db.session.add(new_message)
        db.session.commit()
        
        flash('شكراً لك! تم استلام رسالتك بنجاح.')
        return redirect(url_for('home'))
        
    return render_template('contact.html')
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_in = request.form.get('username')
        pass_in = request.form.get('password')
        user = User.query.filter_by(username=user_in).first()
        
        if user and user.password == pass_in: # تأكد من مطابقة كلمة المرور
            login_user(user)
            return redirect(url_for('admin_panel'))
        else:
            flash('خطأ في اسم المستخدم أو كلمة المرور')
            
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin_panel():
    # Only logged-in users can see this
    surveys = Survey.query.all()
    return render_template('admin.html', surveys=surveys)

@app.route('/delete_survey/<int:id>')
@login_required
def delete_survey(id):
    # البحث عن الرسالة برقم المعرف الخاص بها
    message_to_delete = db.session.get(Survey, id)
    
    if message_to_delete:
        db.session.delete(message_to_delete)
        db.session.commit()
        flash('تم حذف الرسالة بنجاح')
    
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح')
    return redirect(url_for('login'))


@app.route('/manage_gallery')
def show_products():
    # جلب العناصر من قاعدة البيانات
    items = Gallery.query.all() 
    return render_template('show_products.html', gallery_items=items)

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