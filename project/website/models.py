from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(1000))
    file_name = db.Column(db.String(300))
    date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    public = db.Column(db.Boolean, default=False)
    subject = db.Column(db.String(100), default='General')  # New field for subjects


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    notes = db.relationship('Note', backref='user', lazy=True)
    students = db.relationship('Student', backref='user', lazy=True,cascade='all, delete-orphan')
    teachers = db.relationship('Teacher', backref='user', lazy=True,cascade='all, delete-orphan') 


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    class_section = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150))
    profile_pic = db.Column(db.String(300))  # File path for profile picture
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Who added this student
    date_added = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    position = db.Column(db.Integer, default=0)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150))
    profile_pic = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date_added = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    position = db.Column(db.Integer, default=0)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    filename = db.Column(db.String(300))
    file_type = db.Column(db.String(50))  # 'web' or 'desktop'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date_uploaded = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    downloads = db.Column(db.Integer, default=0)
    requirements = db.Column(db.String(300))  # e.g., "tkinter, pillow"
    instructions = db.Column(db.String(500))  # How to play/run the game


class FlappyScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date_achieved = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)