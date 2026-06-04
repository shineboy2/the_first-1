#!/usr/bin/env python
"""
Setup Elasticsearch indices and populate with mock airline data.

Indices:
1. flights - Flight information
2. seats - Available seats for each flight
3. customers - Customer information
4. bookings - Booking records
"""

import asyncio
import json
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import random
import logging
import ssl
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Elasticsearch connection
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

def create_es_client(verify_ssl=False):
    """
    Create Elasticsearch client.
    
    Args:
        verify_ssl: Whether to verify SSL certificate (default: False)
    """
    try:
        # Try to get runtime config from database
        from db.session import SessionLocal
        from models.elasticsearch_config import ElasticsearchConfig
        
        db = SessionLocal()
        config = db.query(ElasticsearchConfig).filter(
            ElasticsearchConfig.is_active == True
        ).first()
        db.close()
        
        if config:
            logger.info(f"Using runtime Elasticsearch config: {config.url}")
            kwargs = {"hosts": [config.url]}
            if config.username and config.password:
                kwargs["basic_auth"] = (config.username, config.password)
            kwargs["verify_certs"] = config.verify_ssl
            return Elasticsearch(**kwargs)
    except Exception as e:
        logger.warning(f"Failed to load runtime Elasticsearch config: {e}")
    
    # Fallback to ES_URL with verify_ssl parameter
    kwargs = {"hosts": [ES_URL]}
    kwargs["verify_certs"] = verify_ssl
    return Elasticsearch(**kwargs)

def setup_indices():
    """Create indices with proper mappings."""
    client = create_es_client()
    
    # 1. Flights Index
    flights_mapping = {
        "mappings": {
            "properties": {
                "flight_number": {"type": "keyword"},
                "airline": {"type": "keyword"},
                "departure_airport": {"type": "keyword"},
                "arrival_airport": {"type": "keyword"},
                "departure_time": {"type": "date"},
                "arrival_time": {"type": "date"},
                "aircraft_type": {"type": "keyword"},
                "total_seats": {"type": "integer"},
                "available_seats": {"type": "integer"},
                "status": {"type": "keyword"},  # scheduled, boarding, departed, landed, cancelled
                "price_economy": {"type": "float"},
                "price_business": {"type": "float"},
                "created_at": {"type": "date"}
            }
        }
    }
    
    # 2. Seats Index
    seats_mapping = {
        "mappings": {
            "properties": {
                "flight_number": {"type": "keyword"},
                "seat_number": {"type": "keyword"},
                "seat_class": {"type": "keyword"},  # economy, business, first
                "status": {"type": "keyword"},  # available, occupied, reserved
                "customer_id": {"type": "keyword"},
                "booking_id": {"type": "keyword"},
                "created_at": {"type": "date"}
            }
        }
    }
    
    # 3. Customers Index
    customers_mapping = {
        "mappings": {
            "properties": {
                "customer_id": {"type": "keyword"},
                "first_name": {"type": "text"},
                "last_name": {"type": "text"},
                "email": {"type": "keyword"},
                "phone": {"type": "keyword"},
                "nationality": {"type": "keyword"},
                "passport_number": {"type": "keyword"},
                "date_of_birth": {"type": "date"},
                "created_at": {"type": "date"}
            }
        }
    }
    
    # 4. Bookings Index
    bookings_mapping = {
        "mappings": {
            "properties": {
                "booking_id": {"type": "keyword"},
                "customer_id": {"type": "keyword"},
                "flight_number": {"type": "keyword"},
                "seat_number": {"type": "keyword"},
                "booking_status": {"type": "keyword"},  # confirmed, pending, cancelled
                "booking_date": {"type": "date"},
                "seat_class": {"type": "keyword"},
                "price": {"type": "float"},
                "payment_status": {"type": "keyword"},  # paid, pending, refunded
                "created_at": {"type": "date"}
            }
        }
    }
    
    # Create indices
    for index_name, mapping in [
        ("flights", flights_mapping),
        ("seats", seats_mapping),
        ("customers", customers_mapping),
        ("bookings", bookings_mapping)
    ]:
        try:
            if client.indices.exists(index=index_name):
                client.indices.delete(index=index_name)
                print(f"🗑️  Deleted existing index: {index_name}")
            
            client.indices.create(index=index_name, body=mapping)
            print(f"✅ Created index: {index_name}")
        except Exception as e:
            print(f"❌ Error creating index {index_name}: {e}")

def populate_mock_data():
    """Populate Elasticsearch with mock airline data."""
    client = create_es_client()
    
    # Flight data
    flights = [
        {
            "flight_number": "AY101",
            "airline": "Airway Airlines",
            "departure_airport": "TRZ",
            "arrival_airport": "IKA",
            "departure_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "arrival_time": (datetime.utcnow() + timedelta(days=1, hours=4)).isoformat(),
            "aircraft_type": "Boeing 737",
            "total_seats": 180,
            "available_seats": 45,
            "status": "scheduled",
            "price_economy": 150.0,
            "price_business": 350.0,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "flight_number": "AY202",
            "airline": "Airway Airlines",
            "departure_airport": "IKA",
            "arrival_airport": "TRZ",
            "departure_time": (datetime.utcnow() + timedelta(days=1, hours=5)).isoformat(),
            "arrival_time": (datetime.utcnow() + timedelta(days=1, hours=9)).isoformat(),
            "aircraft_type": "Airbus A320",
            "total_seats": 210,
            "available_seats": 78,
            "status": "scheduled",
            "price_economy": 160.0,
            "price_business": 380.0,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "flight_number": "AY303",
            "airline": "Airway Airlines",
            "departure_airport": "TRZ",
            "arrival_airport": "DXB",
            "departure_time": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "arrival_time": (datetime.utcnow() + timedelta(days=2, hours=5)).isoformat(),
            "aircraft_type": "Boeing 787",
            "total_seats": 242,
            "available_seats": 120,
            "status": "scheduled",
            "price_economy": 200.0,
            "price_business": 450.0,
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Customer data
    customers = [
        {
            "customer_id": "CUST001",
            "first_name": "علی",
            "last_name": "محمدی",
            "email": "ali.mohammadi@email.com",
            "phone": "+989123456789",
            "nationality": "IR",
            "passport_number": "N12345678",
            "date_of_birth": "1990-01-15",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "customer_id": "CUST002",
            "first_name": "فاطمه",
            "last_name": "علوی",
            "email": "fatima.alavi@email.com",
            "phone": "+989198765432",
            "nationality": "IR",
            "passport_number": "N87654321",
            "date_of_birth": "1992-05-22",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "customer_id": "CUST003",
            "first_name": "حسن",
            "last_name": "رضایی",
            "email": "hassan.rezaei@email.com",
            "phone": "+989136547890",
            "nationality": "IR",
            "passport_number": "N55555555",
            "date_of_birth": "1985-11-30",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "customer_id": "CUST004",
            "first_name": "سارا",
            "last_name": "کریمی",
            "email": "sara.karimi@email.com",
            "phone": "+989145678901",
            "nationality": "IR",
            "passport_number": "N66666666",
            "date_of_birth": "1995-03-18",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "customer_id": "CUST005",
            "first_name": "محمد",
            "last_name": "حسینی",
            "email": "mohammad.hosseini@email.com",
            "phone": "+989167890123",
            "nationality": "IR",
            "passport_number": "N77777777",
            "date_of_birth": "1988-07-25",
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Booking data
    bookings = [
        {
            "booking_id": "BK001",
            "customer_id": "CUST001",
            "flight_number": "AY101",
            "seat_number": "12A",
            "booking_status": "confirmed",
            "booking_date": (datetime.utcnow() - timedelta(days=5)).isoformat(),
            "seat_class": "economy",
            "price": 150.0,
            "payment_status": "paid",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "booking_id": "BK002",
            "customer_id": "CUST002",
            "flight_number": "AY101",
            "seat_number": "12B",
            "booking_status": "confirmed",
            "booking_date": (datetime.utcnow() - timedelta(days=3)).isoformat(),
            "seat_class": "economy",
            "price": 150.0,
            "payment_status": "paid",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "booking_id": "BK003",
            "customer_id": "CUST003",
            "flight_number": "AY202",
            "seat_number": "1A",
            "booking_status": "confirmed",
            "booking_date": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "seat_class": "business",
            "price": 380.0,
            "payment_status": "paid",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "booking_id": "BK004",
            "customer_id": "CUST004",
            "flight_number": "AY303",
            "seat_number": "5C",
            "booking_status": "pending",
            "booking_date": datetime.utcnow().isoformat(),
            "seat_class": "economy",
            "price": 200.0,
            "payment_status": "pending",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "booking_id": "BK005",
            "customer_id": "CUST005",
            "flight_number": "AY303",
            "seat_number": "5D",
            "booking_status": "confirmed",
            "booking_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "seat_class": "economy",
            "price": 200.0,
            "payment_status": "paid",
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Populate flights
    print("\n📝 Populating Flights...")
    for i, flight in enumerate(flights):
        client.index(index="flights", id=flight["flight_number"], document=flight)
        print(f"   ✅ Flight {flight['flight_number']} indexed")
    
    # Populate customers
    print("\n👥 Populating Customers...")
    for i, customer in enumerate(customers):
        client.index(index="customers", id=customer["customer_id"], document=customer)
        print(f"   ✅ Customer {customer['customer_id']} indexed")
    
    # Populate bookings
    print("\n📅 Populating Bookings...")
    for i, booking in enumerate(bookings):
        client.index(index="bookings", id=booking["booking_id"], document=booking)
        print(f"   ✅ Booking {booking['booking_id']} indexed")
    
    # Generate seats for flights
    print("\n🪑 Populating Seats...")
    seat_classes = {
        "economy": 150,
        "business": 30
    }
    
    for flight in flights:
        seat_id = 1
        for seat_class, count in seat_classes.items():
            for i in range(1, count + 1):
                row = (i - 1) // 6 + 1
                col_letter = chr(65 + (i - 1) % 6)  # A-F
                seat_number = f"{row}{col_letter}"
                
                seat_doc = {
                    "flight_number": flight["flight_number"],
                    "seat_number": seat_number,
                    "seat_class": seat_class,
                    "status": "available",
                    "customer_id": None,
                    "booking_id": None,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                client.index(index="seats", document=seat_doc)
                seat_id += 1
        
        print(f"   ✅ {flight['flight_number']}: {len(seat_classes) * sum(seat_classes.values())} seats created")
    
    print("\n🔄 Refreshing indices...")
    for index in ["flights", "customers", "bookings", "seats"]:
        client.indices.refresh(index=index)
    
    print("\n✅ All data populated successfully!")

if __name__ == "__main__":
    print("🚀 Setting up Elasticsearch for Airline System\n")
    
    try:
        print("1️⃣  Creating indices...")
        setup_indices()
        
        print("\n2️⃣  Populating mock data...")
        populate_mock_data()
        
        print("\n" + "="*50)
        print("✅ Elasticsearch setup completed!")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Error: {e}")
