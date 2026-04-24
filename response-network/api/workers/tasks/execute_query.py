import json
from datetime import datetime
import uuid
from time import sleep
import base64

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.config import settings
from models.incoming_request import IncomingRequest
from models.request_type import RequestType
from models.query_result import QueryResult
from models.elasticsearch_config import ElasticsearchConfig
from services.external_api_handler import ExternalAPIHandler

# Setup sync database connection for Celery
sync_engine = create_engine(
    str(settings.DATABASE_URL).replace('postgresql+asyncpg', 'postgresql'),
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

@shared_task(bind=True, max_retries=3)
def execute_pending_queries(self):
    """
    Execute pending requests against Elasticsearch (mocked for now).
    """
    db = SessionLocal()
    try:
        # Get pending requests
        pending_requests = db.query(IncomingRequest).filter(
            IncomingRequest.status == "pending"
        ).limit(50).all()

        if not pending_requests:
            return {"status": "no_pending_requests"}

        processed_count = 0
        for req in pending_requests:
            try:
                # Update status to processing
                req.status = "processing"
                req.started_at = datetime.utcnow()
                req.assigned_worker = self.request.id
                db.commit()

                # Check if it is an external API call
                if req.query_type == "external_api":
                    external_api_name = (req.query_params or {}).get("api_type")
                    if not external_api_name:
                         raise ValueError("api_type not provided in query_params for external_api request")
                         
                    handler = ExternalAPIHandler(db)
                    
                    start_time = datetime.utcnow()
                    api_response = handler.execute_api_call(external_api_name, req.query_params or {})
                    end_time = datetime.utcnow()
                    
                    execution_time = int((end_time - start_time).total_seconds() * 1000)
                    
                    # Create QueryResult
                    query_result = QueryResult(
                        id=uuid.uuid4(),
                        request_id=req.id,
                        original_request_id=req.original_request_id,
                        result_data={"api_response": api_response},
                        result_count=1,
                        execution_time_ms=execution_time,
                        elasticsearch_took_ms=0,
                        cache_hit=False,
                        executed_at=end_time
                    )
                    db.add(query_result)

                    # Update Request Status
                    req.status = "completed"
                    req.completed_at = end_time
                    req.progress = 100.0
                    
                    db.commit()
                    processed_count += 1
                    continue
                
                # Default behavior: ElasticSearch Query
                # Fetch Request Type
                stmt = db.query(RequestType).filter(RequestType.name == req.query_type)
                request_type = stmt.first()
                
                if not request_type:
                     raise ValueError(f"Request Type '{req.query_type}' not found or active")

                if not request_type.elasticsearch_query_template:
                     raise ValueError(f"No query template defined for '{req.query_type}'")
                
                # Validate required parameters
                from models.request_type_parameter import RequestTypeParameter
                stmt_params = db.query(RequestTypeParameter).filter(
                    RequestTypeParameter.request_type_id == request_type.id
                )
                required_params = stmt_params.all()
                
                query_params = req.query_params or {}
                missing_params = []
                
                for param in required_params:
                    if param.is_required:
                        # Case-insensitive lookup
                        param_value = None
                        for key, val in query_params.items():
                            if key.lower() == param.placeholder_key.lower():
                                param_value = val
                                break
                        
                        if param_value is None or param_value == "":
                            missing_params.append(param.placeholder_key)
                
                if missing_params:
                    raise ValueError(
                        f"Missing required parameters: {', '.join(missing_params)}. "
                        f"Please provide values for these parameters in your request."
                    )

                # Parse and Render Query
                # Simple recursive replacement
                def render_template(template, params):
                    if isinstance(template, dict):
                        return {k: render_template(v, params) for k, v in template.items()}
                    elif isinstance(template, list):
                        return [render_template(v, params) for v in template]
                    elif isinstance(template, str):
                        for key, val in params.items():
                             # Handle simple string replacement
                             # Note: This doesn't handle type conversion automatically (e.g. number to int)
                             if f"{{{{{key}}}}}" in template:
                                  template = template.replace(f"{{{{{key}}}}}", str(val))
                        return template
                    else:
                        return template

                query_body = render_template(request_type.elasticsearch_query_template, req.query_params or {})
                
                # Execute Query - Get Elasticsearch config from runtime database
                index_name = request_type.available_indices[0] if request_type.available_indices else "default"
                
                # Try to get active Elasticsearch config from database
                es_config = None
                try:
                    es_config_result = db.query(ElasticsearchConfig).filter(
                        ElasticsearchConfig.is_active == True
                    ).first()
                    es_config = es_config_result
                except Exception as e:
                    import logging
                    logging.warning(f"Failed to load Elasticsearch config from database: {e}")
                
                # Use runtime config if available, otherwise fall back to settings
                if es_config:
                    base_url = es_config.url.rstrip('/')
                    es_auth = None
                    if es_config.username and es_config.password:
                        credentials = f"{es_config.username}:{es_config.password}"
                        encoded_credentials = base64.b64encode(credentials.encode()).decode()
                        es_auth = f"Basic {encoded_credentials}"
                else:
                    base_url = str(settings.ELASTICSEARCH_URL).rstrip('/')
                    es_auth = None
                
                es_url = f"{base_url}/{index_name}/_search"
                
                import urllib.request
                import urllib.error
                
                req_data = json.dumps(query_body).encode('utf-8')
                req_obj = urllib.request.Request(es_url, data=req_data, headers={'Content-Type': 'application/json'})
                
                # Add authentication header if needed
                if es_auth:
                    req_obj.add_header('Authorization', es_auth)
                
                try:
                    with urllib.request.urlopen(req_obj, timeout=10.0) as f:
                        response_body = f.read().decode('utf-8')
                        es_result = json.loads(response_body)
                except urllib.error.HTTPError as e:
                     if e.code == 404:
                         # Index not found or similar -> Treat as empty result
                         es_result = {"hits": {"total": {"value": 0}, "hits": []}, "took": 0}
                     else:
                         raise Exception(f"Elasticsearch Error ({e.code}): {e.read().decode('utf-8')}")
                except Exception as e:
                     raise Exception(f"Elasticsearch Connection Error: {str(e)}")

                
                # Transform Result
                hits = es_result.get("hits", {}).get("hits", [])
                result_data = {
                    "count": es_result.get("hits", {}).get("total", {}).get("value", 0),
                    "results": [h["_source"] for h in hits],
                }

                # Create QueryResult
                query_result = QueryResult(
                    id=uuid.uuid4(),
                    request_id=req.id,
                    original_request_id=req.original_request_id,
                    result_data=result_data,
                    result_count=result_data["count"],
                    execution_time_ms=es_result.get("took", 0), # Approximate
                    elasticsearch_took_ms=es_result.get("took", 0),
                    cache_hit=False,
                    executed_at=datetime.utcnow()
                )
                db.add(query_result)

                # Update Request Status
                req.status = "completed"
                req.completed_at = datetime.utcnow()
                req.progress = 100.0
                
                db.commit()
                processed_count += 1
                
            except Exception as e:
                db.rollback()
                
                # Create QueryResult with error so it gets exported to Request Network
                error_result = QueryResult(
                    id=uuid.uuid4(),
                    request_id=req.id,
                    original_request_id=req.original_request_id,
                    result_data={"error": str(e)},
                    result_count=0,
                    execution_time_ms=0,
                    elasticsearch_took_ms=0,
                    cache_hit=False,
                    executed_at=datetime.utcnow()
                )
                db.add(error_result)
                
                req.status = "failed"
                req.error_message = str(e)
                req.retry_count += 1
                req.completed_at = datetime.utcnow()
                db.commit()
                processed_count += 1
                # Continue to next request

        return {
            "status": "success",
            "processed_count": processed_count
        }
    finally:
        db.close()
