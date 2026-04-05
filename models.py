from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


from sqlalchemy import MetaData

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
db = SQLAlchemy(metadata=MetaData(naming_convention=convention))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id_user = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    # telegram_number = db.Column(db.String(256), nullable=False)

    def get_id(self):
        return str(self.id_user)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class TelegramTarget(db.Model):
    __tablename__ = 'telegram_targets'
    id_telegram_target = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)


class Kategori(db.Model):
    __tablename__ = 'categories'
    id_kategori = db.Column(db.Integer, primary_key=True)
    kategori = db.Column(db.String(100))
    website = db.relationship('Website', backref='kategori', lazy=True)


class Website(db.Model):
    __tablename__ = 'websites'
    id_web = db.Column(db.Integer, primary_key=True)
    nama_web = db.Column(db.String(100))
    url_web = db.Column(db.String(200))
    slug_web = db.Column(db.String(200))
    pages = db.relationship('Page', backref='website', lazy=True)
    deskripsi_web = db.Column(db.String(256), nullable=True)
    kategori_web = db.Column(db.Integer, db.ForeignKey(
        'categories.id_kategori', ondelete='SET NULL'), nullable=True)


class Page(db.Model):
    __tablename__ = 'pages'
    id_page = db.Column(db.Integer, primary_key=True)
    id_web = db.Column(db.Integer, db.ForeignKey(
        'websites.id_web', ondelete='CASCADE'), nullable=False)
    halaman_web = db.Column(db.String(100))
