from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import math

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

class TrafficArea(db.Model):
    """Represents major parking areas (e.g., Market Square, Downtown)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    max_capacity = db.Column(db.Integer, default=100)  # Max public parking spots
    current_occupancy = db.Column(db.Integer, default=0)
    is_full = db.Column(db.Boolean, default=False)
    congestion_level = db.Column(db.String(20), default='low')  # low, medium, high, blocked
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_traffic_status(self):
        """Returns color status for UI: green, yellow, red"""
        if self.congestion_level == 'blocked':
            return 'red'
        elif self.congestion_level == 'high':
            return 'orange'
        elif self.congestion_level == 'medium':
            return 'yellow'
        return 'green'
    
    def get_occupancy_percentage(self):
        """Returns occupancy percentage"""
        if self.max_capacity == 0:
            return 0
        return (self.current_occupancy / self.max_capacity) * 100

class AvailableSlot(db.Model):
    """Represents available time slots for listings"""
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    listing = db.relationship('Listing', backref='available_slots')
    
    def is_time_slot_available(self):
        """Check if slot is available and not booked"""
        if not self.is_available:
            return False
        # Check for overlapping bookings
        overlapping = Booking.query.filter(
            Booking.listing_id == self.listing_id,
            Booking.status != 'cancelled',
            Booking.end_time > self.start_time,
            Booking.start_time < self.end_time
        ).first()
        return overlapping is None