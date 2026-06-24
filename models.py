from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db=SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role= db.Column(db.String(50), nullable=False, default='user')
    Status = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    approval = db.Column(db.Boolean, default=True)

    bookings = db.relationship('Booking', backref='trekker', lazy=True)
    assigned_treks = db.relationship('Trek', backref='assigned_staff', lazy=True)
    staff_profile = db.relationship('TrekStaff', backref='user', uselist=False)

class Trek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    assigned_staffid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)

    bookings = db.relationship('Booking', backref='trek', lazy=True)


class Booking(db.Model):
    booking_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False)

class TrekStaff(db.Model):
    staff_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    contact = db.Column(db.String(15), nullable ='False')








