from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Listing, Booking, Review, Amenity
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev_secret_key_123' # Change for production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parkshare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_amenities():
    amenities = ['EV Charging', 'CCTV', 'Covered Parking', 'Gated', '24/7 Access']
    for name in amenities:
        if not Amenity.query.filter_by(name=name).first():
            db.session.add(Amenity(name=name))
    db.session.commit()

@app.route('/')
def index():
    amenities = Amenity.query.all()
    return render_template('index.html', amenities=amenities)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_host = request.form.get('is_host') == 'on'
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.')
            return redirect(url_for('register'))
            
        new_user = User(username=username, email=email, 
                        password_hash=generate_password_hash(password, method='scrypt'),
                        is_host=is_host)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('dashboard' if is_host else 'index'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard' if user.is_host else 'index'))
        else:
            flash('Please check your login details and try again.')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_host:
        return redirect(url_for('index'))
    listings = Listing.query.filter_by(host_id=current_user.id).all()
    # Calculate earnings (mocked for now or simple sum)
    earnings = sum(booking.total_price for listing in listings for booking in listing.bookings if booking.status == 'confirmed')
    return render_template('dashboard.html', listings=listings, earnings=earnings)

@app.route('/create_listing', methods=['GET', 'POST'])
@login_required
def create_listing():
    if not current_user.is_host:
        flash('Only hosts can create listings.')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        location = request.form.get('location')
        hourly_rate = float(request.form.get('hourly_rate'))
        description = request.form.get('description')
        latitude = float(request.form.get('latitude', 0.0))
        longitude = float(request.form.get('longitude', 0.0))
        
        new_listing = Listing(title=title, location=location, hourly_rate=hourly_rate, 
                              description=description, host_id=current_user.id,
                              latitude=latitude, longitude=longitude)
                              
        # Handle Amenities
        amenity_ids = request.form.getlist('amenities')
        for amenity_id in amenity_ids:
            amenity = Amenity.query.get(int(amenity_id))
            if amenity:
                new_listing.amenities.append(amenity)
                
        db.session.add(new_listing)
        db.session.commit()
        flash('Listing created successfully!')
        return redirect(url_for('dashboard'))
        
    amenities = Amenity.query.all()
    return render_template('create_listing.html', amenities=amenities)

@app.route('/delete_listing/<int:id>', methods=['POST'])
@login_required
def delete_listing(id):
    listing = Listing.query.get_or_404(id)
    if listing.host_id != current_user.id:
        flash('You do not have permission to delete this listing.')
        return redirect(url_for('dashboard'))
        
    db.session.delete(listing)
    db.session.commit()
    flash('Listing deleted.')
    return redirect(url_for('dashboard'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    selected_amenities = request.args.getlist('amenities')
    
    high_traffic = False
    listings = []
    
    # Base Query
    query_obj = Listing.query
    
    if query:
        query_obj = query_obj.filter(Listing.location.ilike(f'%{query}%'))
        
    if min_price is not None:
        query_obj = query_obj.filter(Listing.hourly_rate >= min_price)
        
    if max_price is not None:
        query_obj = query_obj.filter(Listing.hourly_rate <= max_price)
        
    if selected_amenities:
        for amenity_id in selected_amenities:
            query_obj = query_obj.filter(Listing.amenities.any(id=int(amenity_id)))
            
    listings = query_obj.all()
    
    # Traffic Logic
    if listings:
        now = datetime.datetime.now()
        active_bookings = 0
        for listing in listings:
            is_booked = Booking.query.filter(
                Booking.listing_id == listing.id,
                Booking.status != 'cancelled',
                Booking.start_time <= now,
                Booking.end_time >= now
            ).count() > 0
            if is_booked:
                active_bookings += 1
        
        if len(listings) > 0 and (active_bookings / len(listings)) > 0.5:
            high_traffic = True
            
    # Fallback for demo
    if query.lower() == 'market square' and not listings:
         high_traffic = True
         listings = Listing.query.all()

    amenities = Amenity.query.all()
    
    # Get user favorites if logged in
    user_favorites = []
    if current_user.is_authenticated:
        user_favorites = [listing.id for listing in current_user.favorites]
        
    return render_template('index.html', query=query, high_traffic=high_traffic, listings=listings, amenities=amenities, user_favorites=user_favorites)

@app.route('/toggle_favorite/<int:listing_id>', methods=['POST'])
@login_required
def toggle_favorite(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing in current_user.favorites:
        current_user.favorites.remove(listing)
        flash('Removed from favorites.')
    else:
        current_user.favorites.append(listing)
        flash('Added to favorites!')
    db.session.commit()
    # Redirect back to where they came from or index
    return redirect(request.referrer or url_for('index'))

@app.route('/book/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def book(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if request.method == 'POST':
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        
        try:
            start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
            end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format.')
            return redirect(url_for('book', listing_id=listing_id))
            
        if start_time >= end_time:
            flash('End time must be after start time.')
            return redirect(url_for('book', listing_id=listing_id))
            
        if start_time < datetime.datetime.now():
             flash('Booking cannot be in the past.')
             return redirect(url_for('book', listing_id=listing_id))

        # Conflict Detection
        overlapping_bookings = Booking.query.filter(
            Booking.listing_id == listing.id,
            Booking.status != 'cancelled',
            Booking.end_time > start_time,
            Booking.start_time < end_time
        ).first()
        
        if overlapping_bookings:
            flash('This spot is already booked for the selected time.')
            return redirect(url_for('book', listing_id=listing_id))
            
        duration_hours = (end_time - start_time).total_seconds() / 3600
        total_price = duration_hours * listing.hourly_rate
        
        new_booking = Booking(
            start_time=start_time,
            end_time=end_time,
            total_price=total_price,
            user_id=current_user.id,
            listing_id=listing.id,
            status='pending',
            payment_status='unpaid'
        )
        db.session.add(new_booking)
        db.session.commit()
        
        return redirect(url_for('payment', booking_id=new_booking.id))
        
    return render_template('booking.html', listing=listing)

@app.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id or booking.status != 'pending':
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Simulate Payment Processing
        booking.status = 'confirmed'
        booking.payment_status = 'paid'
        db.session.commit()
        flash('Payment successful! Booking confirmed.')
        return redirect(url_for('history'))
        
    return render_template('payment.html', booking=booking)

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        return redirect(url_for('history'))
        
    if booking.start_time > datetime.datetime.utcnow():
        booking.status = 'cancelled'
        booking.payment_status = 'refunded'
        db.session.commit()
        flash('Booking cancelled and refunded.')
    else:
        flash('Cannot cancel past or ongoing bookings.')
        
    return redirect(url_for('history'))

@app.route('/history')
@login_required
def history():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.start_time.desc()).all()
    return render_template('history.html', bookings=bookings, now=datetime.datetime.utcnow())
            
@app.route('/add_review/<int:listing_id>', methods=['POST'])
@login_required
def add_review(listing_id):
    rating = int(request.form.get('rating'))
    comment = request.form.get('comment')
    
    review = Review(rating=rating, comment=comment, user_id=current_user.id, listing_id=listing_id)
    db.session.add(review)
    db.session.commit()
    flash('Review added!')
    return redirect(url_for('history'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.phone_number = request.form.get('phone_number')
        # Mock profile pic update
        db.session.commit()
        flash('Profile updated!')
        return redirect(url_for('profile'))
    return render_template('profile.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_amenities() # Initialize default amenities
    print("Starting ParkShare application...")
    app.run(debug=True)

