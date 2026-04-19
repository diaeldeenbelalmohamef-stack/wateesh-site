from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os
# --- هنا نضع الأسطر المسؤولة عن الميديا (المكان الصحيح) ---
base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static')) 
# -------------------------------------------------------
app = Flask(__name__)
app.secret_key = "wateesh_2026_key" # ابقِ على هذا المفتاح فقط

# إعداد قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# بيانات الإدارة
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123"

# جدول الأخبار
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# --- المسارات (Routes) ---

@app.route('/')
def home():
    try:
        usd_price = requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()['rates']['EGP']
    except:
        usd_price = "غير متاح"
    
    # قيم تجريبية حالياً (سنربطها بـ API حقيقي لاحقاً)
    oil_price = "85.40 دولار"
    gold_price = "2,350 دولار"
    sports_news = "انطلاق مباريات الدوري السوداني والمحترفين بالخارج"
    
    company_news = News.query.order_by(News.date_posted.desc()).all()
    
    # تأكد من إضافة المتغيرات الجديدة هنا
    return render_template('home.html', 
                           usd_price=usd_price, 
                           oil_price=oil_price, 
                           gold_price=gold_price,
                           sports_news=sports_news,
                           news=company_news)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USERNAME and request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        flash("خطأ في بيانات الدخول!")
    return render_template('login.html')

@app.route('/admin')
def admin_panel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    all_news = News.query.all()
    return render_template('admin.html', news=all_news)

# دالة مهمة لإضافة خبر جديد من لوحة التحكم
@app.route('/add_news', methods=['POST'])
def add_news():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    title = request.form.get('title')
    content = request.form.get('content')
    
    if title and content:
        new_post = News(title=title, content=content)
        db.session.add(new_post)
        db.session.commit()
        flash("تم إضافة الخبر بنجاح!")
    
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)