import sys
from pathlib import Path
sys.path.insert(0, "/app")

from workers.celery_app import celery_app
from redbeat import RedBeatSchedulerEntry
from redbeat.schedulers import get_redis

try:
    redis = get_redis(celery_app)
except Exception as e:
    print("get_redis failed:", e)
    import redis as redis_lib
    redis = redis_lib.from_url(celery_app.conf.broker_url)

conf = celery_app.conf
key_prefix = conf.get('redbeat_key_prefix', 'redbeat:')
print("Key prefix:", key_prefix)
keys = redis.keys(f"{key_prefix}*")
print("Found keys:", keys)

for key in keys:
    key_str = key.decode('utf-8')
    name = key_str.replace(key_prefix, '')
    if name.endswith(':meta'):
        continue
    try:
        entry = RedBeatSchedulerEntry.from_key(key_str, app=celery_app)
        print("Schedule:", entry.name, entry.task, entry.schedule)
    except Exception as e:
        print("Error:", e)
