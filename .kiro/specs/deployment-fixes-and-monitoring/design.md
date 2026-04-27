# Deployment Fixes and Monitoring Bugfix Design

## Overview

This design addresses three critical bugs in the air-gapped request/response network system:

1. **Missing Monitoring Infrastructure (Bug 1)**: Elasticsearch and Kibana are not deployed on server 192.168.214.139, preventing log aggregation and system monitoring
2. **Request List Endpoint Failure (Bug 2)**: The `/api/v1/requests` endpoint returns 500 Internal Server Error due to async/sync mismatch in database operations
3. **Status Differentiation Gap (Bug 3)**: The API cannot distinguish between queries with no response versus queries with errors, despite the database schema supporting granular status tracking

The fix approach is minimal and targeted: deploy monitoring infrastructure using existing docker-compose configuration, fix the async/sync mismatch in the CRUD layer, and enhance the API response to differentiate status states using existing database fields.

## Glossary

- **Bug_Condition_1 (C1)**: Elasticsearch/Kibana services are not running on 192.168.214.139
- **Bug_Condition_2 (C2)**: The `/api/v1/requests` endpoint is called with async database session but uses sync query methods
- **Bug_Condition_3 (C3)**: API responses do not differentiate between "no result yet" vs "error result" vs "success result" states
- **Property (P)**: The desired behavior - monitoring services accessible, endpoint returns valid responses, status differentiation clear
- **Preservation**: Existing services (PostgreSQL, Redis, API, Celery) must continue operating without disruption
- **IncomingRequest**: The SQLAlchemy model in `response-network/api/models/incoming_request.py` that stores request metadata
- **QueryResult**: The SQLAlchemy model in `response-network/api/models/query_result.py` that stores query execution results
- **get_requests()**: The CRUD function in `response-network/api/crud/requests.py` that retrieves paginated request lists
- **AsyncSession**: SQLAlchemy 2.0 async database session used throughout the response-network API

## Bug Details

### Bug 1: Missing Monitoring Infrastructure

#### Bug Condition

The bug manifests when attempting to access Elasticsearch or Kibana on server 192.168.214.139. The services are not deployed despite being referenced in the response-network docker-compose configuration.

**Formal Specification:**
```
FUNCTION isBugCondition1(deployment_state)
  INPUT: deployment_state of type DeploymentState
  OUTPUT: boolean
  
  RETURN deployment_state.server == "192.168.214.139"
         AND NOT service_running("elasticsearch", 9200)
         AND NOT service_running("kibana", 5601)
         AND response_network_references_elasticsearch("http://192.168.214.139:9200")
END FUNCTION
```

#### Examples

- **Accessing Elasticsearch**: `curl http://192.168.214.139:9200` → Connection refused (expected: cluster health response)
- **Accessing Kibana**: Navigate to `http://192.168.214.139:5601` → Connection refused (expected: Kibana UI)
- **Response Network Queries**: Celery workers attempt to log to Elasticsearch → Connection errors in logs
- **Docker Compose Check**: `docker ps | grep elasticsearch` on 192.168.214.139 → No containers found

### Bug 2: Request List Endpoint Failure

#### Bug Condition

The bug manifests when the `/api/v1/requests` endpoint is called. The `get_requests()` function in `crud/requests.py` uses async/await syntax but the underlying query execution may have sync/async mismatches causing 500 errors.

**Formal Specification:**
```
FUNCTION isBugCondition2(request)
  INPUT: request of type HTTPRequest
  OUTPUT: boolean
  
  RETURN request.path == "/api/v1/requests"
         AND request.method == "GET"
         AND database_session_type == "AsyncSession"
         AND crud_function_has_async_await_mismatch()
END FUNCTION
```

#### Examples

- **Basic Request**: `GET http://192.168.214.141:8000/api/v1/requests?limit=10` → 500 Internal Server Error (expected: 200 OK with JSON array)
- **With Status Filter**: `GET /api/v1/requests?status=pending` → 500 Internal Server Error (expected: filtered results)
- **Admin Access**: Admin user calls endpoint → 500 error (expected: all requests visible)
- **User Access**: Regular user calls endpoint → 500 error (expected: only their requests visible)

### Bug 3: Status Differentiation Gap

#### Bug Condition

The bug manifests when the API returns request data. The response does not differentiate between requests with no result yet (pending/processing) versus requests that completed with errors versus requests that completed successfully.

**Formal Specification:**
```
FUNCTION isBugCondition3(api_response)
  INPUT: api_response of type APIResponse
  OUTPUT: boolean
  
  RETURN api_response.contains_request_data()
         AND database_has_status_field_with_values(['pending', 'processing', 'completed', 'failed'])
         AND database_has_has_error_field()
         AND database_has_result_relationship()
         AND NOT api_response_differentiates_status_states()
END FUNCTION
```

#### Examples

- **Pending Request**: Request with `status='pending'`, `result=None` → API returns generic response (expected: clear "pending" indicator)
- **Success Result**: Request with `status='completed'`, `has_error=False`, `result.result_data={...}` → API returns same format as error (expected: clear "success" indicator with data)
- **Error Result**: Request with `status='failed'`, `has_error=True`, `error_message="Query timeout"` → API returns same format as pending (expected: clear "error" indicator with message)
- **Frontend Display**: UI cannot show different states for "waiting", "success", "error" → All look the same

## Expected Behavior

### Bug 1: Monitoring Infrastructure Deployment

**Expected Correct Behavior:**

When Elasticsearch and Kibana are properly deployed on 192.168.214.139, the following SHALL occur:

- Elasticsearch SHALL respond to health checks at `http://192.168.214.139:9200`
- Kibana SHALL be accessible at `http://192.168.214.139:5601`
- Response-network services SHALL successfully connect to Elasticsearch for logging
- Docker containers SHALL start automatically with the server
- Existing services (PostgreSQL, Redis, API, Celery) SHALL continue operating without disruption

### Preservation Requirements

**Unchanged Behaviors:**
- PostgreSQL, Redis, API, and Celery worker containers must continue to operate exactly as before
- Request processing workflow (import → execute → export) must remain unchanged
- FTP synchronization between networks must continue working
- User authentication and authorization must remain unchanged
- All existing API endpoints must continue functioning

**Scope:**
All operations that do NOT involve Elasticsearch/Kibana deployment should be completely unaffected by this fix. This includes:
- Database operations and migrations
- Redis caching and task queuing
- API request handling
- Celery task execution
- FTP file transfers

### Bug 2: Request List Endpoint Fix

**Expected Correct Behavior:**

When the `/api/v1/requests` endpoint is called, the following SHALL occur:

- The endpoint SHALL return HTTP 200 OK with valid JSON response
- The response SHALL include paginated request data with proper structure
- Async database operations SHALL execute correctly without blocking
- RBAC SHALL be enforced (non-admin users see only their requests)
- Pagination parameters SHALL be respected (page, size, skip, limit)

### Preservation Requirements

**Unchanged Behaviors:**
- Authentication and authorization logic must remain unchanged
- Request filtering by status and user_id must continue working
- Pagination logic must remain unchanged
- Response schema structure must remain compatible with frontend
- Other CRUD operations (get_request, get_request_stats) must continue working

**Scope:**
All other API endpoints and database operations should be completely unaffected by this fix. This includes:
- User management endpoints
- Authentication endpoints
- Stats and monitoring endpoints
- Admin panel endpoints

### Bug 3: Status Differentiation Implementation

**Expected Correct Behavior:**

When the API returns request data, the following SHALL occur:

- Requests with `status='pending'` or `status='processing'` SHALL be clearly marked as "in progress"
- Requests with `status='completed'` and `has_error=False` SHALL be clearly marked as "success" with result data
- Requests with `status='failed'` or `has_error=True` SHALL be clearly marked as "error" with error message
- The response SHALL include a computed `outcome` field with values: "pending", "success", "error"
- Frontend SHALL be able to display different UI states based on the outcome field

### Preservation Requirements

**Unchanged Behaviors:**
- Database schema must remain unchanged (no new columns)
- Existing status field values must continue to be used
- Status transitions in Celery workers must remain unchanged
- Existing code that checks status values must continue working
- Response schema structure must remain backward compatible

**Scope:**
All database operations and status management logic should be completely unaffected by this fix. This includes:
- Celery worker status updates
- Request lifecycle management
- Error handling and retry logic
- Database constraints and relationships

## Hypothesized Root Cause

### Bug 1: Missing Monitoring Infrastructure

Based on the bug description and codebase analysis, the root cause is:

1. **Deployment Script Gap**: The `deploy.sh` script deploys `request-network` and `response-network` but does not deploy the Elasticsearch/Kibana stack defined in `docker-compose.elasticsearch.yml`

2. **Separate Compose File**: Elasticsearch and Kibana are defined in a separate `docker-compose.elasticsearch.yml` file at the repository root, not integrated into the response-network deployment

3. **Manual Deployment Required**: The monitoring stack requires separate manual deployment steps that were not executed on server 192.168.214.139

4. **Configuration Reference**: The response-network docker-compose.yml references `ELASTICSEARCH_URL=http://192.168.214.139:9200` but assumes the service is already running externally

### Bug 2: Request List Endpoint Failure

Based on the code analysis, the most likely root cause is:

1. **Async/Sync Mismatch**: The `get_requests()` function in `crud/requests.py` uses `await db.execute()` correctly, but may have issues with how the results are processed or how the session is managed

2. **Result Processing Error**: The manual dictionary conversion in lines 24-38 of `crud/requests.py` may fail when accessing related objects (User, QueryResult) due to lazy loading issues in async context

3. **Relationship Loading**: The `outerjoin(User, ...)` and accessing `r.result.result_data` may trigger additional queries that fail in async context without proper `selectinload` or `joinedload` strategies

4. **Exception Handling**: The endpoint may not have proper exception handling, causing unhandled exceptions to bubble up as 500 errors

### Bug 3: Status Differentiation Gap

Based on the requirements and code analysis, the root cause is:

1. **Incomplete Response Mapping**: The `get_requests()` function in `crud/requests.py` returns all database fields but does not compute a derived `outcome` field that clearly indicates the request state

2. **Frontend Interpretation Gap**: The frontend receives `status`, `error`, and `result` fields separately but has no single field to determine "is this pending, success, or error?"

3. **Status Field Overloading**: The `status` field has values like 'pending', 'processing', 'completed', 'failed' but 'completed' doesn't distinguish between success and error

4. **Missing Business Logic**: The API layer does not implement business logic to interpret the combination of `status`, `has_error`, and `result` fields into a clear outcome state

## Correctness Properties

Property 1: Bug Condition 1 - Monitoring Infrastructure Deployment

_For any_ deployment operation on server 192.168.214.139 where Elasticsearch and Kibana are required, the deployment process SHALL successfully start both services, make them accessible on their respective ports (9200, 5601), and configure them to start automatically on server boot.

**Validates: Requirements 4.1, 4.2, 4.3, 4.5, 4.6**

Property 2: Bug Condition 2 - Request List Endpoint Success

_For any_ HTTP GET request to `/api/v1/requests` with valid authentication, the endpoint SHALL return HTTP 200 OK with a properly formatted JSON response containing paginated request data, without throwing unhandled exceptions.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

Property 3: Bug Condition 3 - Status Differentiation

_For any_ request data returned by the API, the response SHALL include a computed `outcome` field that clearly indicates whether the request is "pending" (no result yet), "success" (completed with results), or "error" (failed or completed with error), based on the combination of `status`, `has_error`, and `result` fields.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6**

Property 4: Preservation - Existing Services Unaffected

_For any_ existing service (PostgreSQL, Redis, API, Celery workers) that was operational before the fixes, the service SHALL continue to operate with the same behavior, performance, and reliability after all three bugs are fixed.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.9, 7.10, 7.11, 7.12**

Property 5: Preservation - API Compatibility

_For any_ API endpoint that is NOT `/api/v1/requests`, the endpoint SHALL produce exactly the same responses and behavior as before the fixes, preserving backward compatibility for all API consumers.

**Validates: Requirements 7.5, 7.6, 7.7, 7.8**

## Fix Implementation

### Bug 1: Deploy Monitoring Infrastructure

Assuming our root cause analysis is correct:

**File**: `deploy.sh`

**Function**: `deploy_network()`

**Specific Changes**:

1. **Add Elasticsearch Deployment Function**: Create a new function `deploy_elasticsearch()` that deploys the monitoring stack to 192.168.214.139
   - Use `docker-compose.elasticsearch.yml` as the compose file
   - Deploy to the same server as response-network (192.168.214.139)
   - Ensure network connectivity between response-network and elasticsearch containers

2. **Integrate into Deployment Flow**: Modify the main deployment logic to deploy Elasticsearch before response-network
   - When deploying "response" or "all", first deploy Elasticsearch
   - Wait for Elasticsearch health check before proceeding with response-network

3. **Add Health Check**: Implement a health check loop that waits for Elasticsearch to be ready
   - Poll `http://192.168.214.139:9200/_cluster/health` until status is green or yellow
   - Timeout after 60 seconds with clear error message

4. **Update Docker Compose Network**: Ensure the Elasticsearch containers can communicate with response-network containers
   - Use Docker bridge network or host network mode
   - Configure firewall rules if necessary

5. **Add Deployment Flag**: Add optional `--skip-elasticsearch` flag to allow deploying response-network without Elasticsearch for testing

**Alternative Approach**: If separate deployment is preferred, create a standalone `deploy-elasticsearch.sh` script and document the deployment order in README.

### Bug 2: Fix Request List Endpoint

Assuming our root cause analysis is correct:

**File**: `response-network/api/crud/requests.py`

**Function**: `get_requests()`

**Specific Changes**:

1. **Add Eager Loading**: Use `selectinload()` or `joinedload()` to eagerly load the `result` relationship
   - Import: `from sqlalchemy.orm import selectinload`
   - Modify query: `query = select(IncomingRequest, User.username).options(selectinload(IncomingRequest.result)).outerjoin(...)`

2. **Fix Result Access**: Add null-safe access to `r.result.result_data`
   - Change: `"result": r.result.result_data if r.result else None`
   - This prevents AttributeError when result relationship is None

3. **Add Exception Handling**: Wrap the function body in try-except to catch and log errors
   - Log the full exception with traceback for debugging
   - Re-raise as HTTPException with appropriate status code

4. **Verify Async Consistency**: Ensure all database operations use `await` consistently
   - Check that `db.execute()` is always awaited
   - Verify no sync SQLAlchemy methods are called

**File**: `response-network/api/router/request_router.py`

**Function**: `list_requests()`

**Specific Changes**:

1. **Add Error Handling**: Wrap the endpoint logic in try-except block
   - Catch database errors and return 500 with error details
   - Catch validation errors and return 400
   - Log all errors for debugging

2. **Add Response Validation**: Validate the response structure before returning
   - Ensure all required fields are present
   - Handle edge cases (empty results, null values)

### Bug 3: Implement Status Differentiation

Assuming our root cause analysis is correct:

**File**: `response-network/api/crud/requests.py`

**Function**: `get_requests()` and `get_request()`

**Specific Changes**:

1. **Add Outcome Computation**: Add a computed `outcome` field to the response dictionary
   - Logic:
     ```python
     if r.status in ['pending', 'processing']:
         outcome = 'pending'
     elif r.has_error or r.status == 'failed':
         outcome = 'error'
     elif r.status == 'completed' and r.result:
         outcome = 'success'
     else:
         outcome = 'unknown'
     ```

2. **Add Outcome Field to Response**: Include the `outcome` field in the returned dictionary
   - Add: `"outcome": outcome` to the item dictionary (line 38)

3. **Update get_request()**: Apply the same outcome computation logic to the single request endpoint
   - Ensure consistency between list and detail endpoints

4. **Add Documentation**: Add docstring comments explaining the outcome field values
   - Document: "pending" = no result yet, "success" = completed with results, "error" = failed or error

**File**: `response-network/api/models/schemas.py` (if exists)

**Specific Changes**:

1. **Update Pydantic Schema**: Add `outcome` field to the Request response schema
   - Add: `outcome: str` field with description
   - Add validator to ensure outcome is one of: "pending", "success", "error", "unknown"

2. **Maintain Backward Compatibility**: Make the `outcome` field optional initially
   - Use: `outcome: Optional[str] = None`
   - This allows gradual frontend migration

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate each bug on unfixed code, then verify the fixes work correctly and preserve existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate all three bugs BEFORE implementing the fixes. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

#### Bug 1: Missing Monitoring Infrastructure

**Test Plan**: Attempt to access Elasticsearch and Kibana on server 192.168.214.139 and verify they are not accessible. Check docker containers and network connectivity.

**Test Cases**:
1. **Elasticsearch Health Check**: `curl http://192.168.214.139:9200/_cluster/health` (will fail with connection refused on unfixed deployment)
2. **Kibana Access Check**: `curl http://192.168.214.139:5601/api/status` (will fail with connection refused on unfixed deployment)
3. **Docker Container Check**: `ssh response@192.168.214.139 "docker ps | grep elasticsearch"` (will show no containers on unfixed deployment)
4. **Response Network Logs**: Check response-network API logs for Elasticsearch connection errors (will show errors on unfixed deployment)

**Expected Counterexamples**:
- Connection refused errors when accessing Elasticsearch and Kibana
- No Elasticsearch/Kibana containers running on 192.168.214.139
- Response-network logs showing Elasticsearch connection failures

#### Bug 2: Request List Endpoint Failure

**Test Plan**: Call the `/api/v1/requests` endpoint with valid authentication and observe the 500 error. Check server logs for the exception details.

**Test Cases**:
1. **Basic Request**: `curl -H "Authorization: Bearer $TOKEN" http://192.168.214.141:8000/api/v1/requests?limit=10` (will return 500 on unfixed code)
2. **With Status Filter**: `curl -H "Authorization: Bearer $TOKEN" http://192.168.214.141:8000/api/v1/requests?status=pending` (will return 500 on unfixed code)
3. **Check Server Logs**: `docker logs response-api | tail -50` (will show exception traceback on unfixed code)
4. **Test Other Endpoints**: Verify `/api/v1/requests/{id}` and `/api/v1/requests/stats` work correctly (may also fail on unfixed code)

**Expected Counterexamples**:
- HTTP 500 Internal Server Error responses
- Exception tracebacks in server logs showing async/sync mismatch or relationship loading errors
- Possible AttributeError or SQLAlchemy relationship loading errors

#### Bug 3: Status Differentiation Gap

**Test Plan**: Call the `/api/v1/requests` endpoint (after fixing Bug 2) and observe that responses do not include an `outcome` field or clear status differentiation.

**Test Cases**:
1. **Pending Request**: Create a pending request and verify the API response does not clearly indicate "pending" state (will lack outcome field on unfixed code)
2. **Completed Request**: Create a completed request with results and verify the API response does not clearly indicate "success" state (will lack outcome field on unfixed code)
3. **Failed Request**: Create a failed request and verify the API response does not clearly indicate "error" state (will lack outcome field on unfixed code)
4. **Frontend Simulation**: Attempt to determine request outcome from API response using only `status`, `error`, and `result` fields (will require complex logic on unfixed code)

**Expected Counterexamples**:
- API responses missing `outcome` field
- Frontend code requiring complex conditional logic to determine request state
- Ambiguity between "completed with error" and "completed with success"

### Fix Checking

**Goal**: Verify that for all inputs where each bug condition holds, the fixed system produces the expected behavior.

#### Bug 1: Monitoring Infrastructure

**Pseudocode:**
```
FOR ALL deployment_state WHERE isBugCondition1(deployment_state) DO
  result := deploy_elasticsearch(deployment_state)
  ASSERT elasticsearch_accessible("http://192.168.214.139:9200")
  ASSERT kibana_accessible("http://192.168.214.139:5601")
  ASSERT docker_containers_running(["elasticsearch", "kibana"])
END FOR
```

**Test Cases**:
- Deploy Elasticsearch using updated `deploy.sh` script
- Verify Elasticsearch health check returns green/yellow status
- Verify Kibana UI is accessible
- Verify response-network can connect to Elasticsearch
- Verify containers restart automatically after server reboot

#### Bug 2: Request List Endpoint

**Pseudocode:**
```
FOR ALL request WHERE isBugCondition2(request) DO
  result := call_endpoint("/api/v1/requests", request.params, request.auth)
  ASSERT result.status_code == 200
  ASSERT result.json_valid()
  ASSERT result.contains_request_data()
END FOR
```

**Test Cases**:
- Call `/api/v1/requests` with various pagination parameters
- Call with different status filters
- Call as admin user (should see all requests)
- Call as regular user (should see only their requests)
- Verify response structure matches expected schema

#### Bug 3: Status Differentiation

**Pseudocode:**
```
FOR ALL api_response WHERE isBugCondition3(api_response) DO
  result := add_outcome_field(api_response)
  ASSERT result.has_field("outcome")
  ASSERT result.outcome IN ["pending", "success", "error", "unknown"]
  ASSERT outcome_matches_status(result.outcome, result.status, result.has_error, result.result)
END FOR
```

**Test Cases**:
- Verify pending requests have `outcome="pending"`
- Verify completed requests with results have `outcome="success"`
- Verify failed requests have `outcome="error"`
- Verify requests with `has_error=True` have `outcome="error"`
- Verify outcome field is consistent across list and detail endpoints

### Preservation Checking

**Goal**: Verify that for all inputs where the bug conditions do NOT hold, the fixed system produces the same result as the original system.

**Pseudocode:**
```
FOR ALL operation WHERE NOT (isBugCondition1(operation) OR isBugCondition2(operation) OR isBugCondition3(operation)) DO
  ASSERT system_behavior_after_fix(operation) = system_behavior_before_fix(operation)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for non-affected operations, then write property-based tests capturing that behavior.

**Test Cases**:

1. **Existing Services Preservation**: Verify PostgreSQL, Redis, API, and Celery continue working after Elasticsearch deployment
   - Test database queries and transactions
   - Test Redis caching and task queuing
   - Test API authentication and authorization
   - Test Celery task execution

2. **Other Endpoints Preservation**: Verify all other API endpoints continue working after request list fix
   - Test `/api/v1/users` endpoints
   - Test `/api/v1/auth` endpoints
   - Test `/api/v1/stats` endpoints
   - Test admin panel endpoints

3. **Status Management Preservation**: Verify status transitions and database updates continue working after status differentiation
   - Test Celery worker status updates
   - Test request lifecycle (pending → processing → completed)
   - Test error handling and retry logic
   - Test database constraints

4. **Request Processing Preservation**: Verify the full request processing workflow continues working
   - Test request import from FTP
   - Test query execution
   - Test result export to FTP
   - Test result import in request-network

### Unit Tests

#### Bug 1: Monitoring Infrastructure
- Test Elasticsearch deployment script execution
- Test health check polling logic
- Test Docker network configuration
- Test container startup order

#### Bug 2: Request List Endpoint
- Test `get_requests()` with various filters
- Test pagination logic
- Test RBAC enforcement
- Test error handling for database errors
- Test relationship eager loading

#### Bug 3: Status Differentiation
- Test outcome computation logic for all status combinations
- Test outcome field presence in responses
- Test backward compatibility with existing clients
- Test edge cases (null result, missing error message)

### Property-Based Tests

#### Bug 1: Monitoring Infrastructure
- Generate random deployment configurations and verify Elasticsearch always starts correctly
- Generate random network configurations and verify connectivity
- Test that deployment is idempotent (running twice produces same result)

#### Bug 2: Request List Endpoint
- Generate random pagination parameters and verify responses are always valid
- Generate random filter combinations and verify no 500 errors
- Generate random user permissions and verify RBAC is always enforced
- Test that concurrent requests do not cause race conditions

#### Bug 3: Status Differentiation
- Generate random request states and verify outcome is always computed correctly
- Generate random combinations of status, has_error, and result fields and verify outcome logic
- Test that outcome field is always present and valid
- Test that outcome computation is deterministic (same input always produces same outcome)

### Integration Tests

#### Bug 1: Monitoring Infrastructure
- Deploy full stack (Elasticsearch + response-network) and verify end-to-end logging
- Test log ingestion from API to Elasticsearch
- Test Kibana dashboard creation and visualization
- Test system behavior during Elasticsearch downtime

#### Bug 2: Request List Endpoint
- Test full request lifecycle from submission to result retrieval
- Test pagination across large datasets
- Test concurrent access by multiple users
- Test API performance under load

#### Bug 3: Status Differentiation
- Test frontend integration with new outcome field
- Test request state transitions and outcome updates
- Test error scenarios and outcome field accuracy
- Test backward compatibility with old frontend versions
