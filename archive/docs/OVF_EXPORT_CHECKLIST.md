# ✅ چک‌لیست Export و Import OVF

## 📦 قبل از Export OVF

### Request Network (192.168.214.135)
- [ ] همه کانتینرها healthy هستند
  ```bash
  ssh request@192.168.214.135
  cd request-network
  docker compose ps
  ```
- [ ] دیتابیس داده دارد
  ```bash
  docker exec request-db psql -U request_user -d request_db -c "SELECT COUNT(*) FROM users;"
  ```
- [ ] Login کار می‌کند
  - [ ] به `http://192.168.214.135:3002` بروید
  - [ ] با `admin` / `admin123456` login کنید

### Response Network (192.168.214.141)
- [ ] همه کانتینرها healthy هستند
  ```bash
  ssh response@192.168.214.141
  cd response-network
  docker compose ps
  ```
- [ ] دیتابیس داده دارد
  ```bash
  docker exec response-db psql -U response_user -d response_db -c "SELECT COUNT(*) FROM users;"
  ```
- [ ] Login کار می‌کند
  - [ ] به `http://192.168.214.141:3000` بروید
  - [ ] با `admin` / `admin123456` login کنید

---

## 🚀 Export OVF

### Request Network
1. [ ] VM را Shutdown کنید (نه Suspend)
   ```bash
   ssh request@192.168.214.135
   sudo shutdown -h now
   ```
2. [ ] در VMware/VirtualBox:
   - [ ] File → Export to OVF/OVA
   - [ ] نام: `request-network.ovf`
   - [ ] مسیر: ذخیره در جای امن

### Response Network
1. [ ] VM را Shutdown کنید
   ```bash
   ssh response@192.168.214.141
   sudo shutdown -h now
   ```
2. [ ] در VMware/VirtualBox:
   - [ ] File → Export to OVF/OVA
   - [ ] نام: `response-network.ovf`
   - [ ] مسیر: ذخیره در جای امن

---

## 📥 Import در پروداکشن

### Request Network
1. [ ] فایل OVF را به محیط پروداکشن منتقل کنید
2. [ ] Import کنید (File → Import)
3. [ ] تنظیمات شبکه را بررسی کنید
4. [ ] VM را روشن کنید

### Response Network
1. [ ] فایل OVF را به محیط پروداکشن منتقل کنید
2. [ ] Import کنید
3. [ ] تنظیمات شبکه را بررسی کنید
4. [ ] VM را روشن کنید

---

## 🔧 تنظیمات پس از Import

### Request Network

#### 1. تغییر IP سیستم عامل
```bash
# SSH به VM
ssh request@[OLD_IP]

# ویرایش netplan
sudo nano /etc/netplan/00-installer-config.yaml

# محتوا:
network:
  version: 2
  ethernets:
    ens33:
      addresses:
        - [NEW_IP]/24
      gateway4: [GATEWAY]
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4

# اعمال
sudo netplan apply

# بررسی
ip addr show
```

#### 2. اجرای اسکریپت تنظیم مجدد
```bash
# کپی اسکریپت به VM
scp reconfigure_request_production.sh request@[NEW_IP]:~/

# اجرا
ssh request@[NEW_IP]
chmod +x reconfigure_request_production.sh
./reconfigure_request_production.sh [NEW_IP] [FTP_IP]

# مثال:
# ./reconfigure_request_production.sh 10.0.1.100 10.0.1.50
```

#### 3. بررسی نهایی
- [ ] همه کانتینرها healthy هستند
- [ ] Login کار می‌کند: `http://[NEW_IP]:3002`
- [ ] API پاسخ می‌دهد: `http://[NEW_IP]:8001/api/v1/health`

---

### Response Network

#### 1. تغییر IP سیستم عامل
```bash
# SSH به VM
ssh response@[OLD_IP]

# ویرایش netplan
sudo nano /etc/netplan/00-installer-config.yaml

# محتوا:
network:
  version: 2
  ethernets:
    ens33:
      addresses:
        - [NEW_IP]/24
      gateway4: [GATEWAY]
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4

# اعمال
sudo netplan apply

# بررسی
ip addr show
```

#### 2. اجرای اسکریپت تنظیم مجدد
```bash
# کپی اسکریپت به VM
scp reconfigure_response_production.sh response@[NEW_IP]:~/

# اجرا
ssh response@[NEW_IP]
chmod +x reconfigure_response_production.sh
./reconfigure_response_production.sh [NEW_IP] [FTP_IP] [ES_IP]

# مثال:
# ./reconfigure_response_production.sh 10.0.2.100 10.0.1.50 10.0.2.50
```

#### 3. بررسی نهایی
- [ ] همه کانتینرها healthy هستند
- [ ] Login کار می‌کند: `http://[NEW_IP]:3000`
- [ ] API پاسخ می‌دهد: `http://[NEW_IP]:8000/api/v1/health`
- [ ] ارتباط با Elasticsearch برقرار است

---

## 🔐 امنیت

### تغییر رمز عبور Admin
```bash
# Request Network
ssh request@[NEW_IP]
docker exec -it request-api python reset_admin_password.py

# Response Network
ssh response@[NEW_IP]
docker exec -it response-api python reset_admin_password.py
```

### تغییر SECRET_KEY
```bash
# در هر دو شبکه
cd ~/[network-name]
nano .env

# تغییر:
SECRET_KEY=[NEW_RANDOM_SECRET_KEY]

# Restart
docker compose restart api
```

---

## 📊 تست نهایی

### Request Network
```bash
# Health Check
curl http://[NEW_IP]:8001/api/v1/health

# Login Test
curl -X POST "http://[NEW_IP]:8001/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123456"

# Admin Panel
# باز کردن در مرورگر: http://[NEW_IP]:3002
```

### Response Network
```bash
# Health Check
curl http://[NEW_IP]:8000/api/v1/health

# Login Test
curl -X POST "http://[NEW_IP]:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123456"

# Admin Panel
# باز کردن در مرورگر: http://[NEW_IP]:3000

# Elasticsearch Test
curl http://[ES_IP]:9200
```

---

## 🆘 عیب‌یابی

### مشکل: کانتینرها start نمی‌شوند
```bash
# بررسی لاگ‌ها
docker compose logs api
docker compose logs admin-panel

# بررسی .env
cat .env | grep -E "API_URL|CORS"
```

### مشکل: Login کار نمی‌کند
```bash
# بررسی CORS
docker exec [container]-api env | grep CORS

# بررسی runtime config
docker exec [container]-admin-panel cat /app/public/config.js
```

### مشکل: Network unreachable
```bash
# بررسی IP
ip addr show

# بررسی gateway
ip route show

# تست ping
ping 8.8.8.8
```

---

## 📝 یادداشت‌های مهم

1. **Backup**: قبل از هر تغییری، از `.env` و دیتابیس backup بگیرید
2. **Downtime**: تغییر IP نیاز به restart دارد (حدود 2-3 دقیقه)
3. **DNS**: اگر از DNS استفاده می‌کنید، رکوردها را به‌روز کنید
4. **Firewall**: پورت‌های مورد نیاز را باز کنید:
   - Request: 3002, 8001, 5555
   - Response: 3000, 8000, 5555
5. **FTP**: مطمئن شوید سرور FTP در دسترس است
6. **Elasticsearch**: فقط برای Response Network لازم است

---

## ✅ تایید نهایی

- [ ] Request Network کامل کار می‌کند
- [ ] Response Network کامل کار می‌کند
- [ ] ارتباط بین دو شبکه برقرار است (از طریق FTP)
- [ ] رمزهای عبور تغییر کرده‌اند
- [ ] Backup از تنظیمات گرفته شده
- [ ] مستندات به‌روز شده‌اند

🎉 **سیستم آماده استفاده در پروداکشن است!**
