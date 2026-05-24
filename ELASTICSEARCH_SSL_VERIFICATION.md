# Elasticsearch SSL Verification Configuration

**تاریخ**: 2026-05-23  
**وضعیت**: ✅ تکمیل شده

---

## 📋 خلاصه

تمام جاهایی که به Elasticsearch درخواست می‌رود، اکنون `verify_ssl` را از دیتابیس می‌خوانند و به عنوان پارامتر پاس می‌دهند.

---

## 🔍 فایل‌های اصلاح شده

### 1. `/response-network/api/workers/tasks/execute_query.py`

**وضعیت**: ✅ اصلاح شده

**تغییرات**:
- SSL context برای HTTPS URLs ساخته می‌شود
- `verify_ssl` از `ElasticsearchConfig` خوانده می‌شود
- اگر config نباشد، `verify_ssl=False` به صورت پیش‌فرض استفاده می‌شود

**کد**:
```python
# Try to get active Elasticsearch config from database
es_config = None
try:
    es_config_result = db.query(ElasticsearchConfig).filter(
        ElasticsearchConfig.is_active == True
    ).first()
    es_config = es_config_result
    if es_config:
        logger.info(f"[ELASTICSEARCH] Loaded config from database: {es_config.url} (user: {es_config.username})")
    else:
        logger.warning(f"[ELASTICSEARCH] No active config found in database, using settings: {settings.ELASTICSEARCH_URL}")
except Exception as e:
    logger.error(f"[ELASTICSEARCH] Failed to load config from database: {e}", exc_info=True)

# Create SSL context based on verify_ssl setting
ssl_context = None

if es_url.startswith('https://'):
    ssl_context = ssl.create_default_context()
    
    if es_config and not es_config.verify_ssl:
        # غیرفعال کردن کامل SSL verification
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        logger.info(f"[ELASTICSEARCH] SSL verification disabled for {es_url}")
    elif es_config and es_config.verify_ssl:
        # فعال کردن SSL verification
        logger.info(f"[ELASTICSEARCH] SSL verification enabled for {es_url}")
    else:
        # اگر config نداریم، به صورت پیش‌فرض SSL را غیرفعال کن
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        logger.warning(f"[ELASTICSEARCH] No config from DB, disabling SSL verification for {es_url}")

try:
    with urllib.request.urlopen(req_obj, timeout=10.0, context=ssl_context) as f:
        response_body = f.read().decode('utf-8')
        es_result = json.loads(response_body)
```

---

### 2. `/response-network/api/workers/elasticsearch_client.py`

**وضعیت**: ✅ اصلاح شده

**تغییرات**:
- `verify_ssl` پارامتر در `__init__` دریافت می‌شود
- `verify_certs` به عنوان پارامتر به `AsyncElasticsearch` پاس می‌شود
- `create_from_runtime_config()` method config را از دیتابیس می‌خواند

**کد**:
```python
class ElasticsearchClient:
    def __init__(self, hosts=None, username=None, password=None, verify_ssl=True):
        """
        Initialize Elasticsearch client.
        
        Args:
            hosts: List of ES hosts (overrides settings if provided)
            username: Username for basic auth
            password: Password for basic auth
            verify_ssl: Whether to verify SSL certificate
        """
        self.es = None
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        
        if hosts is None:
            es_url = str(settings.ELASTICSEARCH_URL)
            hosts = [es_url]
        
        try:
            kwargs = {"hosts": hosts}
            if username and password:
                kwargs["basic_auth"] = (username, password)
            kwargs["verify_certs"] = verify_ssl  # ✅ verify_ssl پاس می‌شود
            
            self.es = AsyncElasticsearch(**kwargs)
        except Exception as e:
            logging.error(f"Failed to initialize Elasticsearch client: {e}")
            self.es = None

    @classmethod
    async def create_from_runtime_config(cls):
        """
        Create an Elasticsearch client using runtime configuration from database.
        Falls back to settings if no runtime config is found.
        """
        try:
            from db.session import async_session
            from models.elasticsearch_config import ElasticsearchConfig
            from sqlalchemy import select
            
            async with async_session() as session:
                result = await session.execute(
                    select(ElasticsearchConfig).where(ElasticsearchConfig.is_active == True)
                )
                config = result.scalars().first()
                
                if config:
                    logging.info(f"Using runtime Elasticsearch config: {config.url}")
                    return cls(
                        hosts=[config.url],
                        username=config.username,
                        password=config.password,
                        verify_ssl=config.verify_ssl  # ✅ verify_ssl از config خوانده می‌شود
                    )
        except Exception as e:
            logging.warning(f"Failed to load runtime Elasticsearch config, falling back to settings: {e}")
        
        # Fallback to settings
        return cls()
```

---

### 3. `/response-network/api/setup_elasticsearch.py`

**وضعیت**: ✅ اصلاح شده

**تغییرات**:
- `create_es_client()` اکنون `verify_ssl` پارامتر دریافت می‌کند
- Config را از دیتابیس می‌خواند
- اگر config نباشد، `verify_ssl=False` به صورت پیش‌فرض استفاده می‌شود

**کد**:
```python
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
            kwargs["verify_certs"] = config.verify_ssl  # ✅ verify_ssl از config
            return Elasticsearch(**kwargs)
    except Exception as e:
        logger.warning(f"Failed to load runtime Elasticsearch config: {e}")
    
    # Fallback to ES_URL with verify_ssl parameter
    kwargs = {"hosts": [ES_URL]}
    kwargs["verify_certs"] = verify_ssl  # ✅ پیش‌فرض False
    return Elasticsearch(**kwargs)
```

---

### 4. `/response-network/api/setup_travel_data.py`

**وضعیت**: ✅ اصلاح شده

**تغییرات**: مشابه `setup_elasticsearch.py`

---

### 5. `/response-network/api/services/elasticsearch_config.py`

**وضعیت**: ✅ قبلاً صحیح

**کد**:
```python
async def test_connection(self, config: ElasticsearchConfig) -> tuple[bool, str]:
    """Test connection to Elasticsearch with given configuration."""
    try:
        from elasticsearch import AsyncElasticsearch
        
        # Build connection kwargs
        kwargs = {"hosts": [config.url]}
        if config.username and config.password:
            kwargs["basic_auth"] = (config.username, config.password)
        kwargs["verify_certs"] = config.verify_ssl  # ✅ verify_ssl پاس می‌شود
        
        # Create client and test
        es_client = AsyncElasticsearch(**kwargs)
        
        try:
            info = await es_client.info()
            await es_client.close()
            return True, f"Connected successfully to {info.get('version', {}).get('number', 'Unknown')} Elasticsearch"
        except Exception as e:
            await es_client.close()
            return False, f"Connection failed: {str(e)}"
            
    except Exception as e:
        logger.error(f"Error testing Elasticsearch connection: {str(e)}")
        return False, f"Error: {str(e)}"
```

---

## 📊 جدول خلاصه

| فایل | وضعیت | تغییرات |
|------|-------|---------|
| `execute_query.py` | ✅ | SSL context برای HTTPS، verify_ssl از config |
| `elasticsearch_client.py` | ✅ | verify_ssl پارامتر، create_from_runtime_config |
| `setup_elasticsearch.py` | ✅ | verify_ssl پارامتر، config از DB |
| `setup_travel_data.py` | ✅ | verify_ssl پارامتر، config از DB |
| `elasticsearch_config.py` | ✅ | verify_certs پاس می‌شود |

---

## 🔄 جریان کار

### 1. Worker Query Execution
```
execute_pending_queries()
  ↓
Load ElasticsearchConfig from DB
  ↓
Check if URL is HTTPS
  ↓
Create SSL context with verify_ssl from config
  ↓
urllib.request.urlopen(context=ssl_context)
```

### 2. Elasticsearch Client Initialization
```
ElasticsearchClient.create_from_runtime_config()
  ↓
Load ElasticsearchConfig from DB
  ↓
Pass verify_ssl to AsyncElasticsearch
  ↓
AsyncElasticsearch(verify_certs=verify_ssl)
```

### 3. Setup Scripts
```
create_es_client(verify_ssl=False)
  ↓
Try to load config from DB
  ↓
If found: use config.verify_ssl
  ↓
If not found: use verify_ssl parameter (default False)
```

---

## 🧪 تست

### تست 1: بررسی لاگ Worker
```bash
docker logs response-celery-worker | grep ELASTICSEARCH

# باید نشان دهد:
# [ELASTICSEARCH] Loaded config from database: https://10.1.0.23:9200 (user: 3136)
# [ELASTICSEARCH] SSL verification disabled for https://10.1.0.23:9200/...
```

### تست 2: بررسی Connection Test
```bash
curl -X POST http://localhost:8000/api/v1/admin/elasticsearch/config/test-new \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "url": "https://10.1.0.23:9200",
    "username": "3136",
    "password": "YOUR_PASSWORD",
    "verify_ssl": false
  }'

# باید نشان دهد:
# {"success": true, "message": "Connected successfully to ..."}
```

### تست 3: ارسال Query
```bash
# ارسال یک request از فرانت‌اند
# بررسی لاگ worker برای مشاهده SSL messages
docker logs response-celery-worker --tail 50 | grep -E "ELASTICSEARCH|SSL"
```

---

## ⚠️ نکات مهم

1. **پیش‌فرض**: اگر config در دیتابیس نباشد، `verify_ssl=False` استفاده می‌شود
2. **HTTPS URLs**: فقط برای HTTPS URLs، SSL context ساخته می‌شود
3. **HTTP URLs**: برای HTTP URLs، `ssl_context=None` استفاده می‌شود
4. **Database Priority**: تنظیمات دیتابیس بر تنظیمات environment variable اولویت دارند

---

## 🚀 Deploy

```bash
# Build
cd /home/docker/the_first/the_first/response-network
docker-compose build

# Save
docker save response-network:latest | gzip > response-network.tar.gz

# Transfer
scp response-network.tar.gz user@production:/tmp/

# Load
docker load < response-network.tar.gz

# Restart
docker-compose restart celery-worker
```

---

**تاریخ تکمیل**: 2026-05-23  
**نسخه**: 1.0
