#!/usr/bin/env python3
"""
Seed Elasticsearch with sample airline data
"""

import json
import requests
from datetime import datetime, timedelta
import random

# Elasticsearch configuration
ES_HOST = "http://192.168.214.139:9200"
ES_USER = "elastic"
ES_PASSWORD = "ElasticPass123!"

# API headers
headers = {
    "Content-Type": "application/json",
}

auth = (ES_USER, ES_PASSWORD)

# Sample airlines
AIRLINES = [
    {"id": "IR", "name": "Iran Air", "country": "Iran"},
    {"id": "W5", "name": "Wizz Air", "country": "Hungary"},
    {"id": "TU", "name": "Turkmenistan Airlines", "country": "Turkmenistan"},
    {"id": "FV", "name": "Fly Vayu", "country": "India"},
]

# Sample airports
AIRPORTS = [
    {"code": "IKA", "name": "Imam Khomeini International", "city": "Tehran", "country": "Iran"},
    {"code": "THR", "name": "Mehrabad International", "city": "Tehran", "country": "Iran"},
    {"code": "MHD", "name": "Mashhad International", "city": "Mashhad", "country": "Iran"},
    {"code": "ISF", "name": "Isfahan International", "city": "Isfahan", "country": "Iran"},
    {"code": "AMS", "name": "Amsterdam Airport Schiphol", "city": "Amsterdam", "country": "Netherlands"},
    {"code": "CDG", "name": "Charles de Gaulle", "city": "Paris", "country": "France"},
    {"code": "DXB", "name": "Dubai International", "city": "Dubai", "country": "UAE"},
    {"code": "JFK", "name": "John F. Kennedy", "city": "New York", "country": "USA"},
]

# Aircraft types
AIRCRAFT = [
    {"code": "A380", "name": "Airbus A380"},
    {"code": "A350", "name": "Airbus A350"},
    {"code": "B787", "name": "Boeing 787"},
    {"code": "A320", "name": "Airbus A320"},
    {"code": "B737", "name": "Boeing 737"},
]

def create_indices():
    """Create Elasticsearch indices"""
    indices = {
        "flights": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "flight_number": {"type": "keyword"},
                    "airline": {"type": "keyword"},
                    "departure_airport": {"type": "keyword"},
                    "arrival_airport": {"type": "keyword"},
                    "departure_time": {"type": "date"},
                    "arrival_time": {"type": "date"},
                    "aircraft_type": {"type": "keyword"},
                    "capacity": {"type": "integer"},
                    "available_seats": {"type": "integer"},
                    "status": {"type": "keyword"},
                    "price": {"type": "float"}
                }
            }
        },
        "reservations": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "reservation_id": {"type": "keyword"},
                    "flight_number": {"type": "keyword"},
                    "passenger_name": {"type": "text"},
                    "passenger_email": {"type": "keyword"},
                    "booking_date": {"type": "date"},
                    "status": {"type": "keyword"},
                    "seat_number": {"type": "keyword"},
                    "price_paid": {"type": "float"}
                }
            }
        },
        "passengers": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "passenger_id": {"type": "keyword"},
                    "first_name": {"type": "text"},
                    "last_name": {"type": "text"},
                    "email": {"type": "keyword"},
                    "phone": {"type": "keyword"},
                    "nationality": {"type": "keyword"},
                    "passport_number": {"type": "keyword"},
                    "date_of_birth": {"type": "date"},
                    "total_flights": {"type": "integer"}
                }
            }
        }
    }
    
    for index_name, index_config in indices.items():
        resp = requests.put(f"{ES_HOST}/{index_name}", json=index_config, auth=auth, headers=headers)
        print(f"Created index '{index_name}': {resp.status_code} - {resp.json().get('acknowledged')}")

def seed_flights():
    """Seed flight data"""
    flights = []
    flight_id = 1000
    
    for _ in range(20):
        airline = random.choice(AIRLINES)
        dep_airport = random.choice(AIRPORTS)
        arr_airport = random.choice([a for a in AIRPORTS if a["code"] != dep_airport["code"]])
        aircraft = random.choice(AIRCRAFT)
        
        departure_time = datetime.utcnow() + timedelta(hours=random.randint(1, 168))
        arrival_time = departure_time + timedelta(hours=random.randint(1, 14))
        
        flight = {
            "flight_number": f"{airline['id']}{flight_id}",
            "airline": airline["name"],
            "departure_airport": dep_airport["code"],
            "arrival_airport": arr_airport["code"],
            "departure_time": departure_time.isoformat() + "Z",
            "arrival_time": arrival_time.isoformat() + "Z",
            "aircraft_type": aircraft["code"],
            "capacity": random.choice([300, 350, 416, 180, 200]),
            "available_seats": random.randint(10, 100),
            "status": random.choice(["scheduled", "on-time", "delayed", "boarding"]),
            "price": round(random.uniform(100, 1000), 2)
        }
        
        flights.append(flight)
        flight_id += 1
    
    # Bulk insert
    bulk_data = ""
    for flight in flights:
        bulk_data += json.dumps({"index": {"_index": "flights"}}) + "\n"
        bulk_data += json.dumps(flight) + "\n"
    
    resp = requests.post(f"{ES_HOST}/_bulk", data=bulk_data, auth=auth, headers=headers)
    print(f"Seeded {len(flights)} flights: {resp.status_code}")

def seed_passengers():
    """Seed passenger data"""
    first_names = ["Ali", "Fatima", "Hassan", "Zahra", "Mohammad", "Amir", "Sara", "Reza", "Layla", "Karim"]
    last_names = ["Ahmadi", "Rezaei", "Karimi", "Hosseini", "Sadegh", "Mohammadi", "Nazari", "Saleh", "Vakili", "Bahar"]
    nationalities = ["Iranian", "Turkish", "Indian", "British", "American", "French", "German", "Dutch"]
    
    passengers = []
    for i in range(50):
        passenger = {
            "passenger_id": f"P{1000 + i}",
            "first_name": random.choice(first_names),
            "last_name": random.choice(last_names),
            "email": f"passenger{1000+i}@airline.com",
            "phone": f"+98{random.randint(900000000, 999999999)}",
            "nationality": random.choice(nationalities),
            "passport_number": f"P{random.randint(1000000, 9999999)}",
            "date_of_birth": (datetime.utcnow() - timedelta(days=random.randint(6570, 27375))).isoformat() + "Z",
            "total_flights": random.randint(0, 50)
        }
        passengers.append(passenger)
    
    # Bulk insert
    bulk_data = ""
    for passenger in passengers:
        bulk_data += json.dumps({"index": {"_index": "passengers"}}) + "\n"
        bulk_data += json.dumps(passenger) + "\n"
    
    resp = requests.post(f"{ES_HOST}/_bulk", data=bulk_data, auth=auth, headers=headers)
    print(f"Seeded {len(passengers)} passengers: {resp.status_code}")

def seed_reservations():
    """Seed reservation data"""
    reservations = []
    
    # Hardcoded flight numbers to match seeded flights
    flight_numbers = [f"IR{1000+i}" for i in range(20)]
    
    for i in range(100):
        flight_num = random.choice(flight_numbers)
        reservation = {
            "reservation_id": f"RES{10000 + i}",
            "flight_number": flight_num,
            "passenger_name": f"Passenger {i+1}",
            "passenger_email": f"passenger{i+1}@airline.com",
            "booking_date": (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat() + "Z",
            "status": random.choice(["confirmed", "cancelled", "completed"]),
            "seat_number": f"{random.choice(list('ABCDEF'))}{random.randint(1, 50)}",
            "price_paid": round(random.uniform(50, 800), 2)
        }
        reservations.append(reservation)
    
    # Bulk insert
    bulk_data = ""
    for reservation in reservations:
        bulk_data += json.dumps({"index": {"_index": "reservations"}}) + "\n"
        bulk_data += json.dumps(reservation) + "\n"
    
    resp = requests.post(f"{ES_HOST}/_bulk", data=bulk_data, auth=auth, headers=headers)
    print(f"Seeded {len(reservations)} reservations: {resp.status_code}")

def main():
    print("🌍 Seeding airline data to Elasticsearch...\n")
    
    # Create indices
    print("📋 Creating indices...")
    create_indices()
    print()
    
    # Seed data
    print("✈️ Seeding flights...")
    seed_flights()
    print()
    
    print("👥 Seeding passengers...")
    seed_passengers()
    print()
    
    print("🎫 Seeding reservations...")
    seed_reservations()
    print()
    
    # Verify
    print("✅ Verifying data...")
    for index in ["flights", "passengers", "reservations"]:
        stats = requests.get(f"{ES_HOST}/{index}/_stats", auth=auth).json()
        count = stats["indices"][index]["primaries"]["docs"]["count"]
        print(f"  {index}: {count} documents")

if __name__ == "__main__":
    main()
