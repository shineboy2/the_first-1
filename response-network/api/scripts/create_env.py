content = """DATABASE_URL=postgresql+asyncpg://user:password@localhost:5433/response_db
RESPONSE_DB_USER=user
RESPONSE_DB_PASSWORD=password
RESPONSE_DB_HOST=localhost
RESPONSE_DB_PORT=5433
RESPONSE_DB_NAME=response_db
REDIS_URL=redis://localhost:6380/0
ELASTICSEARCH_URL=http://localhost:9200
PROJECT_NAME=Response Network Monitoring API
API_V1_STR=/api/v1
SECRET_KEY=your-secret-key-change-this-in-production-min-32-chars
LOG_LEVEL=INFO
MONITORING_API_KEY=admin-secret-key-change-this
BACKEND_CORS_ORIGINS=["http://localhost:3000"]"""

with open('.env', 'w') as f:
    f.write(content)
    
print(".env created successfully")
