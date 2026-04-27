# Implementation Plan

## Bug 1: Missing Monitoring Infrastructure

- [ ] 1. Write bug condition exploration test for Elasticsearch/Kibana deployment
  - **Property 1: Bug Condition** - Monitoring Infrastructure Not Deployed
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate Elasticsearch and Kibana are not accessible on 192.168.214.139
  - **Scoped PBT Approach**: Test concrete failing cases - Elasticsearch port 9200 and Kibana port 5601 are not accessible
  - Test implementation details from Bug Condition in design:
    - Verify Elasticsearch is NOT accessible at http://192.168.214.139:9200
    - Verify Kibana is NOT accessible at http://192.168.214.139:5601
    - Verify no Elasticsearch/Kibana containers are running on 192.168.214.139
    - Document connection refused errors and missing containers
  - The test assertions should match the Expected Behavior Properties from design (services should be accessible)
  - Run test on UNFIXED deployment
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 2. Write preservation property tests for existing services (BEFORE implementing fix)
  - **Property 2: Preservation** - Existing Services Continue Operating
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED deployment for existing services:
    - PostgreSQL database operations (queries, transactions)
    - Redis caching and task queuing
    - Response-network API endpoints (auth, users, stats)
    - Celery worker task execution
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - Test that PostgreSQL accepts connections and executes queries
    - Test that Redis accepts connections and stores/retrieves data
    - Test that API endpoints return expected responses
    - Test that Celery workers process tasks
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED deployment
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed deployment
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 3. Deploy Elasticsearch and Kibana monitoring infrastructure

  - [ ] 3.1 Create deployment function for Elasticsearch stack
    - Add `deploy_elasticsearch()` function to `deploy.sh`
    - Use `docker-compose.elasticsearch.yml` as the compose file
    - Deploy to server 192.168.214.139 (same as response-network)
    - Use rsync to sync the compose file to the server
    - Execute docker compose up with --build -d flags
    - _Bug_Condition: isBugCondition1(deployment_state) where Elasticsearch/Kibana not running on 192.168.214.139_
    - _Expected_Behavior: Elasticsearch accessible at :9200, Kibana at :5601, containers running_
    - _Preservation: Existing services (PostgreSQL, Redis, API, Celery) continue operating_
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 7.1_

  - [ ] 3.2 Add health check polling for Elasticsearch
    - Implement health check loop that polls http://192.168.214.139:9200/_cluster/health
    - Wait for status to be green or yellow before proceeding
    - Add 60-second timeout with clear error message
    - Log health check progress for debugging
    - _Requirements: 4.1, 4.3_

  - [ ] 3.3 Integrate Elasticsearch deployment into main workflow
    - Modify main deployment logic to deploy Elasticsearch before response-network
    - When deploying "response" or "all", first call deploy_elasticsearch()
    - Wait for Elasticsearch health check before proceeding with response-network
    - Add optional --skip-elasticsearch flag for testing
    - _Requirements: 4.4, 4.6_

  - [ ] 3.4 Configure Docker network connectivity
    - Ensure Elasticsearch containers can communicate with response-network containers
    - Use Docker bridge network or host network mode
    - Verify network configuration in docker-compose.elasticsearch.yml
    - Test connectivity from response-network API to Elasticsearch
    - _Requirements: 4.3, 4.6_

  - [ ] 3.5 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Monitoring Infrastructure Deployed
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify Elasticsearch is accessible at http://192.168.214.139:9200
    - Verify Kibana is accessible at http://192.168.214.139:5601
    - Verify containers are running and healthy
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 4.6_

  - [ ] 3.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Existing Services Unaffected
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm PostgreSQL, Redis, API, and Celery continue operating
    - Confirm no disruption to request processing workflow
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

## Bug 2: Request List Endpoint Failure

- [ ] 4. Write bug condition exploration test for request list endpoint
  - **Property 1: Bug Condition** - Request List Endpoint Returns 500 Error
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the endpoint returns 500 errors
  - **Scoped PBT Approach**: Test concrete failing case - GET /api/v1/requests?limit=10 with valid authentication
  - Test implementation details from Bug Condition in design:
    - Make GET request to http://192.168.214.141:8000/api/v1/requests?limit=10
    - Verify response status code is 500 (not 200)
    - Check server logs for exception traceback
    - Document the specific error (async/sync mismatch, relationship loading error)
  - The test assertions should match the Expected Behavior Properties from design (should return 200 OK)
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 5. Write preservation property tests for other API endpoints (BEFORE implementing fix)
  - **Property 2: Preservation** - Other API Endpoints Continue Working
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-affected endpoints:
    - Authentication endpoints (/api/v1/auth/login, /api/v1/auth/token)
    - User management endpoints (/api/v1/users)
    - Stats endpoints (/api/v1/requests/stats)
    - Single request endpoint (/api/v1/requests/{id})
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - Test that authentication returns valid tokens
    - Test that user endpoints enforce RBAC
    - Test that stats endpoints return valid data
    - Test that single request endpoint returns request details
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 7.5, 7.6, 7.7, 7.8_

- [ ] 6. Fix request list endpoint async/sync mismatch

  - [ ] 6.1 Add eager loading for relationships in get_requests()
    - Open file: response-network/api/crud/requests.py
    - Import selectinload: `from sqlalchemy.orm import selectinload`
    - Modify query to eagerly load result relationship
    - Add: `.options(selectinload(IncomingRequest.result))`
    - This prevents lazy loading issues in async context
    - _Bug_Condition: isBugCondition2(request) where endpoint called with AsyncSession but has sync/async mismatch_
    - _Expected_Behavior: Endpoint returns 200 OK with valid JSON response_
    - _Preservation: Other API endpoints continue working unchanged_
    - _Requirements: 5.1, 5.2, 5.3, 7.5, 7.6_

  - [ ] 6.2 Add null-safe access to result relationship
    - In get_requests() function, update result data access
    - Change: `"result": r.result.result_data if r.result else None`
    - This prevents AttributeError when result is None
    - Add similar null checks for error_message and other optional fields
    - _Requirements: 5.2, 5.3_

  - [ ] 6.3 Add exception handling to get_requests()
    - Wrap function body in try-except block
    - Catch SQLAlchemy errors and log with full traceback
    - Catch general exceptions and log for debugging
    - Re-raise exceptions to be handled by endpoint error handler
    - _Requirements: 5.2_

  - [ ] 6.4 Add error handling to list_requests() endpoint
    - Open file: response-network/api/router/request_router.py
    - Wrap endpoint logic in try-except block
    - Catch database errors and return HTTPException with 500 status
    - Catch validation errors and return HTTPException with 400 status
    - Log all errors with request context for debugging
    - _Requirements: 5.1, 5.2_

  - [ ] 6.5 Verify async consistency in database operations
    - Review all database operations in get_requests()
    - Ensure all db.execute() calls use await
    - Verify no sync SQLAlchemy methods are called
    - Check that session management is correct
    - _Requirements: 5.2_

  - [ ] 6.6 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Request List Endpoint Returns 200 OK
    - **IMPORTANT**: Re-run the SAME test from task 4 - do NOT write a new test
    - The test from task 4 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 4
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify endpoint returns 200 OK with valid JSON
    - Verify response contains paginated request data
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ] 6.7 Verify preservation tests still pass
    - **Property 2: Preservation** - Other API Endpoints Unaffected
    - **IMPORTANT**: Re-run the SAME tests from task 5 - do NOT write new tests
    - Run preservation property tests from step 5
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm authentication, user, stats, and single request endpoints work
    - Confirm RBAC enforcement is unchanged
    - _Requirements: 7.5, 7.6, 7.7, 7.8_

## Bug 3: Status Differentiation Gap

- [ ] 7. Write bug condition exploration test for status differentiation
  - **Property 1: Bug Condition** - API Does Not Differentiate Status States
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate API responses lack clear status differentiation
  - **Scoped PBT Approach**: Test concrete failing cases - pending, success, and error requests return responses without outcome field
  - Test implementation details from Bug Condition in design:
    - Create test requests with different states (pending, completed-success, completed-error)
    - Call /api/v1/requests endpoint and verify responses
    - Verify responses do NOT contain "outcome" field
    - Verify frontend would need complex logic to determine state
    - Document the ambiguity between states
  - The test assertions should match the Expected Behavior Properties from design (should have outcome field)
  - Run test on UNFIXED code (after Bug 2 is fixed)
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 8. Write preservation property tests for status management (BEFORE implementing fix)
  - **Property 2: Preservation** - Status Transitions and Database Updates Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for status management:
    - Celery worker status updates (pending → processing → completed)
    - Database status field values and transitions
    - Error handling and retry logic
    - Request lifecycle management
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - Test that status transitions work correctly
    - Test that database updates are atomic
    - Test that error handling preserves status integrity
    - Test that existing code checking status values works
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 7.9, 7.10, 7.11, 7.12_

- [ ] 9. Implement status differentiation with outcome field

  - [ ] 9.1 Add outcome computation logic to get_requests()
    - Open file: response-network/api/crud/requests.py
    - Add outcome computation logic after line 38 (in the item dictionary creation)
    - Implement logic:
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
    - Add "outcome" field to the returned dictionary
    - _Bug_Condition: isBugCondition3(api_response) where response does not differentiate status states_
    - _Expected_Behavior: Response includes outcome field with values: pending, success, error_
    - _Preservation: Status transitions and database updates unchanged_
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.6, 7.9, 7.10, 7.11, 7.12_

  - [ ] 9.2 Add outcome computation to get_request() single request endpoint
    - Open file: response-network/api/crud/requests.py
    - Find get_request() function (single request retrieval)
    - Apply the same outcome computation logic as in get_requests()
    - Ensure consistency between list and detail endpoints
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.6_

  - [ ] 9.3 Add documentation for outcome field
    - Add docstring comments to get_requests() and get_request()
    - Document outcome field values:
      - "pending": Request is pending or processing, no result yet
      - "success": Request completed successfully with results
      - "error": Request failed or completed with error
      - "unknown": Status cannot be determined (edge case)
    - Add inline comments explaining the outcome computation logic
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ] 9.4 Update Pydantic schema if exists
    - Check if response-network/api/models/schemas.py exists
    - If exists, add outcome field to Request response schema
    - Add: `outcome: Optional[str] = None` for backward compatibility
    - Add validator to ensure outcome is one of: pending, success, error, unknown
    - If schema doesn't exist, skip this step
    - _Requirements: 6.5, 6.6_

  - [ ] 9.5 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - API Differentiates Status States
    - **IMPORTANT**: Re-run the SAME test from task 7 - do NOT write a new test
    - The test from task 7 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 7
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify responses contain "outcome" field
    - Verify outcome values are correct for each status state
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ] 9.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Status Management Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 8 - do NOT write new tests
    - Run preservation property tests from step 8
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm status transitions work correctly
    - Confirm database updates are unchanged
    - Confirm existing code checking status values works
    - _Requirements: 7.9, 7.10, 7.11, 7.12_

## Final Validation

- [ ] 10. Checkpoint - Ensure all tests pass
  - Re-run all exploration tests (tasks 1, 4, 7) - all should PASS
  - Re-run all preservation tests (tasks 2, 5, 8) - all should PASS
  - Verify Elasticsearch and Kibana are accessible and healthy
  - Verify request list endpoint returns 200 OK with valid data
  - Verify API responses include outcome field with correct values
  - Test full request processing workflow end-to-end
  - Ask the user if questions arise or if additional testing is needed
