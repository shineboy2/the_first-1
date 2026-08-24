import json
from datetime import datetime
import uuid
from time import sleep
import base64
import logging

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.config import settings
from models.incoming_request import IncomingRequest
from models.request_type import RequestType
from models.query_result import QueryResult
from models.elasticsearch_config import ElasticsearchConfig
# External API handler is now loaded dynamically via HandlerRegistry

# Setup logging
logger = logging.getLogger(__name__)

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
        # First, check for stuck "processing" requests and reset them
        # A request is considered stuck if it's been in "processing" for more than 5 minutes
        from datetime import timedelta
        stuck_threshold = datetime.utcnow() - timedelta(minutes=5)
        
        stuck_requests = db.query(IncomingRequest).filter(
            IncomingRequest.status == "processing",
            IncomingRequest.started_at < stuck_threshold
        ).all()
        
        for stuck_req in stuck_requests:
            logger.warning(f"[EXECUTE_QUERY] Found stuck request {stuck_req.id} in processing state, resetting to pending")
            stuck_req.status = "pending"
            stuck_req.started_at = None
            stuck_req.assigned_worker = None
        
        if stuck_requests:
            db.commit()
        
        # Get pending requests
        pending_requests = db.query(IncomingRequest).filter(
            IncomingRequest.status == "pending"
        ).limit(50).all()

        if not pending_requests:
            return {"status": "no_pending_requests"}

        processed_count = 0
        for req in pending_requests:
            req_id = req.id  # Store ID separately to avoid state issues
            try:
                # Update status to processing
                req.status = "processing"
                req.started_at = datetime.utcnow()
                req.assigned_worker = self.request.id
                db.commit()

                # Check if it is a file-based request
                # Look up the RequestType to check execution_method
                file_req_type = db.query(RequestType).filter(
                    RequestType.name == req.query_type
                ).first()

                if file_req_type and file_req_type.execution_method == "file_request":
                    from models.file_request import FileRequest as FileRequestModel
                    from workers.tasks.file_request_sender import send_file_request

                    if not file_req_type.file_request_config_id:
                        raise ValueError(
                            f"RequestType '{req.query_type}' is configured as file_request "
                            f"but has no file_request_config_id"
                        )

                    # Create FileRequest tracker
                    file_req_obj = FileRequestModel(
                        id=uuid.uuid4(),
                        incoming_request_id=req.id,
                        file_request_config_id=file_req_type.file_request_config_id,
                        status="generating",
                    )
                    db.add(file_req_obj)
                    db.commit()

                    # Dispatch async file send task
                    send_file_request.delay(str(file_req_obj.id))
                    processed_count += 1

                    logger.info(
                        f"[EXECUTE_QUERY] File request dispatched for {req.id} "
                        f"(FileRequest: {file_req_obj.id})"
                    )
                    continue

                # Check if it is an external API call
                if req.query_type == "external_api" or (file_req_type and file_req_type.execution_method == "external_api"):
                    from services.handler_registry import HandlerRegistry
                    from models.external_api import ExternalAPI
                    
                    api_config = None
                    if file_req_type and file_req_type.execution_method == "external_api" and file_req_type.external_api_id:
                        api_config = db.query(ExternalAPI).get(file_req_type.external_api_id)
                        if not api_config:
                            raise ValueError(f"Linked ExternalAPI not found for RequestType '{req.query_type}'")
                        external_api_name = api_config.name
                    else:
                        external_api_name = (req.query_params or {}).get("api_type")
                        if not external_api_name:
                             raise ValueError("api_type not provided in query_params for legacy external_api request")
                        api_config = db.query(ExternalAPI).filter(ExternalAPI.name == external_api_name).first()
                        if not api_config:
                            raise ValueError(f"ExternalAPI '{external_api_name}' not found")
                         
                    handler = HandlerRegistry.get_handler(external_api_name, db)
                    
                    start_time = datetime.utcnow()
                    api_response = handler.execute(req.query_params or {}, api_config=api_config)
                    end_time = datetime.utcnow()
                    
                    execution_time = int((end_time - start_time).total_seconds() * 1000)
                    
                    # Update or Create QueryResult
                    existing_result = db.query(QueryResult).filter(QueryResult.request_id == req.id).first()
                    if existing_result:
                        # Update existing result
                        existing_result.result_data = {"api_response": api_response}
                        existing_result.result_count = 1
                        existing_result.execution_time_ms = execution_time
                        existing_result.elasticsearch_took_ms = 0
                        existing_result.executed_at = end_time
                        existing_result.cache_hit = False
                    else:
                        # Create new QueryResult
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
                    req.has_error = False
                    
                    db.commit()
                    processed_count += 1
                    continue

                # Check if it is an object_storage request (ES query + download from Ceph/MinIO)
                if file_req_type and file_req_type.execution_method == "object_storage":
                    from models.object_storage_config import ObjectStorageConfig
                    from services.object_storage_handler import ObjectStorageHandler

                    if not file_req_type.object_storage_config_id:
                        raise ValueError(
                            f"RequestType '{req.query_type}' is configured as object_storage "
                            f"but has no object_storage_config_id"
                        )

                    if not file_req_type.elasticsearch_query_template:
                        raise ValueError(
                            f"RequestType '{req.query_type}' is configured as object_storage "
                            f"but has no elasticsearch_query_template"
                        )

                    # Step 1: Execute ES query to get file paths
                    # (Reuse existing ES query logic)
                    def render_template(template, params):
                        if isinstance(template, dict):
                            return {k: render_template(v, params) for k, v in template.items()}
                        elif isinstance(template, list):
                            return [render_template(v, params) for v in template]
                        elif isinstance(template, str):
                            for key, val in params.items():
                                if f"{{{{{key}}}}}" in template:
                                    template = template.replace(f"{{{{{key}}}}}", str(val))
                            return template
                        else:
                            return template

                    query_body = render_template(
                        file_req_type.elasticsearch_query_template,
                        req.query_params or {}
                    )

                    index_name = ",".join(file_req_type.available_indices) if file_req_type.available_indices else "default"

                    # Get ES config
                    es_config = db.query(ElasticsearchConfig).filter(
                        ElasticsearchConfig.is_active == True
                    ).first()

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
                    import ssl

                    req_data_bytes = json.dumps(query_body).encode('utf-8')
                    logger.info(f"[OBJECT_STORAGE] Executing ES query against {es_url}")

                    req_obj_es = urllib.request.Request(
                        es_url, data=req_data_bytes,
                        headers={'Content-Type': 'application/json'}
                    )
                    if es_auth:
                        req_obj_es.add_header('Authorization', es_auth)

                    ssl_context = None
                    if es_url.startswith('https://'):
                        verify_ssl = es_config.verify_ssl if es_config else False
                        if not verify_ssl:
                            ssl_context = ssl._create_unverified_context()
                        else:
                            ssl_context = ssl.create_default_context()

                    try:
                        with urllib.request.urlopen(req_obj_es, timeout=10.0, context=ssl_context) as f:
                            response_body = f.read().decode('utf-8')
                            es_result = json.loads(response_body)
                    except urllib.error.HTTPError as e:
                        if e.code == 404:
                            es_result = {"hits": {"total": {"value": 0}, "hits": []}, "took": 0}
                        else:
                            raise Exception(f"Elasticsearch Error ({e.code}): {e.read().decode('utf-8')}")

                    hits = es_result.get("hits", {}).get("hits", [])

                    # Step 2: Load Object Storage config and download files
                    os_config = db.query(ObjectStorageConfig).filter(
                        ObjectStorageConfig.id == file_req_type.object_storage_config_id
                    ).first()
                    if not os_config:
                        raise ValueError(
                            f"ObjectStorageConfig '{file_req_type.object_storage_config_id}' not found"
                        )
                    if not os_config.is_active:
                        raise ValueError(
                            f"ObjectStorageConfig '{os_config.name}' is inactive"
                        )

                    handler = ObjectStorageHandler(os_config)
                    mapping_config = file_req_type.object_storage_mapping or {}

                    # Step 3: Enrich ES hits with base64 data from object storage
                    enrichment = handler.enrich_es_hits_with_objects(hits, mapping_config)
                    enriched_hits = enrichment["enriched_hits"]
                    os_stats = enrichment["stats"]

                    # Step 4: Build result (apply field/index mappings like standard ES flow)
                    from collections import defaultdict

                    field_map = file_req_type.field_mapping or {}
                    index_map = file_req_type.index_mapping or {}

                    grouped = defaultdict(list)
                    for h in enriched_hits:
                        source = h.get("_source", {})
                        if field_map:
                            mapped_source = {}
                            for key, value in source.items():
                                mapped_key = field_map.get(key, key)
                                mapped_source[mapped_key] = value
                            source = mapped_source

                        raw_index = h.get("_index", "unknown")
                        display_index = index_map.get(raw_index, raw_index)
                        grouped[display_index].append(source)

                    result_data = {
                        "count": es_result.get("hits", {}).get("total", {}).get("value", 0),
                        "results_by_index": dict(grouped),
                        "object_storage_stats": os_stats,
                    }

                    end_time = datetime.utcnow()
                    es_took = es_result.get("took", 0)
                    total_time = es_took + os_stats.get("download_time_ms", 0)

                    # Step 5: Save QueryResult
                    existing_result = db.query(QueryResult).filter(QueryResult.request_id == req.id).first()
                    if existing_result:
                        existing_result.result_data = result_data
                        existing_result.result_count = result_data["count"]
                        existing_result.execution_time_ms = total_time
                        existing_result.elasticsearch_took_ms = es_took
                        existing_result.executed_at = end_time
                        existing_result.cache_hit = False
                    else:
                        query_result = QueryResult(
                            id=uuid.uuid4(),
                            request_id=req.id,
                            original_request_id=req.original_request_id,
                            result_data=result_data,
                            result_count=result_data["count"],
                            execution_time_ms=total_time,
                            elasticsearch_took_ms=es_took,
                            cache_hit=False,
                            executed_at=end_time,
                        )
                        db.add(query_result)

                    req.status = "completed"
                    req.completed_at = end_time
                    req.progress = 100.0
                    req.has_error = False

                    db.commit()
                    processed_count += 1

                    logger.info(
                        f"[OBJECT_STORAGE] Request {req.id} completed: "
                        f"{os_stats['total_files_downloaded']} files downloaded, "
                        f"{os_stats['total_size_bytes']} bytes, "
                        f"{os_stats['download_time_ms']}ms download time"
                    )
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
                index_name = ",".join(request_type.available_indices) if request_type.available_indices else "default"
                
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
                import ssl
                
                req_data = json.dumps(query_body).encode('utf-8')
                
                # Log the query for debugging
                logger.info(f"[ELASTICSEARCH] Executing query against {es_url}")
                logger.debug(f"[ELASTICSEARCH] Query Payload: {json.dumps(query_body, ensure_ascii=False)}")
                
                req_obj = urllib.request.Request(es_url, data=req_data, headers={'Content-Type': 'application/json'})
                
                # Add authentication header if needed
                if es_auth:
                    req_obj.add_header('Authorization', es_auth)
                
                # Create SSL context based on verify_ssl setting
                ssl_context = None
                
                # اگر URL با https شروع می‌شود، حتماً ssl_context بسازید
                if es_url.startswith('https://'):
                    verify_ssl = False  # default: self-signed certs are common in internal networks
                    
                    if es_config:
                        verify_ssl = es_config.verify_ssl
                        logger.info(f"[ELASTICSEARCH] Config from DB: verify_ssl={verify_ssl} for {es_url}")
                    else:
                        logger.warning(f"[ELASTICSEARCH] No config from DB, using default: verify_ssl={verify_ssl} for {es_url}")
                    
                    # Create SSL context
                    if not verify_ssl:
                        # For self-signed certificates, use unverified context
                        ssl_context = ssl._create_unverified_context()
                        logger.info(f"[ELASTICSEARCH] ✅ SSL verification DISABLED for {es_url}")
                    else:
                        # For verified certificates, use default context
                        ssl_context = ssl.create_default_context()
                        logger.info(f"[ELASTICSEARCH] ✅ SSL verification ENABLED for {es_url}")
                
                try:
                    with urllib.request.urlopen(req_obj, timeout=10.0, context=ssl_context) as f:
                        response_body = f.read().decode('utf-8')
                        es_result = json.loads(response_body)
                except urllib.error.HTTPError as e:
                     if e.code == 404:
                         # Index not found or similar -> Treat as empty result
                         logger.warning(f"[ELASTICSEARCH] Got 404 Not Found from {es_url}. The index '{index_name}' might not exist.")
                         es_result = {"hits": {"total": {"value": 0}, "hits": []}, "took": 0}
                     else:
                         raise Exception(f"Elasticsearch Error ({e.code}): {e.read().decode('utf-8')}")
                except Exception as e:
                     raise Exception(f"Elasticsearch Connection Error: {str(e)}")

                
                # Transform Result — Grouped by index with field & index mapping
                from collections import defaultdict

                hits = es_result.get("hits", {}).get("hits", [])

                # Load mappings from RequestType
                field_map = request_type.field_mapping or {}
                index_map = request_type.index_mapping or {}

                grouped = defaultdict(list)
                for h in hits:
                    source = h.get("_source", {})

                    # Apply field mapping (rename keys)
                    if field_map:
                        mapped_source = {}
                        for key, value in source.items():
                            mapped_key = field_map.get(key, key)
                            mapped_source[mapped_key] = value
                        source = mapped_source

                    # Apply index mapping (alias real index name)
                    raw_index = h.get("_index", "unknown")
                    display_index = index_map.get(raw_index, raw_index)

                    grouped[display_index].append(source)

                result_data = {
                    "count": es_result.get("hits", {}).get("total", {}).get("value", 0),
                    "results_by_index": dict(grouped),
                }

                # Update or Create QueryResult
                existing_result = db.query(QueryResult).filter(QueryResult.request_id == req.id).first()
                if existing_result:
                    # Update existing result
                    existing_result.result_data = result_data
                    existing_result.result_count = result_data["count"]
                    existing_result.execution_time_ms = es_result.get("took", 0)
                    existing_result.elasticsearch_took_ms = es_result.get("took", 0)
                    existing_result.executed_at = datetime.utcnow()
                    existing_result.cache_hit = False
                else:
                    # Create new QueryResult
                    query_result = QueryResult(
                        id=uuid.uuid4(),
                        request_id=req.id,
                        original_request_id=req.original_request_id,
                        result_data=result_data,
                        result_count=result_data["count"],
                        execution_time_ms=es_result.get("took", 0),
                        elasticsearch_took_ms=es_result.get("took", 0),
                        cache_hit=False,
                        executed_at=datetime.utcnow()
                    )
                    db.add(query_result)

                # Update Request Status
                req.status = "completed"
                req.completed_at = datetime.utcnow()
                req.progress = 100.0
                req.has_error = False
                
                db.commit()
                processed_count += 1
                
            except Exception as e:
                logger.error(f"[EXECUTE_QUERY] Error processing request {req_id}: {str(e)}", exc_info=True)
                db.rollback()
                
                # Fetch fresh copy of request from database after rollback
                fresh_req = db.query(IncomingRequest).filter(IncomingRequest.id == req_id).first()
                if fresh_req:
                    # Try to update existing QueryResult instead of creating a new one
                    existing_result = db.query(QueryResult).filter(QueryResult.request_id == fresh_req.id).first()
                    
                    if existing_result:
                        # Update existing result with error
                        existing_result.result_data = {"error": str(e)}
                        existing_result.result_count = 0
                        existing_result.execution_time_ms = 0
                        existing_result.elasticsearch_took_ms = 0
                        existing_result.executed_at = datetime.utcnow()
                        logger.info(f"[EXECUTE_QUERY] Updated existing QueryResult for request {req_id}")
                    else:
                        # Create new QueryResult with error
                        error_result = QueryResult(
                            id=uuid.uuid4(),
                            request_id=fresh_req.id,
                            original_request_id=fresh_req.original_request_id,
                            result_data={"error": str(e)},
                            result_count=0,
                            execution_time_ms=0,
                            elasticsearch_took_ms=0,
                            cache_hit=False,
                            executed_at=datetime.utcnow()
                        )
                        db.add(error_result)
                    
                    # Increment retry count
                    fresh_req.retry_count += 1
                    fresh_req.error_message = str(e)
                    fresh_req.has_error = True
                    
                    # Check if we should auto-retry or mark as failed
                    max_retries = 3  # Same as Celery max_retries
                    if fresh_req.retry_count < max_retries:
                        # Auto-retry: set status back to pending
                        fresh_req.status = "pending"
                        fresh_req.started_at = None  # Reset started time
                        fresh_req.assigned_worker = None  # Reset worker assignment
                        logger.info(f"[EXECUTE_QUERY] Request {req_id} will be retried (attempt {fresh_req.retry_count}/{max_retries})")
                    else:
                        # Max retries exceeded: mark as failed
                        fresh_req.status = "failed"
                        fresh_req.completed_at = datetime.utcnow()
                        logger.error(f"[EXECUTE_QUERY] Request {req_id} exceeded max retries ({max_retries}), marked as failed")
                    
                    db.commit()
                    processed_count += 1
                else:
                    logger.error(f"[EXECUTE_QUERY] Could not fetch request {req_id} after rollback")
                # Continue to next request

        return {
            "status": "success",
            "processed_count": processed_count
        }
    finally:
        db.close()
