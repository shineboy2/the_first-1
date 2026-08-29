"""
دیباگ Celery - بررسی اینکه Beat و Worker صحیح کار می‌کنند
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / "api"))

from workers.celery_app import celery_app

print("=" * 60)
print("🔍 Celery Configuration Debug")
print("=" * 60)

# 1. بررسی Broker و Backend
print("\n1️⃣ Broker & Backend:")
print(f"   Broker: {celery_app.conf.broker_url}")
print(f"   Backend: {celery_app.conf.result_backend}")

# 2. بررسی Beat Schedule
print("\n2️⃣ Beat Schedule:")
if hasattr(celery_app.conf, 'beat_schedule'):
    for name, config in celery_app.conf.beat_schedule.items():
        print(f"   ✅ {name}")
        print(f"      Task: {config['task']}")
        print(f"      Schedule: {config['schedule']}s")
else:
    print("   ❌ Beat schedule تعریف نشده!")

# 3. بررسی Tasks
print("\n3️⃣ Registered Tasks:")
try:
    tasks = celery_app.tasks
    if tasks:
        for task_name in sorted(tasks.keys()):
            if 'settings' in task_name.lower() or 'export' in task_name.lower():
                print(f"   ✅ {task_name}")
    else:
        print("   ❌ هیچ تسکی رجیستر نشده!")
except Exception as e:
    print(f"   ❌ خطا: {e}")

# 4. بررسی Timezone
print("\n4️⃣ Timezone:")
print(f"   Timezone: {celery_app.conf.timezone}")
print(f"   Enable UTC: {celery_app.conf.enable_utc}")

# 5. بررسی Connection
print("\n5️⃣ Broker Connection:")
try:
    with celery_app.connection() as conn:
        print("   ✅ Redis متصل است!")
        # بررسی Queue
        print(f"   Queue: celery")
except Exception as e:
    print(f"   ❌ خطا: {e}")

print("\n" + "=" * 60)
print("✅ Debug تمام شد!")
print("=" * 60)
