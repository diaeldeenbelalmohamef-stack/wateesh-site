import os
import sqlite3
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, make_response # تأكد من استدعاء make_response



# 1. إعداد التطبيق الأساسي
base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

app.secret_key = 'WATEESH_SECRET_2026_PRO'  # مفتاح تشفير الجلسات

# 2. إعداد قاعدة البيانات (وحدناها كلها في wateesh.db)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'wateesh.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# دالة لإنشاء جداول SQLite التقليدية (للاستبيانات والطلبات)
def init_sqlite_db():
    conn = sqlite3.connect(os.path.join(base_dir, 'wateesh.db'))
    cursor = conn.cursor()
    # جدول الاستبيانات
    cursor.execute('''CREATE TABLE IF NOT EXISTS survey_results 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       rating TEXT NOT NULL, 
                       feedback TEXT, 
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    # جدول طلبات الشراء
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       product_id TEXT, 
                       qty INTEGER, 
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# نموذج الأخبار باستخدام SQLAlchemy
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

# إنشاء كل الجداول عند تشغيل السيرفر
with app.app_context():
    init_sqlite_db()
    db.create_all()

# بيانات الإدارة (البسيطة)
ADMIN_USER = "admin"
ADMIN_PASS = "123"

# --- 3. المسارات (Routes) ---
@app.route('/')
def home():
    try:
        # جلب سعر الصرف
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=3)
        usd_price = response.json()['rates'].get('EGP', 'غير متاح')
    except:
        usd_price = "خطأ في الاتصال"
    
    # جلب الأخبار من القاعدة لعرضها في الصفحة الرئيسية
    all_news = News.query.order_by(News.date_posted.desc()).all()
    
    # تحضير الـ Response لإضافة الـ Header الخاص بـ ngrok
    resp = make_response(render_template('home.html', 
                            usd_price=usd_price, 
                            news=all_news,
                            oil_price="85.40$", 
                            gold_price="2350$"))
    
    # السطر السحري عشان تتخطى رسالة ngrok الرخمة
    resp.headers['ngrok-skip-browser-warning'] = 'any_value'
    
    return resp

@app.route('/survey', methods=['POST'])
def handle_survey():
    rating = request.form.get('rating')
    feedback = request.form.get('feedback')
    try:
        with sqlite3.connect(os.path.join(base_dir, 'wateesh.db')) as conn:
            conn.execute("INSERT INTO survey_results (rating, feedback) VALUES (?, ?)", (rating, feedback))
        flash("شكراً لمشاركتك في استبيان WATEESH!")
    except Exception as e:
        flash(f"خطأ في الحفظ: {e}")
    return redirect(url_for('home'))

@app.route('/order', methods=['POST'])
def handle_order():
    p_id = request.form.get('product_id')
    qty = request.form.get('quantity')
    try:
        with sqlite3.connect(os.path.join(base_dir, 'wateesh.db')) as conn:
            conn.execute("INSERT INTO orders (product_id, qty) VALUES (?, ?)", (p_id, qty))
        return "<h3>تم استلام طلبك بنجاح! سنتواصل معك قريباً.</h3>"
    except Exception as e:
        return f"خطأ: {e}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if user == ADMIN_USER and pw == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        flash("بيانات الدخول غير صحيحة!")
    return render_template('login.html')

@app.route('/admin')
def admin_panel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # جلب الاستبيانات من SQLite
    conn = sqlite3.connect(os.path.join(base_dir, 'wateesh.db'))
    conn.row_factory = sqlite3.Row
    surveys = conn.execute("SELECT * FROM survey_results ORDER BY created_at DESC").fetchall()
    conn.close()
    
    # جلب الأخبار من SQLAlchemy
    news_list = News.query.all()
    
    return render_template('admin.html', surveys=surveys, news=news_list)

@app.route('/add_news', methods=['POST'])
def add_news():
    if session.get('logged_in'):
        title = request.form.get('title')
        content = request.form.get('content')
        if title and content:
            new_entry = News(title=title, content=content)
            db.session.add(new_entry)
            db.session.commit()
            flash("تم نشر الخبر بنجاح")
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# صفحة الميديا
@app.route('/median')
def median():
    return render_template('median.html')
@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/contact')
def contact():
    return render_template('contact.html') # تأكد أن الملف موجود في مجلد templates
if __name__ == '__main__':
    app.run(debug=True, port=5000)