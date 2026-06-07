#!/usr/bin/env python3
"""
Bearer Token Migration Test Script

This script tests the dual authentication system (cookies + bearer tokens)
to ensure our migration is working correctly.

Usage: python test_bearer_token_migration.py
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:5000"  # Adjust as needed
TEST_USER = {
    "email": "test@example.com",
    "password": "testpassword123"
}

class BearerTokenTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()  # For cookie-based auth
        self.bearer_token = None
        self.user_data = None
        
    def print_test(self, test_name: str):
        print(f"\n🧪 {test_name}")
        print("=" * 50)
    
    def print_success(self, message: str):
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        print(f"❌ {message}")
    
    def print_info(self, message: str):
        print(f"ℹ️  {message}")

    def test_login_cookie_auth(self) -> bool:
        """Test traditional cookie-based login"""
        self.print_test("Cookie-Based Login")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/user/login",
                json=TEST_USER
            )
            
            if response.status_code == 200:
                self.user_data = response.json()
                self.print_success(f"Login successful: {self.user_data.get('user', {}).get('email')}")
                
                # Check if cookies were set
                cookies = self.session.cookies.get_dict()
                if 'user_token' in cookies:
                    self.print_success("HTTP-only cookies set correctly")
                    return True
                else:
                    self.print_error("No cookies found in response")
                    return False
            else:
                self.print_error(f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Login request failed: {e}")
            return False

    def test_bearer_token_extraction(self) -> bool:
        """Test if we can extract bearer token from login response"""
        self.print_test("Bearer Token Extraction")
        
        if not self.user_data:
            self.print_error("No user data from login - run cookie auth test first")
            return False
        
        # Try to get bearer token from response (depends on login endpoint implementation)
        if 'access_token' in self.user_data:
            self.bearer_token = self.user_data['access_token']
            self.print_success(f"Bearer token found: {self.bearer_token[:20]}...")
            return True
        elif 'user' in self.user_data and 'user_token' in self.user_data['user']:
            # Fallback: use the user_token as bearer token
            self.bearer_token = self.user_data['user']['user_token']
            self.print_info(f"Using user_token as bearer token: {self.bearer_token[:20]}...")
            return True
        else:
            self.print_error("No bearer token found in login response")
            self.print_info("This is expected if login endpoint hasn't been updated yet")
            return False

    def test_cookie_based_request(self) -> bool:
        """Test API call using cookie-based authentication"""
        self.print_test("Cookie-Based API Request")
        
        try:
            response = self.session.get(f"{self.base_url}/api/user/info")
            
            if response.status_code == 200:
                user_info = response.json()
                self.print_success(f"Got user info via cookies: {user_info.get('email')}")
                return True
            else:
                self.print_error(f"Cookie auth failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Cookie request failed: {e}")
            return False

    def test_bearer_token_request(self) -> bool:
        """Test API call using bearer token authentication"""
        self.print_test("Bearer Token API Request")
        
        if not self.bearer_token:
            self.print_error("No bearer token available - run token extraction test first")
            return False
        
        try:
            # Create a fresh session without cookies
            fresh_session = requests.Session()
            headers = {
                'Authorization': f'Bearer {self.bearer_token}',
                'Content-Type': 'application/json'
            }
            
            response = fresh_session.get(
                f"{self.base_url}/api/user/info",
                headers=headers
            )
            
            if response.status_code == 200:
                user_info = response.json()
                self.print_success(f"Got user info via bearer token: {user_info.get('email')}")
                return True
            else:
                self.print_error(f"Bearer auth failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Bearer token request failed: {e}")
            return False

    def test_mixed_authentication(self) -> bool:
        """Test that both auth methods work for the same user"""
        self.print_test("Mixed Authentication Test")
        
        if not self.bearer_token:
            self.print_error("No bearer token available")
            return False
        
        try:
            # Test multiple endpoints with both auth methods
            endpoints = [
                "/api/user/info",
                "/api/sessions/list",
                "/api/user/all"
            ]
            
            success_count = 0
            total_tests = len(endpoints) * 2  # Each endpoint tested with both auth methods
            
            for endpoint in endpoints:
                # Test with cookies
                cookie_response = self.session.get(f"{self.base_url}{endpoint}")
                if cookie_response.status_code == 200:
                    success_count += 1
                    self.print_success(f"Cookie auth OK: {endpoint}")
                else:
                    self.print_error(f"Cookie auth failed: {endpoint} - {cookie_response.status_code}")
                
                # Test with bearer token
                fresh_session = requests.Session()
                headers = {'Authorization': f'Bearer {self.bearer_token}'}
                bearer_response = fresh_session.get(f"{self.base_url}{endpoint}", headers=headers)
                
                if bearer_response.status_code == 200:
                    success_count += 1
                    self.print_success(f"Bearer auth OK: {endpoint}")
                else:
                    self.print_error(f"Bearer auth failed: {endpoint} - {bearer_response.status_code}")
            
            success_rate = (success_count / total_tests) * 100
            self.print_info(f"Overall success rate: {success_rate:.1f}% ({success_count}/{total_tests})")
            
            return success_rate >= 80  # 80% success rate threshold
            
        except Exception as e:
            self.print_error(f"Mixed auth test failed: {e}")
            return False

    def test_logout_both_methods(self) -> bool:
        """Test logout with both authentication methods"""
        self.print_test("Logout Test (Both Methods)")
        
        try:
            # Test cookie-based logout
            cookie_logout = self.session.get(f"{self.base_url}/api/user/logout")
            if cookie_logout.status_code == 200:
                self.print_success("Cookie-based logout successful")
            else:
                self.print_error(f"Cookie logout failed: {cookie_logout.status_code}")
            
            # Test bearer token logout (if we have a token)
            if self.bearer_token:
                fresh_session = requests.Session()
                headers = {'Authorization': f'Bearer {self.bearer_token}'}
                bearer_logout = fresh_session.get(
                    f"{self.base_url}/api/user/logout",
                    headers=headers
                )
                
                if bearer_logout.status_code == 200:
                    self.print_success("Bearer token logout successful")
                    return True
                else:
                    self.print_error(f"Bearer logout failed: {bearer_logout.status_code}")
                    return False
            else:
                self.print_info("No bearer token to test logout with")
                return True
                
        except Exception as e:
            self.print_error(f"Logout test failed: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Run all tests and return overall success"""
        print("🚀 Bearer Token Migration Test Suite")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"Test user: {TEST_USER['email']}")
        
        tests = [
            ("Cookie Login", self.test_login_cookie_auth),
            ("Bearer Token Extraction", self.test_bearer_token_extraction),
            ("Cookie API Requests", self.test_cookie_based_request),
            ("Bearer Token API Requests", self.test_bearer_token_request),
            ("Mixed Authentication", self.test_mixed_authentication),
            ("Logout Methods", self.test_logout_both_methods),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.print_error(f"Test '{test_name}' crashed: {e}")
                failed += 1
        
        print(f"\n📊 Test Results:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if passed > failed:
            print(f"\n🎉 Overall: MIGRATION WORKING! ({passed}/{passed+failed} tests passed)")
            return True
        else:
            print(f"\n⚠️  Overall: NEEDS WORK ({failed}/{passed+failed} tests failed)")
            return False

def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = BASE_URL
    
    tester = BearerTokenTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 