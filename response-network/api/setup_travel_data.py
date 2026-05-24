#!/usr/bin/env python
"""
Setup Elasticsearch indices for Travel Agency System.

Creates and populates indices:
1. customers - Customer profiles (مشتریان)
2. airlines - Airline information (خطوط هوایی)
3. flights - Flight schedules (پرواز‌ها)
4. reservations - Booking records (رزروها)
5. tickets - Issued tickets (بلیط‌ها)
"""

import json
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import random
import uuid
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Elasticsearch connection
ES_URL = "http://localhost:9200"

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
    """Create indices with proper mappings for travel agency."""
    client = create_es_client()
    
    # 1. Customers Index (مشتریان)
    customers_mapping = {
        "mappings": {
            "properties": {
                "customer_id": {"type": "keyword"},
                "first_name": {"type": "text"},
                "last_name": {"type": "text"},
                "full_name": {"type": "text"},
                "email": {"type": "keyword"},
                "phone": {"type": "keyword"},
                "passport_number": {"type": "keyword"},
                "national_id": {"type": "keyword"},
                "nationality": {"type": "keyword"},
                "date_of_birth": {"type": "date"},
                "loyalty_tier": {"type": "keyword"},  # bronze, silver, gold, platinum
                "total_bookings": {"type": "integer"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        }
    }
    
    # 2. Airlines Index (خطوط هوایی)
    airlines_mapping = {
        "mappings": {
            "properties": {
                "airline_code": {"type": "keyword"},
                "airline_name": {"type": "text"},
                "airline_name_fa": {"type": "text"},
                "country": {"type": "keyword"},
                "country_fa": {"type": "text"},
                "fleet_size": {"type": "integer"},
                "rating": {"type": "float"},
                "is_active": {"type": "boolean"},
                "created_at": {"type": "date"}
            }
        }
    }
    
    # 3. Flights Index (پرواز‌ها)
    flights_mapping = {
        "mappings": {
            "properties": {
                "flight_number": {"type": "keyword"},
                "airline_code": {"type": "keyword"},
                "airline_name": {"type": "text"},
                "origin": {"type": "keyword"},
                "origin_city": {"type": "text"},
                "destination": {"type": "keyword"},
                "destination_city": {"type": "text"},
                "departure_time": {"type": "date"},
                "arrival_time": {"type": "date"},
                "duration_minutes": {"type": "integer"},
                "aircraft_type": {"type": "keyword"},
                "total_seats": {"type": "integer"},
                "available_seats": {"type": "integer"},
                "price_economy": {"type": "float"},
                "price_business": {"type": "float"},
                "price_first": {"type": "float"},
                "status": {"type": "keyword"},  # scheduled, boarding, departed, landed, cancelled, delayed
                "flight_date": {"type": "date"},
                "created_at": {"type": "date"}
            }
        }
    }
    
    # 4. Reservations Index (رزروها)
    reservations_mapping = {
        "mappings": {
            "properties": {
                "reservation_id": {"type": "keyword"},
                "pnr": {"type": "keyword"},  # Passenger Name Record
                "customer_id": {"type": "keyword"},
                "customer_name": {"type": "text"},
                "flight_number": {"type": "keyword"},
                "airline_code": {"type": "keyword"},
                "origin": {"type": "keyword"},
                "destination": {"type": "keyword"},
                "departure_date": {"type": "date"},
                "booking_date": {"type": "date"},
                "status": {"type": "keyword"},  # confirmed, pending, cancelled, completed
                "passengers": {"type": "integer"},
                "total_price": {"type": "float"},
                "payment_status": {"type": "keyword"},  # paid, pending, refunded, partial
                "booking_class": {"type": "keyword"},  # economy, business, first
                "created_by": {"type": "keyword"},  # User ID who created booking
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        }
    }
    
    # 5. Tickets Index (بلیط‌ها)
    tickets_mapping = {
        "mappings": {
            "properties": {
                "ticket_number": {"type": "keyword"},
                "reservation_id": {"type": "keyword"},
                "pnr": {"type": "keyword"},
                "passenger_name": {"type": "text"},
                "passenger_passport": {"type": "keyword"},
                "flight_number": {"type": "keyword"},
                "airline_code": {"type": "keyword"},
                "origin": {"type": "keyword"},
                "destination": {"type": "keyword"},
                "departure_date": {"type": "date"},
                "seat_number": {"type": "keyword"},
                "seat_class": {"type": "keyword"},  # economy, business, first
                "price": {"type": "float"},
                "status": {"type": "keyword"},  # issued, used, cancelled, refunded
                "issue_date": {"type": "date"},
                "issued_by": {"type": "keyword"},  # User ID who issued ticket
                "created_at": {"type": "date"}
            }
        }
    }
    
    # Create indices
    indices = [
        ("customers", customers_mapping),
        ("airlines", airlines_mapping),
        ("flights", flights_mapping),
        ("reservations", reservations_mapping),
        ("tickets", tickets_mapping)
    ]
    
    for index_name, mapping in indices:
        try:
            if client.indices.exists(index=index_name):
                client.indices.delete(index=index_name)
                print(f"🗑️  Deleted existing index: {index_name}")
            
            client.indices.create(index=index_name, body=mapping)
            print(f"✅ Created index: {index_name}")
        except Exception as e:
            print(f"❌ Error creating index {index_name}: {e}")

def populate_mock_data():
    """Populate Elasticsearch with realistic travel agency mock data."""
    client = create_es_client()
    
    # Iranian names for customers
    first_names = ["علی", "محمد", "حسن", "حسین", "رضا", "مهدی", "امیر", "سعید",
                   "فاطمه", "زهرا", "مریم", "سارا", "نرگس", "لیلا", "نازنین", "پریسا"]
    last_names = ["محمدی", "احمدی", "حسینی", "رضایی", "علوی", "کریمی", "نوری", "صادقی",
                  "موسوی", "جعفری", "اکبری", "حسنی", "یوسفی", "ابراهیمی", "باقری", "خانی"]
    
    # 1. Populate Airlines (خطوط هوایی)
    print("\n✈️  Populating Airlines...")
    airlines_data = [
        {"code": "IR", "name": "Iran Air", "name_fa": "هواپیمایی ایران", "country": "IR", "country_fa": "ایران", "fleet": 45, "rating": 4.2},
        {"code": "W5", "name": "Mahan Air", "name_fa": "هواپیمایی ماهان", "country": "IR", "country_fa": "ایران", "fleet": 65, "rating": 4.5},
        {"code": "EP", "name": "Iran Aseman Airlines", "name_fa": "هواپیمایی آسمان", "country": "IR", "country_fa": "ایران", "fleet": 30, "rating": 4.0},
        {"code": "QB", "name": "Qeshm Air", "name_fa": "هواپیمایی قشم", "country": "IR", "country_fa": "ایران", "fleet": 20, "rating": 3.8},
        {"code": "TK", "name": "Turkish Airlines", "name_fa": "هواپیمایی ترکیه", "country": "TR", "country_fa": "ترکیه", "fleet": 380, "rating": 4.7},
        {"code": "EK", "name": "Emirates", "name_fa": "امارات", "country": "AE", "country_fa": "امارات", "fleet": 270, "rating": 4.9},
        {"code": "QR", "name": "Qatar Airways", "name_fa": "هواپیمایی قطر", "country": "QA", "country_fa": "قطر", "fleet": 250, "rating": 4.8},
        {"code": "LH", "name": "Lufthansa", "name_fa": "لوفت‌هانزا", "country": "DE", "country_fa": "آلمان", "fleet": 280, "rating": 4.6},
    ]
    
    for airline in airlines_data:
        doc = {
            "airline_code": airline["code"],
            "airline_name": airline["name"],
            "airline_name_fa": airline["name_fa"],
            "country": airline["country"],
            "country_fa": airline["country_fa"],
            "fleet_size": airline["fleet"],
            "rating": airline["rating"],
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        client.index(index="airlines", id=airline["code"], document=doc)
        print(f"   ✅ {airline['name']} ({airline['code']})")
    
    # 2. Populate Customers (مشتریان)
    print("\n👥 Populating Customers...")
    customers = []
    loyalty_tiers = ["bronze", "silver", "gold", "platinum"]
    
    for i in range(500):
        customer_id = f"CUST{i+1:05d}"
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        customer = {
            "customer_id": customer_id,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "email": f"{first_name.lower()}.{last_name.lower()}{i}@email.com",
            "phone": f"+9891{random.randint(10000000, 99999999)}",
            "passport_number": f"N{random.randint(10000000, 99999999)}",
            "national_id": f"{random.randint(1000000000, 9999999999)}",
            "nationality": "IR",
            "date_of_birth": f"{random.randint(1960, 2005)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "loyalty_tier": random.choice(loyalty_tiers),
            "total_bookings": random.randint(0, 50),
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 1000))).isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        customers.append(customer)
        client.index(index="customers", id=customer_id, document=customer)
    
    print(f"   ✅ Created {len(customers)} customers")
    
    # 3. Populate Flights (پرواز‌ها)
    print("\n🛫 Populating Flights...")
    
    # Iranian airports
    airports = [
        {"code": "IKA", "city": "تهران", "city_en": "Tehran"},
        {"code": "MHD", "city": "مشهد", "city_en": "Mashhad"},
        {"code": "SYZ", "city": "شیراز", "city_en": "Shiraz"},
        {"code": "TBZ", "city": "تبریز", "city_en": "Tabriz"},
        {"code": "IFN", "city": "اصفهان", "city_en": "Isfahan"},
        {"code": "KIH", "city": "کیش", "city_en": "Kish"},
        {"code": "AWZ", "city": "اهواز", "city_en": "Ahvaz"},
        {"code": "DXB", "city": "دبی", "city_en": "Dubai"},
        {"code": "IST", "city": "استانبول", "city_en": "Istanbul"},
        {"code": "DOH", "city": "دوحه", "city_en": "Doha"},
    ]
    
    aircraft_types = ["Boeing 737", "Airbus A320", "Boeing 777", "Airbus A330", "Boeing 747"]
    
    flights = []
    for i in range(200):
        airline = random.choice(airlines_data)
        origin = random.choice(airports)
        destination = random.choice([a for a in airports if a["code"] != origin["code"]])
        
        departure_date = datetime.utcnow() + timedelta(days=random.randint(1, 90))
        flight_duration = random.randint(60, 480)  # 1-8 hours
        arrival_date = departure_date + timedelta(minutes=flight_duration)
        
        total_seats = random.choice([150, 180, 210, 250, 300])
        available = random.randint(0, total_seats)
        
        flight = {
            "flight_number": f"{airline['code']}{random.randint(100, 999)}",
            "airline_code": airline["code"],
            "airline_name": airline["name"],
            "origin": origin["code"],
            "origin_city": origin["city"],
            "destination": destination["code"],
            "destination_city": destination["city"],
            "departure_time": departure_date.isoformat(),
            "arrival_time": arrival_date.isoformat(),
            "duration_minutes": flight_duration,
            "aircraft_type": random.choice(aircraft_types),
            "total_seats": total_seats,
            "available_seats": available,
            "price_economy": round(random.uniform(50, 500), 2),
            "price_business": round(random.uniform(200, 1500), 2),
            "price_first": round(random.uniform(500, 3000), 2),
            "status": random.choice(["scheduled"] * 8 + ["delayed", "cancelled"]),
            "flight_date": departure_date.date().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        flights.append(flight)
        client.index(index="flights", document=flight)
    
    print(f"   ✅ Created {len(flights)} flights")
    
    # 4. Populate Reservations (رزروها)
    print("\n📅 Populating Reservations...")
    
    reservations = []
    for i in range(1000):
        customer = random.choice(customers)
        flight = random.choice(flights)
        passengers = random.randint(1, 5)
        booking_class = random.choice(["economy"] * 7 + ["business"] * 2 + ["first"])
        
        if booking_class == "economy":
            price_per_person = flight["price_economy"]
        elif booking_class == "business":
            price_per_person = flight["price_business"]
        else:
            price_per_person = flight["price_first"]
        
        total_price = price_per_person * passengers
        
        reservation = {
            "reservation_id": f"RES{i+1:06d}",
            "pnr": f"{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}{random.randint(10000, 99999)}",
            "customer_id": customer["customer_id"],
            "customer_name": customer["full_name"],
            "flight_number": flight["flight_number"],
            "airline_code": flight["airline_code"],
            "origin": flight["origin"],
            "destination": flight["destination"],
            "departure_date": flight["departure_time"],
            "booking_date": (datetime.utcnow() - timedelta(days=random.randint(1, 60))).isoformat(),
            "status": random.choice(["confirmed"] * 8 + ["pending", "cancelled"]),
            "passengers": passengers,
            "total_price": round(total_price, 2),
            "payment_status": random.choice(["paid"] * 7 + ["pending", "refunded"]),
            "booking_class": booking_class,
            "created_by": f"USER{random.randint(1, 10):03d}",
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 60))).isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        reservations.append(reservation)
        client.index(index="reservations", id=reservation["reservation_id"], document=reservation)
    
    print(f"   ✅ Created {len(reservations)} reservations")
    
    # 5. Populate Tickets (بلیط‌ها)
    print("\n🎫 Populating Tickets...")
    
    tickets_count = 0
    for reservation in reservations:
        if reservation["status"] == "confirmed" and reservation["payment_status"] == "paid":
            # Create tickets for each passenger
            for p in range(reservation["passengers"]):
                ticket = {
                    "ticket_number": f"TKT{tickets_count+1:08d}",
                    "reservation_id": reservation["reservation_id"],
                    "pnr": reservation["pnr"],
                    "passenger_name": f"{random.choice(first_names)} {random.choice(last_names)}",
                    "passenger_passport": f"N{random.randint(10000000, 99999999)}",
                    "flight_number": reservation["flight_number"],
                    "airline_code": reservation["airline_code"],
                    "origin": reservation["origin"],
                    "destination": reservation["destination"],
                    "departure_date": reservation["departure_date"],
                    "seat_number": f"{random.randint(1, 40)}{random.choice('ABCDEF')}",
                    "seat_class": reservation["booking_class"],
                    "price": round(reservation["total_price"] / reservation["passengers"], 2),
                    "status": random.choice(["issued"] * 9 + ["used"]),
                    "issue_date": reservation["booking_date"],
                    "issued_by": reservation["created_by"],
                    "created_at": reservation["created_at"]
                }
                client.index(index="tickets", document=ticket)
                tickets_count += 1
    
    print(f"   ✅ Created {tickets_count} tickets")
    
    # Refresh all indices
    print("\n🔄 Refreshing indices...")
    for index in ["customers", "airlines", "flights", "reservations", "tickets"]:
        client.indices.refresh(index=index)
    
    print("\n✅ All travel agency data populated successfully!")
    
    # Print summary
    print("\n" + "="*60)
    print("📊 DATA SUMMARY")
    print("="*60)
    print(f"Airlines:     {len(airlines_data):>6}")
    print(f"Customers:    {len(customers):>6}")
    print(f"Flights:      {len(flights):>6}")
    print(f"Reservations: {len(reservations):>6}")
    print(f"Tickets:      {tickets_count:>6}")
    print("="*60)

def verify_data():
    """Verify that data was created successfully."""
    client = create_es_client()
    
    print("\n🔍 Verifying data...")
    indices = ["customers", "airlines", "flights", "reservations", "tickets"]
    
    for index in indices:
        try:
            count = client.count(index=index)["count"]
            print(f"   ✅ {index}: {count} documents")
        except Exception as e:
            print(f"   ❌ {index}: Error - {e}")

if __name__ == "__main__":
    print("🚀 Setting up Elasticsearch for Travel Agency System\n")
    print("="*60)
    
    try:
        print("1️⃣  Creating indices...")
        setup_indices()
        
        print("\n2️⃣  Populating mock data...")
        populate_mock_data()
        
        print("\n3️⃣  Verifying data...")
        verify_data()
        
        print("\n" + "="*60)
        print("✅ Elasticsearch setup completed successfully!")
        print("="*60)
        print("\n💡 You can now query the data:")
        print("   curl http://localhost:9200/flights/_search")
        print("   curl http://localhost:9200/customers/_count")
        print("   curl http://localhost:9200/reservations/_search")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
