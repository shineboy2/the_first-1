# Elasticsearch Airline System - Access Information

## ✈️ Status: Elasticsearch Cluster Running

### 📊 Access Details

**Elasticsearch (Main API)**
- URL: http://localhost:9200
- Username: `elastic`
- Password: `ElasticPass123!`
- Type: HTTP/Basic Auth

**Kibana (Dashboard & Visualization)**
- URL: http://localhost:5601
- Username: `elastic`
- Password: `ElasticPass123!`
- Use Kibana to visualize and analyze airline data

### 🗂️ Available Indices

1. **flights** (20 documents)
   - flight_number: Flight identifier (e.g., IR1000, IR1001)
   - airline: Airline name
   - departure_airport: Departure airport code (IKA, THR, etc)
   - arrival_airport: Arrival airport code
   - departure_time: Scheduled departure time
   - arrival_time: Scheduled arrival time
   - aircraft_type: Aircraft model (A380, A350, B787, A320, B737)
   - capacity: Total seats
   - available_seats: Remaining available seats
   - status: Flight status (scheduled, on-time, delayed, boarding)
   - price: Ticket price

2. **passengers** (50 documents)
   - passenger_id: Unique identifier
   - first_name: First name
   - last_name: Last name
   - email: Email address
   - phone: Phone number
   - nationality: Passenger nationality
   - passport_number: Passport ID
   - date_of_birth: Birth date
   - total_flights: Number of flights taken

3. **reservations** (100 documents)
   - reservation_id: Booking reference
   - flight_number: Associated flight
   - passenger_name: Passenger name
   - passenger_email: Passenger email
   - booking_date: Date of booking
   - status: Reservation status (confirmed, cancelled, completed)
   - seat_number: Assigned seat
   - price_paid: Amount paid for ticket

### 🔌 Connection Examples

**Using curl:**
```bash
# List flights
curl -u elastic:ElasticPass123! -X GET "localhost:9200/flights/_search?size=100"

# Search for a specific flight
curl -u elastic:ElasticPass123! -X GET "localhost:9200/flights/_search" -H 'Content-Type: application/json' -d '{
  "query": {
    "match": {
      "airline": "Iran Air"
    }
  }
}'

# Get reservation statistics
curl -u elastic:ElasticPass123! -X GET "localhost:9200/reservations/_stats"
```

**Using Python:**
```python
import requests
from requests.auth import HTTPBasicAuth

ES_URL = "http://localhost:9200"
auth = HTTPBasicAuth("elastic", "ElasticPass123!")

# Search flights
response = requests.get(
    f"{ES_URL}/flights/_search?size=10",
    auth=auth
)
flights = response.json()["hits"]["hits"]
```

**Using JavaScript/Node.js:**
```javascript
const { Client } = require('@elastic/elasticsearch');

const client = new Client({
  node: 'http://localhost:9200',
  auth: {
    username: 'elastic',
    password: 'ElasticPass123!'
  }
});

// Search flights
const response = await client.search({
  index: 'flights',
  size: 10
});
```

### 🛠️ Docker Commands

```bash
# View running containers
docker ps

# View logs
docker-compose -f docker-compose.elasticsearch.yml logs -f elasticsearch
docker-compose -f docker-compose.elasticsearch.yml logs -f kibana

# Stop services
docker-compose -f docker-compose.elasticsearch.yml down

# Remove volumes (reset data)
docker-compose -f docker-compose.elasticsearch.yml down -v
```

### 📈 Sample Kibana Queries

1. **Total flights today**
   ```
   GET /flights/_count
   ```

2. **Average ticket price**
   ```
   GET /flights/_search
   {
     "aggs": {
       "avg_price": {
         "avg": {
           "field": "price"
         }
       }
     }
   }
   ```

3. **Reservations by status**
   ```
   GET /reservations/_search
   {
     "aggs": {
       "status_count": {
         "terms": {
           "field": "status"
         }
       }
     }
   }
   ```

4. **Flights by airline**
   ```
   GET /flights/_search
   {
     "aggs": {
       "airlines": {
         "terms": {
           "field": "airline"
         }
       }
     }
   }
   ```

### 🚀 Next Steps

1. Open Kibana at http://localhost:5601
2. Create index patterns for visualization
3. Build dashboards to monitor:
   - Flight availability
   - Reservation trends
   - Revenue analysis
   - Occupancy rates

---

**System Created:** April 18, 2026
**Elasticsearch Version:** 8.11.0
**Data Locale:** Airline Reservation System
