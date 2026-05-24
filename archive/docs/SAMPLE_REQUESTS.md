# نمونه درخواست‌های تست برای Elasticsearch

## 1. جستجوی پرواز (Flight_Search)

### جستجوی بر اساس شماره پرواز:
```bash
curl -X POST http://192.168.214.146:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query_type": "Flight_Search",
    "query_params": {
      "flight_number": "FV1000"
    }
  }'
```

### جستجوی بر اساس airline:
```bash
curl -X POST http://192.168.214.146:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query_type": "Flight_Search",
    "query_params": {
      "airline": "Fly Vayu"
    }
  }'
```

### جستجوی بر اساس فرودگاه مبدا:
```bash
curl -X POST http://192.168.214.146:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query_type": "Flight_Search",
    "query_params": {
      "departure_airport": "JFK"
    }
  }'
```

## 2. جستجوی مسافر (Passenger_Search)

### جستجوی بر اساس ایمیل:
```bash
curl -X POST http://192.168.214.146:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query_type": "Passenger_Search",
    "query_params": {
      "email": "passenger1000@airline.com"
    }
  }'
```

### جستجوی بر اساس نام:
```bash
curl -X POST http://192.168.214.146:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query_type": "Passenger_Search",
    "query_params": {
      "first_name": "Hassan",
      "last_name": "Sadegh"
    }
  }'
```

### جستجوی بر اساس ملیت:
```bash
curl -X POST http://192.168.214.146:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query_type": "Passenger_Search",
    "query_params": {
      "nationality": "Indian"
    }
  }'
```

## 3. جستجوی رزرو (Reservation_Search)

### جستجوی بر اساس شماره پرواز:
```bash
curl -X POST http://192.168.214.146:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query_type": "Reservation_Search",
    "query_params": {
      "flight_number": "IR1016"
    }
  }'
```

### جستجوی بر اساس ایمیل مسافر:
```bash
curl -X POST http://192.168.214.146:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query_type": "Reservation_Search",
    "query_params": {
      "passenger_email": "passenger1@airline.com"
    }
  }'
```

### جستجوی بر اساس وضعیت:
```bash
curl -X POST http://192.168.214.146:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query_type": "Reservation_Search",
    "query_params": {
      "status": "completed"
    }
  }'
```

### جستجوی بر اساس reservation_id:
```bash
curl -X POST http://192.168.214.146:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query_type": "Reservation_Search",
    "query_params": {
      "reservation_id": "RES10000"
    }
  }'
```

## نحوه دریافت توکن:

```bash
curl -X POST http://192.168.214.146:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123456"
  }'
```

## بررسی نتایج:

### لیست درخواست‌ها:
```bash
curl -X GET http://192.168.214.146:8000/api/v1/requests \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### جزئیات یک درخواست:
```bash
curl -X GET http://192.168.214.146:8000/api/v1/requests/{REQUEST_ID} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## داده‌های موجود در Elasticsearch:

- **flights**: 20 پرواز با airline های مختلف (Fly Vayu و غیره)
- **passengers**: 50 مسافر با ملیت‌های مختلف (Indian, Dutch و غیره)
- **reservations**: 100 رزرو با وضعیت‌های مختلف (completed, cancelled, confirmed)
