# راهنمای راه‌اندازی سرور FTP واسط

## معماری اتصال

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  Request Network│   FTP   │   FTP Server    │   FTP   │ Response Network│
│    (سمت کاربر)   │◄──────►│     (واسط)       │◄──────►│  (سمت پردازش)   │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

## نصب FTP Server

### گزینه 1: vsftpd (توصیه شده)

```bash
# نصب
sudo apt update
sudo apt install vsftpd -y

# تنظیم
sudo nano /etc/vsftpd.conf
```

**تنظیمات vsftpd.conf:**
```ini
listen=YES
listen_ipv6=NO
anonymous_enable=NO
local_enable=YES
write_enable=YES
local_umask=022
chroot_local_user=YES
allow_writeable_chroot=YES
pasv_enable=YES
pasv_min_port=10000
pasv_max_port=10100
userlist_enable=YES
userlist_file=/etc/vsftpd.userlist
userlist_deny=NO
```

### گزینه 2: ProFTPD

```bash
sudo apt install proftpd -y
```

## ایجاد کاربران

```bash
# ایجاد کاربر برای Request Network
sudo useradd -m -s /bin/bash request_ftp
sudo passwd request_ftp

# ایجاد کاربر برای Response Network
sudo useradd -m -s /bin/bash response_ftp
sudo passwd response_ftp

# افزودن به لیست مجاز
echo "request_ftp" | sudo tee -a /etc/vsftpd.userlist
echo "response_ftp" | sudo tee -a /etc/vsftpd.userlist
```

## ساختار دایرکتوری

```bash
# ایجاد دایرکتوری‌های اصلی
sudo mkdir -p /srv/ftp/requests
sudo mkdir -p /srv/ftp/results
sudo mkdir -p /srv/ftp/users
sudo mkdir -p /srv/ftp/settings

# تنظیم دسترسی‌ها
sudo chown -R request_ftp:request_ftp /srv/ftp/requests
sudo chown -R response_ftp:response_ftp /srv/ftp/results
sudo chown -R response_ftp:response_ftp /srv/ftp/users
sudo chown -R response_ftp:response_ftp /srv/ftp/settings

# دسترسی خواندن برای همه، نوشتن برای مالک
sudo chmod 755 /srv/ftp/*
```

## ماتریس دسترسی

| دایرکتوری | Request Network | Response Network |
|-----------|----------------|------------------|
| /requests | نوشتن ✏️ | خواندن 📖 |
| /results | خواندن 📖 | نوشتن ✏️ |
| /users | خواندن 📖 | نوشتن ✏️ |
| /settings | خواندن 📖 | نوشتن ✏️ |

## جریان داده

```
Request Network                    FTP Server                    Response Network
     │                                  │                              │
     │  1. Export Requests              │                              │
     ├─────────────────────────────────►│                              │
     │     /requests/*.jsonl            │                              │
     │                                  │  2. Import Requests          │
     │                                  │◄─────────────────────────────┤
     │                                  │     /requests/*.jsonl        │
     │                                  │                              │
     │                                  │  3. Process & Query ES       │
     │                                  │                              │
     │                                  │  4. Export Results           │
     │                                  ├─────────────────────────────►│
     │                                  │     /results/*.jsonl         │
     │  5. Import Results              │                              │
     │◄─────────────────────────────────┤                              │
     │     /results/*.jsonl            │                              │
```

## تست اتصال

### از Request Network:
```bash
# تست اتصال
ftp FTP_SERVER_IP
# ورود با request_ftp
# آپلود تست: put test.txt requests/test.txt
```

### از Response Network:
```bash
# تست اتصال
ftp FTP_SERVER_IP
# ورود با response_ftp
# دانلود تست: get requests/test.txt
```

## امنیت

### فعال‌سازی TLS

```bash
# ایجاد Certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/vsftpd.pem \
  -out /etc/ssl/private/vsftpd.pem

# افزودن به vsftpd.conf
ssl_enable=YES
rsa_cert_file=/etc/ssl/private/vsftpd.pem
rsa_private_key_file=/etc/ssl/private/vsftpd.pem
force_local_data_ssl=YES
force_local_logins_ssl=YES
```

### Firewall

```bash
sudo ufw allow 20/tcp  # FTP data
sudo ufw allow 21/tcp  # FTP control
sudo ufw allow 10000:10100/tcp  # Passive mode
sudo ufw enable
```

## عیب‌یابی

### مشکل اتصال
```bash
# بررسی سرویس
sudo systemctl status vsftpd

# بررسی لاگ
sudo tail -f /var/log/vsftpd.log
```

### مشکل دسترسی
```bash
# بررسی دسترسی‌ها
ls -la /srv/ftp/

# تست نوشتن
sudo -u request_ftp touch /srv/ftp/requests/test.txt
```
