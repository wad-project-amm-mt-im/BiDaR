from flask_login import UserMixin

from __init__ import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    gender = db.Column(db.String(10))
    state = db.Column(db.String(1000))
    birthday = db.Column(db.DateTime)


class Interest(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, primary_key=True)
    interest = db.Column(db.String(1000), unique=True)
