from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Listing, Booking, Review, Amenity, TrafficArea, AvailableSlot
import datetime
import math

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

def init_traffic_areas():
    """Initialize common parking areas"""
    areas = [
        {'name': 'Market Square', 'lat': 40.7128, 'lon': -74.0060, 'capacity': 50},
        {'name': 'Downtown Center', 'lat': 40.7255, 'lon': -73.9983, 'capacity': 75},
        {'name': 'Airport District', 'lat': 40.7700, 'lon': -73.8740, 'capacity': 200},
        {'name': 'Harbor Front', 'lat': 40.6892, 'lon': -74.0445, 'capacity': 100},
        {'name': 'Tech Park', 'lat': 40.7489, 'lon': -73.9680, 'capacity': 150},
    ]
    
    for area in areas:
        if not TrafficArea.query.filter_by(name=area['name']).first():
            new_area = TrafficArea(
                name=area['name'],
                latitude=area['lat'],
                longitude=area['lon'],
                max_capacity=area['capacity']
            )
            db.session.add(new_area)
    db.session.commit()

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km (Haversine formula)"""
    R = 6371  # Earth radius in km
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def get_area_traffic_status(area_name):
    """Determine traffic status based on current occupancy"""
    area = TrafficArea.query.filter_by(name=area_name).first()
    if not area:
        return {'status': 'unknown', 'color': 'gray', 'percentage': 0}
    
    occupancy = area.get_occupancy_percentage()
    
    if occupancy >= 100:
        area.congestion_level = 'blocked'
    elif occupancy >= 80:
        area.congestion_level = 'high'
    elif occupancy >= 50:
        area.congestion_level = 'medium'
    else:
        area.congestion_level = 'low'
    
    area.is_full = occupancy >= 100
    db.session.commit()
    
    return {
        'status': area.congestion_level,
        'color': area.get_traffic_status(),
        'percentage': occupancy,
        'is_full': area.is_full
    }

def find_nearby_parking(search_location_lat, search_location_lon, search_area_name, radius_km=5):
    """Find available private parking near congested areas"""
    all_listings = Listing.query.all()
    nearby_listings = []
    
    now = datetime.datetime.now()
    
    for listing in all_listings:
        if listing.latitude is None or listing.longitude is None:
            continue
            
        distance = calculate_distance(
            search_location_lat, search_location_lon,
            listing.latitude, listing.longitude
        )
        
        if distance <= radius_km:
            # Check if listing has available slots now
            available_booking = Booking.query.filter(
                Booking.listing_id == listing.id,
                Booking.status == 'confirmed',
                Booking.end_time > now
            ).first()
            
            nearby_listings.append({
                'listing': listing,
                'distance': round(distance, 2),
                'host': listing.host
            })
    
    # Sort by distance
    nearby_listings.sort(key=lambda x: x['distance'])
    return nearby_listings[:10]  # Return top 10 nearest

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
    
    # Calculate earnings from completed bookings
    completed_bookings = Booking.query.filter(
        Booking.listing_id.in_([l.id for l in listings]),
        Booking.status == 'confirmed',
        Booking.payment_status == 'paid'
    ).all()
    
    total_earnings = sum(booking.total_price for booking in completed_bookings)
    
    # Calculate stats
    total_bookings = len(completed_bookings)
    total_hours = sum(
        (booking.end_time - booking.start_time).total_seconds() / 3600 
        for booking in completed_bookings
    )
    
    # Get ratings
    all_reviews = Review.query.filter(
        Review.listing_id.in_([l.id for l in listings])
    ).all()
    avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews) if all_reviews else 0
    
    earnings_breakdown = {}
    for listing in listings:
        listing_bookings = Booking.query.filter(
            Booking.listing_id == listing.id,
            Booking.status == 'confirmed'
        ).all()
        earnings_breakdown[listing.id] = sum(b.total_price for b in listing_bookings)
    
    return render_template(
        'dashboard.html',
        listings=listings,
        earnings=total_earnings,
        total_bookings=total_bookings,
        total_hours=round(total_hours, 1),
        avg_rating=round(avg_rating, 1),
        earnings_breakdown=earnings_breakdown
    )

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
    high_traffic_status = None
    reroute_suggestions = []
    listings = []
    traffic_area = None
    
    # Check traffic status for the searched area
    if query:
        traffic_area = TrafficArea.query.filter_by(name=query).first()
        if traffic_area:
            traffic_status = get_area_traffic_status(query)
            high_traffic = traffic_status['is_full']
            high_traffic_status = traffic_status
            
            # If area is full/high traffic, suggest nearby private parking
            if high_traffic or traffic_status['percentage'] >= 75:
                reroute_suggestions = find_nearby_parking(
                    traffic_area.latitude,
                    traffic_area.longitude,
                    query,
                    radius_km=5
                )
    
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
    
    amenities = Amenity.query.all()
    
    # Get user favorites if logged in
    user_favorites = []
    if current_user.is_authenticated:
        user_favorites = [listing.id for listing in current_user.favorites]
        
    return render_template(
        'index.html',
        query=query,
        high_traffic=high_traffic,
        high_traffic_status=high_traffic_status,
        reroute_suggestions=reroute_suggestions,
        listings=listings,
        amenities=amenities,
        user_favorites=user_favorites,
        traffic_area=traffic_area
    )

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

# ============== API Routes for AJAX ==============

@app.route('/api/traffic_status/<area_name>')
def api_traffic_status(area_name):
    """API endpoint to get traffic status for an area"""
    status = get_area_traffic_status(area_name)
    return jsonify(status)

@app.route('/api/nearby_parking')
def api_nearby_parking():
    """API endpoint to get nearby parking suggestions"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    area_name = request.args.get('area', '')
    radius = request.args.get('radius', 5, type=float)
    
    if lat is None or lon is None:
        return jsonify({'error': 'Missing coordinates'}), 400
    
    suggestions = find_nearby_parking(lat, lon, area_name, radius_km=radius)
    
    result = []
    for item in suggestions:
        result.append({
            'id': item['listing'].id,
            'title': item['listing'].title,
            'location': item['listing'].location,
            'rate': item['listing'].hourly_rate,
            'distance': item['distance'],
            'lat': item['listing'].latitude,
            'lon': item['listing'].longitude,
            'host': item['host'].username
        })
    
    return jsonify(result)

@app.route('/api/earnings/<int:listing_id>')
@login_required
def api_earnings(listing_id):
    """API endpoint to get earnings for a specific listing"""
    listing = Listing.query.get_or_404(listing_id)
    if listing.host_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    bookings = Booking.query.filter(
        Booking.listing_id == listing_id,
        Booking.status == 'confirmed'
    ).all()
    
    total = sum(b.total_price for b in bookings)
    hours = sum((b.end_time - b.start_time).total_seconds() / 3600 for b in bookings)
    
    return jsonify({
        'listing_id': listing_id,
        'total_earnings': round(total, 2),
        'total_bookings': len(bookings),
        'total_hours': round(hours, 1),
        'average_rate': listing.hourly_rate
    })

@app.route('/api/all_traffic_areas')
def api_all_traffic_areas():
    """API endpoint to get all traffic areas and their status"""
    areas = TrafficArea.query.all()
    result = []
    
    for area in areas:
        status = get_area_traffic_status(area.name)
        result.append({
            'id': area.id,
            'name': area.name,
            'lat': area.latitude,
            'lon': area.longitude,
            'occupancy': round(status['percentage'], 1),
            'status': status['status'],
            'color': status['color'],
            'is_full': status['is_full']
        })
    
    return jsonify(result)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_amenities() # Initialize default amenities
        init_traffic_areas() # Initialize traffic areas
    print("Starting ParkShare application...")
    app.run(debug=True)

