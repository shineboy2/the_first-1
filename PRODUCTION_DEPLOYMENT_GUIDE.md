# 📋 راهنمای دیپلوی در محیط پروداکشن

## 🎯 مراحل انتقال VM ها به پروداکشن

### 1️⃣ **Export OVF از سرورهای تست**

#### Request Network (192.168.214.135)
```bash
# در VMware/VirtualBox:
# File → Export → Export to OVF
# نام فایل: request-network.ovf
```

#### Response Network (192.168.214.141)
```bash
# در VMware/VirtualBox:
# File → Export → Export to OVF
# نام فایل: response-network.ovf
```

---

### 2️⃣ **Import در محیط پروداکشن**

1. فایل‌های OVF را به محیط پروداکشن منتقل کنید
2. VM ها را Import کنید
3. **قبل از روشن کردن VM ها**، تنظیمات شبکه را بررسی کنید

---

### 3️⃣ **تغییرات مورد نیاز در Request Network**

پس از روشن کردن VM، به آن SSH کنید و مراحل زیر را انجام دهید:

#### الف) تغییر IP سیستم عامل
```bash
# 1. تغییر IP استاتیک
sudo nano /etc/netplan/00-installer-config.yaml

# محتوای فایل را به این شکل تغییر دهید:
network:
  version: 2
  ethernets:
    ens33:  # یا نام interface شما
      addresses:
        - [IP_PRODUCTION_REQUEST]/24
      gateway4: [GATEWAY]
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4

# 2. اعمال تغییرات
sudo netplan apply

# 3. بررسی IP جدید
ip addr show
```

#### ب) تغییر فایل `.env`
```bash
cd ~/request-network

# ویرایش فایل .env
nano .env

# تغییر این متغیرها:
NEXT_PUBLIC_API_URL=http://[IP_PRODUCTION_REQUEST]:8001
BACKEND_CORS_ORIGINS=http://localhost:3002,http://[IP_PRODUCTION_REQUEST]:3002
```

#### ج) Restart کانتینرها
```bash
cd ~/request-network
docker compose down
docker compose up -d

# بررسی وضعیت
docker compose ps
```

---

### 4️⃣ **تغییرات مورد نیاز در Response Network**

#### الف) تغییر IP سیستم عامل
```bash
# 1. تغییر IP استاتیک
sudo nano /etc/netplan/00-installer-config.yaml

# محتوای فایل:
network:
  version: 2
  ethernets:
    ens33:
      addresses:
        - [IP_PRODUCTION_RESPONSE]/24
      gateway4: [GATEWAY]
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4

# 2. اعمال تغییرات
sudo netplan apply
```

#### ب) تغییر فایل `.env`
```bash
cd ~/response-network

# ویرایش فایل .env
nano .env

# تغییر این متغیرها:
NEXT_PUBLIC_API_URL=http://[IP_PRODUCTION_RESPONSE]:8000
BACKEND_CORS_ORIGINS=http://localhost:3000,http://[IP_PRODUCTION_RESPONSE]:3000
```

#### ج) Restart کانتینرها
```bash
cd ~/response-network
docker compose down
docker compose up -d

# بررسی وضعیت
docker compose ps
```

---

### 5️⃣ **تغییر IP سرور FTP (اگر تغییر کرده)**

اگر IP سرور FTP در پروداکشن متفاوت است:

#### Request Network:
```bash
cd ~/request-network
nano .env

# تغییر این متغیرها:
FTP_HOST=[IP_PRODUCTION_FTP]
FTP_USER=agftp
FTP_PASSWORD=agpass123

# Restart
docker compose restart api celery-worker celery-beat
```

#### Response Network:
```bash
cd ~/response-network
nano .env

# تغییر این متغیرها:
FTP_HOST=[IP_PRODUCTION_FTP]
FTP_USER=agftp
FTP_PASSWORD=agpass123

# Restart
docker compose restart api celery-worker celery-beat
```

---

### 6️⃣ **تغییر IP Elasticsearch (در Response Network)**

```bash
cd ~/response-network
nano .env

# اضافه کردن:
ELASTICSEARCH_URL=http://[IP_PRODUCTION_ELASTICSEARCH]:9200

# Restart
docker compose restart api celery-worker celery-beat
```

---

## 🔧 اسکریپت خودکار تغییر IP

برای سهولت کار، از اسکریپت زیر استفاده کنید:

### Request Network:
```bash
#!/bin/bash
# reconfigure_request_production.sh

NEW_IP="$1"
FTP_IP="$2"

if [ -z "$NEW_IP" ] || [ -z "$FTP_IP" ]; then
    echo "Usage: $0 <NEW_REQUEST_IP> <FTP_IP>"
    echo "Example: $0 10.0.1.100 10.0.1.50"
    exit 1
fi

echo "🔧 Reconfiguring Request Network for IP: $NEW_IP"

cd ~/request-network

# Backup current .env
cp .env .env.backup

# Update .env
sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://${NEW_IP}:8001|g" .env
sed -i "s|BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=http://localhost:3002,http://${NEW_IP}:3002|g" .env
sed -i "s|FTP_HOST=.*|FTP_HOST=${FTP_IP}|g" .env

echo "✅ .env updated"

# Restart containers
echo "🔄 Restarting containers..."
docker compose down
docker compose up -d

echo "✅ Request Network reconfigured!"
echo "📍 New URLs:"
echo "   Admin Panel: http://${NEW_IP}:3002"
echo "   API: http://${NEW_IP}:8001"
echo "   Flower: http://${NEW_IP}:5555"
```

### Response Network:
```bash
#!/bin/bash
# reconfigure_response_production.sh

NEW_IP="$1"
FTP_IP="$2"
ES_IP="$3"

if [ -z "$NEW_IP" ] || [ -z "$FTP_IP" ] || [ -z "$ES_IP" ]; then
    echo "Usage: $0 <NEW_RESPONSE_IP> <FTP_IP> <ELASTICSEARCH_IP>"
    echo "Example: $0 10.0.2.100 10.0.1.50 10.0.2.50"
    exit 1
fi

echo "🔧 Reconfiguring Response Network for IP: $NEW_IP"

cd ~/response-network

# Backup current .env
cp .env .env.backup

# Update .env
sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://${NEW_IP}:8000|g" .env
sed -i "s|BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=http://localhost:3000,http://${NEW_IP}:3000|g" .env
sed -i "s|FTP_HOST=.*|FTP_HOST=${FTP_IP}|g" .env
sed -i "s|ELASTICSEARCH_URL=.*|ELASTICSEARCH_URL=http://${ES_IP}:9200|g" .env

echo "✅ .env updated"

# Restart containers
echo "🔄 Restarting containers..."
docker compose down
docker compose up -d

echo "✅ Response Network reconfigured!"
echo "📍 New URLs:"
echo "   Admin Panel: http://${NEW_IP}:3000"
echo "   API: http://${NEW_IP}:8000"
echo "   Flower: http://${NEW_IP}:5555"
```

---

## 📝 چک‌لیست نهایی

### ✅ قبل از Export OVF:
- [ ] همه کانتینرها healthy هستند
- [ ] دیتابیس‌ها داده دارند
- [ ] کاربر admin ساخته شده
- [ ] Login تست شده و کار می‌کند

### ✅ بعد از Import در پروداکشن:
- [ ] IP سیستم عامل تغییر کرده
- [ ] فایل `.env` در هر دو شبکه به‌روز شده
- [ ] کانتینرها restart شده‌اند
- [ ] همه سرویس‌ها healthy هستند
- [ ] Login در admin panel کار می‌کند
- [ ] ارتباط با FTP برقرار است
- [ ] ارتباط با Elasticsearch برقرار است (Response Network)

---

## 🔐 اطلاعات ورود پیش‌فرض

### Request Network:
```
Username: admin
Password: admin123456
```

### Response Network:
```
Username: admin
Password: admin123456
```

⚠️ **مهم**: بعد از دیپلوی در پروداکشن، حتماً رمز عبور admin را تغییر دهید!

---

## 🆘 عیب‌یابی

### مشکل: کانتینرها start نمی‌شوند
```bash
# بررسی لاگ‌ها
docker compose logs api
docker compose logs admin-panel

# بررسی .env
cat .env
```

### مشکل: Login کار نمی‌کند
```bash
# بررسی CORS
docker exec [container-name]-api env | grep CORS

# تست API
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123456"
```

### مشکل: Runtime config load نمی‌شود
```bash
# بررسی config.js
docker exec [container-name]-admin-panel cat /app/public/config.js

# Restart admin panel
docker compose restart admin-panel
```

---

## 📞 پشتیبانی

در صورت بروز مشکل، لاگ‌های زیر را بررسی کنید:
```bash
# API logs
docker logs [network]-api --tail 100

# Admin Panel logs
docker logs [network]-admin-panel --tail 100

# Database logs
docker logs [network]-db --tail 50
```
