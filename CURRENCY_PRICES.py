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
import sqlite3 
from flask import redirect, url_for




app = Flask(__name__)
app.secret_key = 'wateesh_2026_safe'

# إعداد مسار لحفظ الملفات (تأكد إن المجلد موجود)
# تحديد المجلد الرئيسي كـ static مباشرة
UPLOAD_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# لرفع فيديوهات بمساحة كبيرة (مثلاً 100 ميجا)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# إعدادات القاعدة والمجلدات
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "wateesh.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

def sync_database():
    conn = sqlite3.connect('wateesh.db')
    cursor = conn.cursor()
    
    # 1. نتأكد إن الجدول الأساسي موجود
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS survey (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feedback TEXT,
            rating TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. نستخدم ALTER TABLE اللي إنت قلت عليها عشان لو الأعمدة ناقصة
    # بنعملها لكل عمود بنشك فيه عشان نضمن إن قاعدة البيانات "محتوية" للكل
    try:
        cursor.execute("ALTER TABLE survey ADD COLUMN feedback TEXT")
    except sqlite3.OperationalError:
        pass # العمود موجود أصلاً، فلاسك مش محتاج يزعل

    try:
        cursor.execute("ALTER TABLE survey ADD COLUMN rating TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE survey ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()
    print("قاعدة البيانات اتظبطت وبقت جاهزة لكل ملفات الـ HTML!")

# نادِ الدالة دي
sync_database()


def save_to_db(filename):
    conn = sqlite3.connect('wateesh.db') # تأكد من اسم ملف قاعدتك
   # conn.row_factory = sqlite3.Row  # هذا السطر هو السحر اللي بيخليك تستخدم p.id بدل p[0]
    cursor = conn.cursor()
    # لنفترض أن اسم الجدول content وفيه عمود لاسم الصورة
    cursor.execute("INSERT INTO content (image_path) VALUES (?)", (filename,))
    conn.commit()
    conn.close()
def create_tables():
    conn = sqlite3.connect('wateesh.db')
    cursor = conn.cursor()
    
    # إنشاء جدول المحتوى (للصور)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL
        )
    ''')
    
    
    # إنشاء جدول الأخبار (عشان الـ Loop بتاع الأخبار ما يضربش)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date_posted TEXT
        )
    ''')
        # إضافة جدول المنتجات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        image_path TEXT,
        description TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print("تم إنشاء الجداول بنجاح!")

# نفذ الدالة دي مرة واحدة
create_tables()  
def add_sample_products():
    conn = sqlite3.connect('wateesh.db')
    cursor = conn.cursor()
    
    # إضافة منتج تجريبي
    # (الاسم، السعر، اسم الصورة في مجلد static، الوصف)
    cursor.execute('''
        INSERT INTO products (name, price, image_path, description) 
        VALUES (?, ?, ?, ?)
    ''', ('تيشرت وتيش فخم', 5000, 'TOMYHILLFIGURE.webp', 'خامة قطنية أصلية من مراتع كردفان'))
    
    conn.commit()
    conn.close()
    print("تم إضافة المنتج بنجاح!")

#add_sample_products() 

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
    image_url = db.Column(db.String(200)) # تأكد من وجود هذا السطر
class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.Text)
    file_url = db.Column(db.String(200), nullable=False)
    is_video = db.Column(db.Boolean, default=False)    

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feedback = db.Column(db.Text)
    # بدل UTC، خليه يستخدم وقت الجهاز المحلي
    created_at = db.Column(db.DateTime, default=datetime.now)
    
   

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
    conn = sqlite3.connect('wateesh.db')
    cursor = conn.cursor()
    
    # 1. جلب الصور
    cursor.execute("SELECT image_path FROM content")
    images = cursor.fetchall()
    
    # 2. جلب الأخبار (لو عندك جدول للأخبار)
    cursor.execute("SELECT title, date_posted FROM news ORDER BY id DESC")
    news_list = cursor.fetchall()
    
    conn.close()
    
    # نبعت كل البيانات في سطر الـ return
    return render_template('home.html', 
                           images=images, 
                           news=news_list, 
                           usd_price=1200) # أو السعر اللي بتجيبه من الـ API

@app.route('/products')
def products():
    conn = sqlite3.connect('wateesh.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    all_products = cursor.fetchall()
    conn.close()
    return render_template('products.html', products=all_products)


# أضفنا methods=['GET', 'POST'] عشان نسمح بإرسال البيانات
@app.route('/checkout/<int:product_id>', methods=['GET', 'POST'])
def checkout(product_id):
    conn = sqlite3.connect('wateesh.db')
    # تأكد إن السطر ده ملغي بالهاش لو عايز تستخدم أرقام [0]
    # conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    if request.method == 'POST':
        try:
            # 1. سحب الكمية والتأكد إنها رقم
            raw_qty = request.form.get('quantity')
            # لو الحقل فاضي أو مش رقم بنخليه 1 تلقائياً
            qty = int(raw_qty) if raw_qty and raw_qty.isdigit() else 1
            
            # 2. سحب السعر من الفهرس رقم 2 (تأكد إن السعر هو العمود الثالث في جدولك)
            # بننظف السعر من أي كلمات زي "ج.س" لو موجودة عشان ما يعملش خطأ
            price_data = str(product[2]).replace('ج.س', '').strip()
            price = float(price_data)
            
            total_price = price * qty
            
            # 3. سحب باقي البيانات
            customer_name = request.form.get('name')
            phone = request.form.get('phone')
            payment_method = request.form.get('payment')

            return render_template('invoice.html', 
                                   product=product, 
                                   quantity=qty, 
                                   total=total_price, 
                                   customer=customer_name,
                                   phone=phone,
                                   payment=payment_method)
        except Exception as e:
            # ده عشان يطبع لك في الشاشة السوداء (Terminal) الغلط فين بالظبط
            print(f"DEBUG: Error details -> {e}")
            return f"خطأ في الحسابات: {e}", 400

    return render_template('checkout.html', product=product)


# دالة إضافة منتج جديد

@app.route('/add_product', methods=['GET', 'POST'])
@login_required  # <-- السطر ده هو اللي هيمنع أي حد مش مسجل دخول من دخول الصفحة
def add_product():
    # 1. قراءة الصور (دي بره الـ if عشان تظهر في الـ GET والـ POST)
    static_path = os.path.join(app.root_path, 'static')
    images = [f for f in os.listdir(static_path) if f.endswith(('.png', '.jpg', '.jpeg'))]

    if request.method == 'POST':
        try:
            # 2. استلام البيانات (لازم تكون متدخلة لجوه تحت الـ if)
            name = request.form.get('name')
            price = request.form.get('price')
            image_to_save = request.form.get('image') 
            desc = request.form.get('description')

            # 3. الاتصال بقاعدة البيانات والحفظ
            conn = sqlite3.connect('wateesh.db')
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (name, price, image_path, description) 
                VALUES (?, ?, ?, ?)
            """, (name, price, image_to_save, desc))
            
            conn.commit()
            conn.close()
            return "تمت إضافة المنتج بنجاح يا معلم! <a href='/'>ارجع شوفه في المتجر</a>"
        
        except Exception as e:
            print(f"DEBUG: Error -> {e}")
            return f"حصلت مشكلة: {e}"

    # 4. لو الصفحة بتتفتح عادي (GET) بنعرض الفورم ونبعت له قائمة الصور
    return render_template('add_product.html', images=images)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # التأكد من سحب البيانات من الـ HTML
        rating_value = request.form.get('rating') 
        feedback_text = request.form.get('feedback')
        
        conn = sqlite3.connect('wateesh.db')
        cursor = conn.cursor()
        
        # التصحيح هنا: اسم الجدول survey بدون S
        try:
            # إضافة عمود created_at واستخدام CURRENT_TIMESTAMP عشان SQL يسجل الوقت أوتوماتيك
            cursor.execute(
                "INSERT INTO survey (rating, feedback, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)", 
                (rating_value, feedback_text))

            conn.commit()
        except sqlite3.OperationalError as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return f"الجدول غير موجود: {e}"
        finally:
            conn.close()
            
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
            return redirect(url_for('admmin'))
        else:
            flash('خطأ في اسم المستخدم أو كلمة المرور')
            
    return render_template('login.html')

@app.route('/admin') # أو الرابط اللي بتستخدمه
def admmin():
    # 1. نفتح الاتصال بقاعدة البيانات
    conn = sqlite3.connect('wateesh.db')
    conn.row_factory = sqlite3.Row
    
    # 2. نطلب البيانات ونخلي SQL ينسق التاريخ فوراً
    # استخدمنا strftime عشان نحول شكل الوقت لتاريخ ووقت مفهوم
    query = """
    SELECT id, feedback, rating, 
    strftime('%d/%m/%Y - %H:%M', created_at) as created_at 
    FROM survey ORDER BY id DESC
    """
    
    surveys = conn.execute(query).fetchall()
    conn.close()
    
    # 3. نرسل البيانات لصفحة admin.html
    return render_template('admin.html', surveys=surveys)



@app.route('/submit_survey', methods=['POST'])
def submit_survey():
    rating = request.form.get('rating')
    feedback = request.form.get('feedback')
    
    conn = sqlite3.connect('wateesh.db')
    cursor = conn.cursor()
    # إضافة البيانات للـ 3 أعمدة: feedback, created_at, rating
    cursor.execute("INSERT INTO survey (feedback, rating, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)", 
                   (feedback, rating))
    conn.commit()
    conn.close()
    # جوه دالة الـ login لما الباسورد يصح
    return redirect(url_for('admmin'))  # أو وديه لصفحة شكر

@app.route('/delete_survey/<int:id>')
@login_required
def delete_survey(id):
    # البحث عن الرسالة برقم المعرف الخاص بها
    message_to_delete = db.session.get(Survey, id)
    
    if message_to_delete:
        db.session.delete(message_to_delete)
        db.session.commit()
        flash('تم حذف الرسالة بنجاح')
    
    return redirect(url_for('admin.html'))

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


@app.route('/add_content', methods=['POST'])
def add_content():
    file = request.files.get('file')
    if file:
        # هنا بنستخدم secure_filename اللي كانت باهتة
        filename = secure_filename(file.filename) 
        if file:
        # هنا الدالة 'نورت' لأننا استخدمناها
        # بتشيل أي مسافات أو رموز غريبة من اسم الملف
            filename = secure_filename(file.filename)
        
        # التأكد من حفظ الملف بالاسم الآمن
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        save_to_db(filename)
        return redirect(url_for('home')) 
    return "فشل الرفع"

# --- 4. تشغيل السيرفر ---

if __name__ == "__main__":
    with app.app_context():
        # إنشاء جداول SQLAlchemy (User, Survey, etc.)
        db.create_all()
        
        # إنشاء جداول sqlite3 العادية (products, content, news)
        create_tables()
        
        # تعطيل الإضافة التلقائية عشان ما يحصلش تكرار أو قفل للقاعدة
        # add_sample_products() 

        # إضافة مستخدم أدمن لو مش موجود
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", password="123")
            db.session.add(admin)
            db.session.commit()

    print("سيرفر وتيش انطلق بنجاح على http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
