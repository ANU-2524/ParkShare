# ParkShare API Documentation

## Overview
ParkShare provides RESTful API endpoints for traffic management, parking suggestions, and earnings analytics.

---

## Base URL
```
http://localhost:5000
```

---

## API Endpoints

### 1. Traffic Status API

#### Get Traffic Status for Area
```
GET /api/traffic_status/<area_name>
```

**Description**: Get current traffic status for a specific parking area.

**Parameters**:
- `area_name` (string, required): Name of the traffic area (e.g., "Market Square")

**Response**:
```json
{
  "status": "high",
  "color": "orange",
  "percentage": 82.5,
  "is_full": false
}
```

**Status Levels**:
- `"low"` - Green indicator (0-49% occupancy)
- `"medium"` - Yellow indicator (50-79% occupancy)
- `"high"` - Orange indicator (80-99% occupancy)
- `"blocked"` - Red indicator (100% occupancy)

**Color Values**:
- `"green"` - Plenty of parking
- `"yellow"` - Moderate traffic
- `"orange"` - High traffic
- `"red"` - Area full

**Example Request**:
```bash
curl http://localhost:5000/api/traffic_status/Market%20Square
```

**Example Response**:
```json
{
  "status": "high",
  "color": "orange",
  "percentage": 80.0,
  "is_full": false
}
```

---

### 2. Nearby Parking Suggestions

#### Get Nearby Parking
```
GET /api/nearby_parking
```

**Description**: Find available private parking near a location.

**Query Parameters**:
- `lat` (float, required): Latitude of search point
- `lon` (float, required): Longitude of search point
- `area` (string, optional): Area name for context
- `radius` (float, optional): Search radius in km (default: 5)

**Response**:
```json
[
  {
    "id": 1,
    "title": "Spacious Driveway",
    "location": "Market Square",
    "rate": 5.0,
    "distance": 0.8,
    "lat": 40.7180,
    "lon": -73.9850,
    "host": "john_smith"
  },
  {
    "id": 2,
    "title": "Garage Downtown",
    "location": "Downtown Center",
    "rate": 4.0,
    "distance": 1.2,
    "lat": 40.7200,
    "lon": -73.9900,
    "host": "jane_doe"
  }
]
```

**Example Request**:
```bash
curl "http://localhost:5000/api/nearby_parking?lat=40.7128&lon=-74.0060&area=Market%20Square&radius=5"
```

**Error Responses**:
```json
{
  "error": "Missing coordinates"
}
```

---

### 3. Earnings API

#### Get Listing Earnings
```
GET /api/earnings/<listing_id>
```

**Description**: Get earnings information for a specific listing. Requires authentication.

**Parameters**:
- `listing_id` (integer, required): ID of the listing

**Authentication**: 
- Required: User must be logged in and own the listing
- Method: Flask-Login session

**Response**:
```json
{
  "listing_id": 1,
  "total_earnings": 1850.50,
  "total_bookings": 37,
  "total_hours": 370.0,
  "average_rate": 5.0
}
```

**Example Request**:
```bash
curl -H "Cookie: session=..." http://localhost:5000/api/earnings/1
```

**Error Responses**:
```json
{
  "error": "Unauthorized"
}
```
(Status: 403 Forbidden)

---

### 4. All Traffic Areas

#### Get All Traffic Areas
```
GET /api/all_traffic_areas
```

**Description**: Get status of all monitored traffic areas.

**Response**:
```json
[
  {
    "id": 1,
    "name": "Market Square",
    "lat": 40.7128,
    "lon": -74.0060,
    "occupancy": 80.0,
    "status": "high",
    "color": "orange",
    "is_full": false
  },
  {
    "id": 2,
    "name": "Downtown Center",
    "lat": 40.7255,
    "lon": -73.9983,
    "occupancy": 50.0,
    "status": "medium",
    "color": "yellow",
    "is_full": false
  },
  {
    "id": 3,
    "name": "Airport District",
    "lat": 40.7700,
    "lon": -73.8740,
    "occupancy": 25.0,
    "status": "low",
    "color": "green",
    "is_full": false
  }
]
```

**Example Request**:
```bash
curl http://localhost:5000/api/all_traffic_areas
```

---

## Web Routes (Non-API)

### Authentication
- `GET /register` - Registration page
- `POST /register` - Create new account
- `GET /login` - Login page
- `POST /login` - Authenticate user
- `GET /logout` - Logout (requires auth)

### Listing Management
- `GET /create_listing` - Create listing form (host only)
- `POST /create_listing` - Submit new listing (host only)
- `POST /delete_listing/<id>` - Delete listing (host only)
- `GET /dashboard` - Host dashboard (host only)

### Booking Management
- `GET /search` - Search for parking
- `GET /book/<listing_id>` - Booking form
- `POST /book/<listing_id>` - Create booking
- `GET /payment/<booking_id>` - Payment confirmation
- `POST /payment/<booking_id>` - Process payment
- `POST /cancel_booking/<booking_id>` - Cancel booking
- `GET /history` - Booking history (auth required)

### User Management
- `GET /profile` - User profile page (auth required)
- `POST /profile` - Update profile (auth required)
- `POST /toggle_favorite/<listing_id>` - Add/remove favorite (auth required)
- `POST /add_review/<listing_id>` - Add review (auth required)

### Pages
- `GET /` - Home page with search
- `GET /index.html` (same as above)

---

## Data Models

### Traffic Area
```json
{
  "id": 1,
  "name": "Market Square",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "max_capacity": 50,
  "current_occupancy": 40,
  "is_full": false,
  "congestion_level": "high",
  "updated_at": "2026-01-28T10:30:00"
}
```

### Listing
```json
{
  "id": 1,
  "title": "Spacious Driveway",
  "location": "Market Square",
  "hourly_rate": 5.0,
  "description": "Large driveway, well-lit, secure",
  "latitude": 40.7180,
  "longitude": -73.9850,
  "host_id": 1,
  "amenities": ["EV Charging", "CCTV"],
  "reviews": [...]
}
```

### Booking
```json
{
  "id": 1,
  "start_time": "2026-01-28T10:00:00",
  "end_time": "2026-01-28T14:00:00",
  "total_price": 20.0,
  "status": "confirmed",
  "payment_status": "paid",
  "user_id": 2,
  "listing_id": 1,
  "created_at": "2026-01-28T09:45:00"
}
```

---

## Error Handling

### HTTP Status Codes
- `200 OK` - Successful request
- `400 Bad Request` - Missing or invalid parameters
- `403 Forbidden` - User not authorized
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
  "error": "Error message description"
}
```

### Common Errors

**Missing Coordinates**:
```json
{
  "error": "Missing coordinates"
}
```
Status: 400

**Unauthorized Access**:
```json
{
  "error": "Unauthorized"
}
```
Status: 403

---

## Rate Limiting
Currently no rate limiting implemented. Production deployment should include:
- Per-IP rate limiting (100 requests/minute)
- Per-user rate limiting (1000 requests/hour)
- API key management

---

## Authentication

### Session-Based Authentication
- Uses Flask-Login
- Sessions stored in browser cookies
- Automatically managed by `@login_required` decorator

### Protected Endpoints
Endpoints requiring `@login_required`:
- All dashboard routes
- All booking management routes
- Profile management
- Earnings API

### Example with Authentication
```bash
# Login first
curl -c cookies.txt -d "email=user@example.com&password=pass" \
  http://localhost:5000/login

# Use session cookie for protected endpoint
curl -b cookies.txt http://localhost:5000/api/earnings/1
```

---

## Request/Response Examples

### Example 1: Get Traffic Status
```bash
Request:
GET /api/traffic_status/Market%20Square HTTP/1.1
Host: localhost:5000

Response:
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "high",
  "color": "orange",
  "percentage": 80.0,
  "is_full": false
}
```

### Example 2: Find Nearby Parking
```bash
Request:
GET /api/nearby_parking?lat=40.7128&lon=-74.0060&radius=5 HTTP/1.1
Host: localhost:5000

Response:
HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "id": 1,
    "title": "Spacious Driveway",
    "location": "Market Square",
    "rate": 5.0,
    "distance": 0.8,
    "lat": 40.7180,
    "lon": -73.9850,
    "host": "john_smith"
  }
]
```

### Example 3: Get Earnings (With Auth)
```bash
Request:
GET /api/earnings/1 HTTP/1.1
Host: localhost:5000
Cookie: session=xxxxx

Response:
HTTP/1.1 200 OK
Content-Type: application/json

{
  "listing_id": 1,
  "total_earnings": 1850.50,
  "total_bookings": 37,
  "total_hours": 370.0,
  "average_rate": 5.0
}
```

---

## WebSocket Support
Not implemented in current version. Future enhancement for real-time updates:
- Live traffic status updates
- Instant booking notifications
- Real-time earnings updates

---

## CORS (Cross-Origin Resource Sharing)
Not configured in current version. For frontend integration from different origins, add:
```python
from flask_cors import CORS
CORS(app)
```

---

## API Versioning
Current version: v1 (no versioning prefix in URLs)

Future versions should use:
- `/api/v2/traffic_status/<area_name>`
- `/api/v2/nearby_parking`
- etc.

---

## Pagination
Not implemented. Future enhancement for large result sets:
```
GET /api/nearby_parking?lat=40.7128&lon=-74.0060&page=1&limit=10
```

---

## Filtering & Sorting
Current implementation supports basic filtering in web routes. API endpoints could be enhanced with:
```
GET /api/nearby_parking?lat=40.7128&lon=-74.0060&min_rate=3&max_rate=7&sort=distance
```

---

## Caching Strategy
For production, implement caching:
- Traffic status (cache 5 minutes)
- Nearby parking (cache 10 minutes)
- Earnings data (cache 30 minutes)

```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/traffic_status/<area_name>')
@cache.cached(timeout=300)
def api_traffic_status(area_name):
    ...
```

---

## Testing Examples

### Using curl
```bash
# Test traffic status
curl -X GET http://localhost:5000/api/traffic_status/Market%20Square

# Test nearby parking
curl -X GET "http://localhost:5000/api/nearby_parking?lat=40.7128&lon=-74.0060"

# Test all traffic areas
curl -X GET http://localhost:5000/api/all_traffic_areas
```

### Using Python requests
```python
import requests

# Traffic status
response = requests.get('http://localhost:5000/api/traffic_status/Market Square')
print(response.json())

# Nearby parking
params = {'lat': 40.7128, 'lon': -74.0060, 'radius': 5}
response = requests.get('http://localhost:5000/api/nearby_parking', params=params)
print(response.json())
```

### Using JavaScript fetch
```javascript
// Traffic status
fetch('/api/traffic_status/Market%20Square')
  .then(r => r.json())
  .then(data => console.log(data));

// Nearby parking
const params = new URLSearchParams({
  lat: 40.7128,
  lon: -74.0060,
  radius: 5
});
fetch('/api/nearby_parking?' + params)
  .then(r => r.json())
  .then(data => console.log(data));
```

---

## Changelog

### Version 1.0 (January 28, 2026)
- Initial API implementation
- Traffic status endpoint
- Nearby parking suggestions
- Earnings API
- All traffic areas endpoint

### Planned Enhancements
- WebSocket real-time updates
- Advanced filtering & sorting
- Pagination support
- Rate limiting
- API authentication tokens
- Webhooks for external integrations

---

**Last Updated**: January 28, 2026
**Status**: Production Ready
**Support**: GitHub Issues
