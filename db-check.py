from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/monitoring_web_itk'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Quick connection test
with app.app_context():
    try:
        db.session.execute(text('SELECT 1'))
        print("✅ Database connected successfully")
    except OperationalError as e:
        print("❌ Database connection failed:", str(e))
