from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    user_type = db.Column(db.String(10), nullable=False)  # 'patient' or 'driver'
    lat = db.Column(db.Float)  # Current latitude, for drivers mainly
    lng = db.Column(db.Float)  # Current longitude

class Ambulance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(10), default='active')  # 'active' or 'inactive'
    driver = db.relationship('User', backref='ambulance', uselist=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ambulance_id = db.Column(db.Integer, db.ForeignKey('ambulance.id'), nullable=False)
    status = db.Column(db.String(10), default='pending')  # 'pending', 'confirmed', 'rejected', 'completed'
    patient_lat = db.Column(db.Float, nullable=False)
    patient_lng = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    patient = db.relationship('User', backref='bookings')
    ambulance = db.relationship('Ambulance', backref='bookings')