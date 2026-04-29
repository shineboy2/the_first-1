# 🚀 راهنمای ساده VM Template

## 📋 خلاصه کار:
1. 2 تا VM Ubuntu بساز
2. کل پروژه رو توشون کپی کن
3. یک دستور اجرا کن
4. Export کن
5. به پروداکشن ببر

---

## مرحله 1: ساخت VM ها

**VM اول**: Response Network
- Ubuntu 20.04, 4GB RAM, 50GB Storage

**VM دوم**: Request Network  
- Ubuntu 20.04, 2GB RAM, 30GB Storage

---

## مرحله 2: نصب Docker در هر VM

```bash
# در هر VM:
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo apt install docker-compose-plugin
sudo reboot
```

---

## مرحله 3: کپی پروژه

**کل پوشه پروژه** رو در هر دو VM کپی کن (با USB یا shared folder)

```bash
# در هر VM:
cp -r /path/to/project ~/project
cd ~/project
```

---

## مرحله 4: آماده‌سازی

```bash
# در VM اول (Response):
./prepare_vm_template.sh response

# در VM دوم (Request):
./prepare_vm_template.sh request
```

---

## مرحله 5: Export

1. VM ها رو خاموش کن
2. Export to OVF
3. فایل‌های .ovf و .vmdk تولید میشه

---

## مرحله 6: انتقال به پروداکشن

1. فایل‌های OVF رو با USB ببر
2. Import کن
3. IP ها رو تنظیم کن:
```bash
./reconfigure_production_ips.sh
```

**تمام!** 🎉