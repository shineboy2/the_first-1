"""
Comprehensive endpoint testing script for Response Network API
Tests all available endpoints and generates a detailed report
"""
import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime
import sys

BASE_URL = "http://localhost:8001"
API_V1 = "/api/v1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.session = requests.Session()
        self.results = {
            'passed': [],
            'failed': [],
            'skipped': []
        }
    
    def print_status(self, endpoint: str, method: str, status: str, details: str = ""):
        if status == "PASS":
            color = Colors.GREEN
            self.results['passed'].append(f"{method} {endpoint}")
        elif status == "FAIL":
            color = Colors.RED
            self.results['failed'].append(f"{method} {endpoint}: {details}")
        else:
            color = Colors.YELLOW
            self.results['skipped'].append(f"{method} {endpoint}: {details}")
        
        print(f"{color}[{status}]{Colors.RESET} {method:6} {endpoint:50} {details}")
    
    def test_endpoint(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     auth: bool = True, expected_status: list = [200, 201], 
                     description: str = "") -> bool:
        """Test a single endpoint"""
        url = f"{self.base_url}{API_V1}{endpoint}"
        headers = {}
        
        if auth and self.token:
            headers['Authorization'] = f"Bearer {self.token}"
        
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers)
            elif method == "POST":
                headers['Content-Type'] = 'application/json'
                response = self.session.post(url, json=data, headers=headers)
            elif method == "PUT":
                headers['Content-Type'] = 'application/json'
                response = self.session.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                self.print_status(endpoint, method, "SKIP", f"Unsupported method")
                return False
            
            if response.status_code in expected_status:
                self.print_status(endpoint, method, "PASS", f"Status: {response.status_code}")
                return True
            else:
                details = f"Status: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        details += f" - {error_data['detail']}"
                except:
                    pass
                self.print_status(endpoint, method, "FAIL", details)
                return False
                
        except requests.exceptions.ConnectionError:
            self.print_status(endpoint, method, "FAIL", "Connection failed - Is server running?")
            return False
        except Exception as e:
            self.print_status(endpoint, method, "FAIL", f"Error: {str(e)}")
            return False
    
    def login(self, username: str = "admin", password: str = "admin123"):
        """Login and get access token"""
        print(f"\n{Colors.BLUE}=== AUTHENTICATION ==={Colors.RESET}")
        url = f"{self.base_url}{API_V1}/auth/login"
        
        try:
            response = self.session.post(
                url,
                data={
                    'username': username,
                    'password': password
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.print_status("/auth/login", "POST", "PASS", f"Token received")
                return True
            else:
                self.print_status("/auth/login", "POST", "FAIL", 
                                f"Status: {response.status_code} - Check credentials")
                return False
        except Exception as e:
            self.print_status("/auth/login", "POST", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print(f"\n{Colors.BLUE}=== AUTH ENDPOINTS ==={Colors.RESET}")
        
        self.test_endpoint("GET", "/auth/me", auth=True)
        self.test_endpoint("POST", "/auth/logout", auth=True)
    
    def test_system_endpoints(self):
        """Test system health and stats endpoints"""
        print(f"\n{Colors.BLUE}=== SYSTEM ENDPOINTS ==={Colors.RESET}")
        
        self.test_endpoint("GET", "/system/health", auth=False)
        self.test_endpoint("GET", "/system/health/detailed", auth=True)
        self.test_endpoint("GET", "/stats", auth=True)
        self.test_endpoint("GET", "/system/logs", auth=True)
    
    def test_monitoring_endpoints(self):
        """Test monitoring endpoints"""
        print(f"\n{Colors.BLUE}=== MONITORING ENDPOINTS ==={Colors.RESET}")
        
        self.test_endpoint("GET", "/monitoring/requests", auth=False)
        self.test_endpoint("GET", "/monitoring/queries", auth=False)
        self.test_endpoint("GET", "/monitoring/system/health", auth=False)
        self.test_endpoint("GET", "/monitoring/system/stats", auth=False)
        self.test_endpoint("GET", "/monitoring/logs", auth=False)
    
    def test_stats_endpoints(self):
        """Test statistics endpoints"""
        print(f"\n{Colors.BLUE}=== STATS ENDPOINTS ==={Colors.RESET}")
        
        self.test_endpoint("GET", "/stats/", auth=True)
        self.test_endpoint("GET", "/stats/queues", auth=True)
        self.test_endpoint("GET", "/stats/workers", auth=True)
        self.test_endpoint("GET", "/stats/cache", auth=True)
    
    def test_user_endpoints(self):
        """Test user management endpoints"""
        print(f"\n{Colors.BLUE}=== USER ENDPOINTS ==={Colors.RESET}")
        
        self.test_endpoint("GET", "/users", auth=True)
        
        new_user_data = {
            "username": f"testuser_{datetime.now().timestamp()}",
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "password": "Test123!@#",
            "profile_type": "user",
            "is_active": True
        }
        
        response = requests.post(
            f"{self.base_url}{API_V1}/users",
            json=new_user_data,
            headers={'Authorization': f"Bearer {self.token}"}
        )
        
        if response.status_code in [200, 201]:
            user_id = response.json().get('id')
            self.print_status("/users", "POST", "PASS", f"User created: {user_id}")
            
            self.test_endpoint("GET", f"/users/{user_id}", auth=True)
            
            update_data = {"is_active": False}
            self.test_endpoint("PUT", f"/users/{user_id}", data=update_data, auth=True)
            
            self.test_endpoint("POST", f"/users/{user_id}/suspend", auth=True)
            self.test_endpoint("POST", f"/users/{user_id}/activate", auth=True)
            
            self.test_endpoint("DELETE", f"/users/{user_id}", auth=True, expected_status=[200, 204])
        else:
            self.print_status("/users", "POST", "FAIL", 
                            f"Status: {response.status_code} - {response.text[:100]}")
    
    def test_request_endpoints(self):
        """Test request handling endpoints"""
        print(f"\n{Colors.BLUE}=== REQUEST ENDPOINTS ==={Colors.RESET}")
        
        self.test_endpoint("GET", "/requests", auth=True)
        self.test_endpoint("GET", "/requests?status=pending", auth=True)
        self.test_endpoint("GET", "/requests?page=1&size=10", auth=True)
    
    def test_search_endpoints(self):
        """Test search endpoints"""
        print(f"\n{Colors.BLUE}=== SEARCH ENDPOINTS ==={Colors.RESET}")
        
        search_data = {
            "indices": ["test_index"],
            "query": {"match_all": {}},
            "size": 10
        }
        
        self.test_endpoint("POST", "/search/", data=search_data, auth=True, 
                          expected_status=[200, 400, 403])
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"{Colors.BLUE}TEST SUMMARY{Colors.RESET}")
        print(f"{Colors.BLUE}{'='*80}{Colors.RESET}")
        
        total = len(self.results['passed']) + len(self.results['failed']) + len(self.results['skipped'])
        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        skipped = len(self.results['skipped'])
        
        print(f"\n{Colors.GREEN}Passed:  {passed}/{total}{Colors.RESET}")
        print(f"{Colors.RED}Failed:  {failed}/{total}{Colors.RESET}")
        print(f"{Colors.YELLOW}Skipped: {skipped}/{total}{Colors.RESET}")
        
        if self.results['failed']:
            print(f"\n{Colors.RED}Failed Tests:{Colors.RESET}")
            for test in self.results['failed']:
                print(f"  - {test}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n{Colors.BLUE}Success Rate: {success_rate:.1f}%{Colors.RESET}")
        print(f"{Colors.BLUE}{'='*80}{Colors.RESET}\n")
        
        return failed == 0
    
    def run_all_tests(self):
        """Run all endpoint tests"""
        print(f"{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"{Colors.BLUE}Response Network API - Comprehensive Endpoint Testing{Colors.RESET}")
        print(f"{Colors.BLUE}Base URL: {self.base_url}{Colors.RESET}")
        print(f"{Colors.BLUE}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.BLUE}{'='*80}{Colors.RESET}")
        
        if not self.login():
            print(f"\n{Colors.RED}Login failed! Cannot proceed with authenticated tests.{Colors.RESET}")
            print(f"{Colors.YELLOW}Make sure the server is running and credentials are correct.{Colors.RESET}")
            return False
        
        self.test_auth_endpoints()
        self.test_system_endpoints()
        self.test_monitoring_endpoints()
        self.test_stats_endpoints()
        self.test_user_endpoints()
        self.test_request_endpoints()
        self.test_search_endpoints()
        
        return self.print_summary()

def main():
    """Main entry point"""
    base_url = BASE_URL
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    tester = APITester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
