from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

listing_amenities = db.Table('listing_amenities',
    db.Column('listing_id', db.Integer, db.ForeignKey('listing.id'), primary_key=True),
    db.Column('amenity_id', db.Integer, db.ForeignKey('amenity.id'), primary_key=True)
)

class Amenity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_host = db.Column(db.Boolean, default=False)
    phone_number = db.Column(db.String(20)) # New
    profile_pic = db.Column(db.String(200)) # New
    
    listings = db.relationship('Listing', backref='host', lazy=True)
    bookings = db.relationship('Booking', backref='driver', lazy=True)
    favorites = db.relationship('Listing', secondary='user_favorites', backref='favorited_by', lazy='dynamic')

user_favorites = db.Table('user_favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('listing_id', db.Integer, db.ForeignKey('listing.id'), primary_key=True)
)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    hourly_rate = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    latitude = db.Column(db.Float) # New for Map
    longitude = db.Column(db.Float) # New for Map
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    bookings = db.relationship('Booking', backref='listing', lazy=True)
    reviews = db.relationship('Review', backref='listing', lazy=True)
    amenities = db.relationship('Amenity', secondary=listing_amenities, lazy='subquery',
        backref=db.backref('listings', lazy=True))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False) # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    
    author = db.relationship('User', backref='reviews_written', lazy=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, confirmed, cancelled
    payment_status = db.Column(db.String(20), default='unpaid') # unpaid, paid, refunded
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
