# 📥 راهنمای Import و راه‌اندازی در پروداکشن

این راهنما برای تیم پروداکشن جهت import و راه‌اندازی VM های آماده شده طراحی شده است.

## 📦 محتویات دریافتی

شما باید فایل‌های زیر را دریافت کرده باشید:

```
📁 Production_Package/
├── 📁 Response_Network_VM/          # VM سرور اصلی
│   ├── response-network.ovf
│   ├── response-network.vmdk
│   └── response-network.mf
├── 📁 Request_Network_VM/           # VM پردازش درخواست
│   ├── request-network.ovf
│   ├── request-network.vmdk
│   └── request-network.mf
├── 📄 PRODUCTION_IMPORT_GUIDE.md    # این فایل
├── 📄 VM_TEMPLATE_GUIDE.md          # راهنمای تکمیلی
└── 📄 VM_INFO.txt                   # اطلاعات VM ها
```

---

## 🖥️ مرحله 1: Import VM ها

### VMware vSphere/ESXi:
1. به vSphere Client وارد شوید
2. **Host** → **Deploy OVF Template**
3. **Local file** را انتخاب کنید
4. فایل `.ovf` مربوط به Response Network را انتخاب کنید
5. نام VM: `Response-Network-Production`
6. **Datastore** و **Network** مناسب را انتخاب کنید
7. **Finish** کلیک کنید
8. همین مراحل را برای Request Network تکرار کنید

### VMware Workstation:
1. **File** → **Open**
2. فایل `.ovf` را انتخاب کنید
3. نام VM را وارد کنید
4. مسیر ذخیره را انتخاب کنید
5. **Import** کلیک کنید

### VirtualBox:
1. **File** → **Import Appliance**
2. فایل `.ovf` را انتخاب کنید
3. تنظیمات را بررسی کنید (RAM, CPU, Network)
4. **Import** کلیک کنید

---

## 🌐 مرحله 2: تنظیم شبکه

### تنظیم IP استاتیک برای هر VM:

#### Response Network VM:
```bash
# ورود به VM
sudo nano /etc/netplan/00-installer-config.yaml

# تنظیم IP (مثال)
network:
  version: 2
  ethernets:
    ens33:
      dhcp4: false
      addresses: [192.168.1.10/24]    # IP مورد نظر شما
      gateway4: 192.168.1.1           # Gateway شبکه
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]

# اعمال تغییرات
sudo netplan apply
```

#### Request Network VM:
```bash
# همین مراحل با IP متفاوت
addresses: [192.168.1.11/24]    # IP مورد نظر شما
```

### تست اتصال شبکه:
```bash
# تست ping
ping 8.8.8.8
ping 192.168.1.1

# تست DNS
nslookup google.com
```

---

## 🔧 مرحله 3: تنظیم IP های سرویس‌ها

### در هر VM:

1. **ورود به پوشه پروژه**:
```bash
cd /home/[username]/[project_folder]
```

2. **اجرای اسکریپت تنظیم**:
```bash
./reconfigure_production_ips.sh
```

3. **وارد کردن IP ها**:
```
IP سرور Response Network: 192.168.1.10
IP سرور Request Network: 192.168.1.11
IP سرور Elasticsearch: 192.168.1.10    # معمولاً همان Response
IP سرور FTP: 192.168.1.10              # معمولاً همان Response
```

4. **تأیید و اجرا**: `y`

---

## ✅ مرحله 4: تست سلامت سیستم

### تست خودکار:
```bash
./test_production.sh
```

### تست دستی:

#### Response Network:
```bash
# تست API
curl http://192.168.1.10:8000/api/v1/health

# تست اتصال به Elasticsearch (سرور خارجی)
curl http://[ELASTICSEARCH_IP]:9200/_cluster/health

# تست در مرورگر
# Admin Panel: http://192.168.1.10:3000
```

**توجه**: Elasticsearch روی سرور جداگانه قرار دارد و Response Network به آن متصل می‌شود.

#### Request Network:
```bash
# تست API
curl http://192.168.1.11:8001/api/v1/health

# تست در مرورگر
# Admin Panel: http://192.168.1.11:3002
```

---

## 🔑 مرحله 5: ورود اولیه و تنظیمات

### اطلاعات ورود پیش‌فرض:
- **نام کاربری**: `admin`
- **رمز عبور**: `admin123456`

### تنظیمات اولیه:

1. **تغییر رمز عبور admin**:
   - وارد پنل مدیریت شوید
   - بخش تنظیمات کاربری
   - رمز عبور جدید تنظیم کنید

2. **تنظیم FTP** (در Response Network):
   - بخش تنظیمات سیستم
   - اطلاعات FTP Server را وارد کنید

3. **تست اتصال بین شبکه‌ها**:
   - از Request Network یک درخواست تست ایجاد کنید
   - بررسی کنید که در Response Network دریافت شود

---

## 🔍 عیب‌یابی مشکلات رایج

### مشکل 1: VM راه‌اندازی نمی‌شود
```bash
# بررسی وضعیت VM
# در VMware: VM Settings → Hardware → Memory/CPU
# در VirtualBox: Settings → System

# بررسی لاگ‌های VM
# VMware: VM → Troubleshoot → Collect Support Information
# VirtualBox: Machine → Show Log
```

### مشکل 2: شبکه کار نمی‌کند
```bash
# بررسی تنظیمات شبکه
ip addr show
ip route show

# تست اتصال
ping 192.168.1.1
ping 8.8.8.8

# بررسی فایروال
sudo ufw status
```

### مشکل 3: سرویس‌ها راه‌اندازی نمی‌شوند
```bash
# بررسی وضعیت Docker
sudo systemctl status docker

# بررسی کانتینرها
sudo docker ps -a

# بررسی لاگ‌ها
sudo docker logs [container_name]

# راه‌اندازی مجدد
cd response-network  # یا request-network
sudo docker compose down
sudo docker compose up -d
```

### مشکل 4: API در دسترس نیست
```bash
# بررسی پورت‌های باز
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :8001

# بررسی فایروال
sudo ufw allow 8000
sudo ufw allow 8001
sudo ufw allow 3000
sudo ufw allow 3002

# تست محلی
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/api/v1/health
```

---

## 📋 چک‌لیست نهایی

### Response Network:
- [ ] VM import و راه‌اندازی شده
- [ ] IP شبکه تنظیم شده
- [ ] اسکریپت reconfigure اجرا شده
- [ ] API سالم: `curl http://[IP]:8000/api/v1/health`
- [ ] Admin Panel: `http://[IP]:3000`
- [ ] اتصال به Elasticsearch خارجی تست شده
- [ ] رمز عبور admin تغییر داده شده

### Request Network:
- [ ] VM import و راه‌اندازی شده
- [ ] IP شبکه تنظیم شده
- [ ] اسکریپت reconfigure اجرا شده
- [ ] API سالم: `curl http://[IP]:8001/api/v1/health`
- [ ] Admin Panel: `http://[IP]:3002`
- [ ] رمز عبور admin تغییر داده شده

### اتصال بین شبکه‌ها:
- [ ] FTP Server تنظیم شده
- [ ] تست تبادل فایل انجام شده
- [ ] درخواست از Request به Response ارسال می‌شود

---

## 📞 پشتیبانی

### در صورت بروز مشکل:

1. **بررسی فایل‌های راهنما**:
   - `VM_INFO.txt` - اطلاعات کلی VM
   - `VM_TEMPLATE_GUIDE.md` - راهنمای تکمیلی

2. **جمع‌آوری اطلاعات خطا**:
```bash
# لاگ‌های سیستم
sudo journalctl -xe

# لاگ‌های Docker
sudo docker logs [container_name]

# وضعیت سرویس‌ها
sudo systemctl status docker
```

3. **تماس با پشتیبانی**:
   - اطلاعات سیستم عامل
   - پیام‌های خطا
   - مراحل انجام شده

---

## 🎯 نکات مهم

1. **امنیت**: حتماً رمز عبور admin را تغییر دهید
2. **بکاپ**: از VM ها snapshot بگیرید
3. **مانیتورینگ**: لاگ‌ها را به طور منظم بررسی کنید
4. **بروزرسانی**: برای بروزرسانی، VM جدید دریافت کنید

---

**موفق باشید! 🚀**