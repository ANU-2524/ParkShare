"This project was developed during the Winter Internship '25 at console.success."

# ParkShare - Community Parking & Traffic Routing System

## 🚗 Project Overview

**ParkShare** is a revolutionary web application designed to solve the urban parking crisis by connecting drivers with homeowners who have empty parking spaces. The system also acts as an intelligent traffic router, directing users away from congested areas and suggesting available private parking nearby.

### Key Problems Solved
- **Urban Parking Crisis**: Drivers spend significant time looking for parking in congested areas
- **Traffic Congestion**: Unnecessary circling in full parking zones increases emissions and frustration
- **Lost Income Opportunity**: Homeowners can't monetize their unused driveway/garage spaces
- **Information Gap**: Drivers lack real-time visibility into parking availability

---

## 🎯 Core Features

### 1. **Host & Space Registration**
- Property owners ("Hosts") can register and list their empty parking spaces
- Configure space details:
  - **Location**: Precise geographic coordinates (latitude/longitude)
  - **Hourly Rate**: Set custom pricing for your space
  - **Amenities**: Add features like EV Charging, CCTV, Covered Parking, 24/7 Access
  - **Description**: Detailed space information for drivers
  - **Time Slots**: Manage available booking windows

### 2. **Smart Availability & Routing Logic**

#### The "Full" Check
- System monitors parking occupancy in major urban areas
- Real-time status shows: **GREEN** (available), **YELLOW** (moderate occupancy), **ORANGE** (high occupancy), **RED** (full/blocked)
- Pre-configured traffic areas include: Market Square, Downtown Center, Airport District, Harbor Front, Tech Park

#### The Re-Route (Auto-Routing)
- When a public parking area reaches 75%+ occupancy, the system automatically triggers smart routing
- **Intelligent Algorithm**:
  - Calculates distances using Haversine formula (realistic geographic distance)
  - Finds nearest available private parking spots within 5km radius
  - Ranks suggestions by proximity (closest first)
  - Shows host information and real-time availability
- **Visual Reroute Card** displays:
  - Space location and amenities
  - Hourly rate
  - Distance from congested area
  - Host name and rating

### 3. **Booking Engine**

#### Reservation System
- Drivers search for available parking in specific areas
- Real-time availability checking prevents double bookings
- Conflict detection ensures time slots don't overlap
- Instant booking confirmation with:
  - Booking ID
  - Duration (hours)
  - Total cost calculation
  - Payment gateway integration

#### Payment Integration
- Secure payment processing
- Automatic status updates (pending → confirmed)
- Payment status tracking (unpaid → paid)
- Refund processing for cancellations

### 4. **Earnings Calculator & Host Dashboard**

#### Comprehensive Dashboard
Hosts see at a glance:
- **💰 Total Earnings**: Sum of all completed bookings
- **📅 Total Bookings**: Number of confirmed reservations
- **⏱️ Hours Booked**: Aggregate parking hours
- **⭐ Average Rating**: Guest review score

#### Per-Listing Analytics
- Individual earnings breakdown for each listing
- Booking history and rates
- Guest reviews and ratings
- Performance insights

#### Features for Income Growth
- Tips for increasing earnings
- Pricing optimization suggestions
- Amenity recommendations
- Response time analytics

---

## 🏗️ System Architecture

### Database Models

```
User
├── Profile information (username, email, phone)
├── Role (Host/Driver)
└── Relationships:
    ├── Listings (for Hosts)
    ├── Bookings (for Drivers)
    └── Reviews (written by user)

Listing
├── Title, Location (name & coordinates)
├── Hourly Rate
├── Host information
├── Amenities (many-to-many)
├── Reviews (one-to-many)
└── Bookings (one-to-many)

Booking
├── Time Slots (start_time, end_time)
├── Total Price (hours × hourly_rate)
├── Status (pending, confirmed, cancelled)
├── Payment Status (unpaid, paid, refunded)
└── Driver & Listing references

TrafficArea (NEW)
├── Name (e.g., "Market Square")
├── Location (latitude, longitude)
├── Max Capacity (public parking spots)
├── Current Occupancy
├── Congestion Level (low, medium, high, blocked)
└── Status computation methods

AvailableSlot (NEW)
├── Listing reference
├── Time window (start, end)
├── Availability flag
└── Booking conflict detection
```

### API Endpoints

#### Traffic & Routing
- `GET /api/traffic_status/<area_name>` - Get current traffic status for an area
- `GET /api/nearby_parking` - Get nearby private parking suggestions
- `GET /api/all_traffic_areas` - Get status of all monitored areas

#### Host Earnings
- `GET /api/earnings/<listing_id>` - Get earnings for a specific listing

### Technology Stack

**Backend**:
- Flask (lightweight Python web framework)
- Flask-SQLAlchemy (ORM for database operations)
- Flask-Login (user authentication)
- SQLite (development database)

**Frontend**:
- HTML5 / Jinja2 templating
- CSS3 (modern glassmorphism design)
- Leaflet.js (interactive mapping)
- Vanilla JavaScript (dynamic interactions)

**Security**:
- Werkzeug password hashing (scrypt)
- Login required decorators
- CSRF protection ready
- Role-based access control

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Modern web browser

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ParkShare
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open browser: `http://localhost:5000`
   - Application initializes database automatically on first run

---

## 📖 User Guide

### For Drivers

1. **Search for Parking**
   - Enter location name (e.g., "Market Square")
   - View traffic status color (RED = full, YELLOW/ORANGE = congested, GREEN = available)
   - Apply filters (price range, amenities)

2. **Smart Reroute Suggestions**
   - If area is full, see "Smart Reroute" cards with nearby options
   - Cards show distance, price, amenities, and host info
   - Click "Book" to reserve a spot

3. **Make a Booking**
   - Select start and end time (no past bookings allowed)
   - See instant cost calculation
   - Proceed to payment

4. **Manage Bookings**
   - View booking history
   - Cancel upcoming bookings (if before start time)
   - Add reviews after parking

### For Hosts

1. **Register as Host**
   - Check "I'm a Host" during registration
   - Verify email address

2. **Create a Listing**
   - Go to Dashboard → "Add New Listing"
   - Enter space details:
     - Title (e.g., "Spacious Driveway near Market")
     - Location (e.g., "Market Square")
     - Coordinates (latitude, longitude) - can use Google Maps
     - Hourly rate (e.g., $5)
     - Description
     - Select amenities
   - Listing goes live immediately

3. **Monitor Earnings**
   - Dashboard shows real-time earnings
   - See total bookings, hours booked, average rating
   - Individual listing breakdown

4. **Manage Listings**
   - View all active listings
   - Delete outdated listings
   - Track bookings per listing

---

## 🗺️ Traffic System Deep Dive

### How Traffic Status Works

1. **Occupancy Calculation**
   ```
   Occupancy % = (Current Bookings / Max Capacity) × 100
   ```

2. **Congestion Levels**
   - 0-49%: **GREEN** - Plenty of parking
   - 50-79%: **YELLOW/ORANGE** - Moderate traffic
   - 80-99%: **ORANGE** - High traffic
   - 100%: **RED** - Area full/blocked

3. **Smart Rerouting Algorithm**
   ```
   When occupancy >= 75%:
   1. Get user's search coordinates
   2. Find all listings within 5km radius
   3. Calculate distance using Haversine formula
   4. Filter available (non-conflicting) bookings
   5. Sort by distance (closest first)
   6. Display top 6 suggestions with distance badges
   ```

### Real-World Example

**Scenario**: Driver searches for parking at "Market Square" (Max capacity: 50 spaces)

**Current Occupancy**: 40 confirmed bookings = 80% full

**System Response**:
1. Shows RED traffic status: "Market Square - HIGH"
2. Displays percentage and warning
3. Automatically triggers Smart Reroute
4. Lists nearby private parking:
   - "Spacious Driveway" - 0.8 km away - $5/hr
   - "Garage Near Market" - 1.2 km away - $4/hr
   - "Covered Spot" - 1.5 km away - $6/hr (with amenities)

Driver saves time by avoiding congestion and finds convenient alternatives!

---

## 💡 Key Algorithms

### 1. Distance Calculation (Haversine Formula)
```python
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin²(delta_lat/2) + cos(lat1) × cos(lat2) × sin²(delta_lon/2)
    c = 2 × asin(√a)
    return R × c
```

### 2. Booking Conflict Detection
```python
Overlapping = Booking.query.filter(
    listing_id == current,
    status != 'cancelled',
    end_time > start_time,
    start_time < end_time
).first()
```

### 3. Earnings Calculation
```python
total_earnings = sum(booking.total_price 
                    for booking in confirmed_bookings)
total_hours = sum((end - start).seconds / 3600 
               for booking in confirmed_bookings)
```

---

## 📊 Expected Outcomes

### User Interface
- ✅ **Search Interface**: Shows RED for full areas and pin maps for available spots
- ✅ **Traffic Indicators**: Color-coded status (RED/ORANGE/YELLOW/GREEN)
- ✅ **Smart Reroute Cards**: Nearby parking with distance, price, amenities
- ✅ **Interactive Map**: Leaflet.js map with listing markers

### Booking System
- ✅ **Reservation Logic**: Prevent double bookings, instant confirmations
- ✅ **Payment Integration**: Pending → Confirmed flow
- ✅ **Cancellation**: Refund processing for future bookings

### Host Dashboard
- ✅ **Earnings Tracking**: Real-time income calculations
- ✅ **Slot Management**: View and organize bookings
- ✅ **Performance Metrics**: Ratings, booking counts, hours booked
- ✅ **Growth Tips**: Suggestions for increasing earnings

---

## 🔐 Security Features

- Password hashing with Werkzeug scrypt
- Login required decorators for protected routes
- User role verification (Host vs. Driver)
- Database transaction safety
- Input validation and sanitization

---

## 🚀 Future Enhancements

1. **Mobile App**: React Native or Flutter mobile application
2. **Real Payment Gateway**: Stripe/PayPal integration
3. **Advanced Analytics**: Host dashboards with charts and trends
4. **SMS/Email Notifications**: Booking confirmations and reminders
5. **In-App Messaging**: Direct host-driver communication
6. **Dispute Resolution**: Rating fairness and refund mediation
7. **Dynamic Pricing**: AI-powered rate suggestions
8. **Vehicle Detection**: IoT parking sensors
9. **Multi-language Support**: Internationalization
10. **Social Features**: Host profiles, verified badges, recommendations

---

## 📝 License

This project is part of the Console.success Open Source initiative.

---

## 👥 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Support

For issues, questions, or suggestions:
- Create an issue on GitHub
- Contact the development team
- Check documentation in project Wiki

---

## ✨ Acknowledgments

Special thanks to:
- Flask community for the excellent framework
- Leaflet.js for mapping capabilities
- Open Street Map for geographic data
- Console.success program for the opportunity

---

**Made with ❤️ for the urban mobility community**
