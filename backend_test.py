#!/usr/bin/env python3
"""
Canine.Fit Backend API Testing Suite
Tests the complete backend API flow as specified in the review request.
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, Any, Optional
import sys
from datetime import datetime

class CanineFitAPITester:
    def __init__(self):
        # Use the configured backend URL from environment
        self.base_url = "https://dog-fitness-hub.preview.emergentagent.com"
        self.api_base = f"{self.base_url}/api"
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.dog_id: Optional[str] = None
        self.test_results = []
        
    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
    
    async def teardown(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, message: str, data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None, auth: bool = False) -> tuple[bool, Dict]:
        """Make HTTP request to API"""
        url = f"{self.api_base}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        try:
            async with self.session.request(method, url, json=data, headers=headers) as response:
                response_data = await response.json()
                return response.status < 400, response_data
        except Exception as e:
            return False, {"error": str(e), "type": "connection_error"}
    
    async def test_auth_signup(self):
        """Test 1: Auth Flow - Signup"""
        test_data = {
            "email": "dogowner@test.com",
            "password": "test123",
            "name": "Dog Owner"
        }
        
        success, response = await self.make_request("POST", "/auth/signup", test_data)
        
        if success and "access_token" in response:
            self.access_token = response["access_token"]
            user_data = response.get("user", {})
            self.log_result("Auth Signup", True, 
                          f"User created successfully. ID: {user_data.get('id', 'N/A')}", 
                          {"user_id": user_data.get("id"), "email": user_data.get("email")})
        else:
            # Check if user already exists (which is fine for testing)
            if "already registered" in str(response).lower():
                # Try login instead
                await self.test_auth_login_fallback()
            else:
                self.log_result("Auth Signup", False, f"Signup failed: {response}")
    
    async def test_auth_login_fallback(self):
        """Fallback login if user already exists"""
        test_data = {
            "email": "dogowner@test.com",
            "password": "test123"
        }
        
        success, response = await self.make_request("POST", "/auth/login", test_data)
        
        if success and "access_token" in response:
            self.access_token = response["access_token"]
            user_data = response.get("user", {})
            self.log_result("Auth Login (Fallback)", True, 
                          f"User logged in successfully. ID: {user_data.get('id', 'N/A')}")
        else:
            self.log_result("Auth Login (Fallback)", False, f"Login failed: {response}")
    
    async def test_dog_creation(self):
        """Test 2: Dog Profile Creation"""
        if not self.access_token:
            self.log_result("Dog Creation", False, "No access token available")
            return
        
        test_data = {
            "name": "Buddy",
            "breed": "Golden Retriever",
            "weight_lbs": 65,
            "date_of_birth": "2022-03-15",
            "activity_level": "high"
        }
        
        success, response = await self.make_request("POST", "/dogs", test_data, auth=True)
        
        if success and "id" in response:
            self.dog_id = response["id"]
            self.log_result("Dog Creation", True, 
                          f"Dog profile created successfully. ID: {self.dog_id}", 
                          {"dog_id": self.dog_id, "name": response.get("name")})
        else:
            self.log_result("Dog Creation", False, f"Dog creation failed: {response}")
    
    async def test_daily_log_creation(self):
        """Test 3: Daily Log Creation"""
        if not self.access_token or not self.dog_id:
            self.log_result("Daily Log Creation", False, "No access token or dog_id available")
            return
        
        test_data = {
            "dog_id": self.dog_id,
            "mood": "great",
            "exercise_level": "active",
            "nutrition_quality": "excellent"
        }
        
        success, response = await self.make_request("POST", "/daily-logs", test_data, auth=True)
        
        if success:
            log_data = {
                "log_id": response.get("id"),
                "mood": response.get("mood"),
                "points": response.get("points_earned", 0)
            }
            self.log_result("Daily Log Creation", True, 
                          f"Daily log created successfully. Points earned: {response.get('points_earned', 0)}", 
                          log_data)
        else:
            # Check if it's a "already logged for today" error (which is acceptable)
            if "already logged" in str(response).lower():
                self.log_result("Daily Log Creation", True, 
                              "Daily log already exists for today (acceptable)", 
                              {"status": "already_exists"})
            else:
                self.log_result("Daily Log Creation", False, f"Daily log creation failed: {response}")
    
    async def test_healthspan_check(self):
        """Test 4: Healthspan Check"""
        if not self.access_token or not self.dog_id:
            self.log_result("Healthspan Check", False, "No access token or dog_id available")
            return
        
        success, response = await self.make_request("GET", f"/healthspan/{self.dog_id}", auth=True)
        
        if success:
            required_fields = ["score", "streak", "total_points"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                health_data = {
                    "score": response.get("score"),
                    "streak": response.get("streak"),
                    "total_points": response.get("total_points"),
                    "breed_rank": response.get("breed_rank")
                }
                self.log_result("Healthspan Check", True, 
                              f"Healthspan data retrieved. Score: {response['score']}, Streak: {response['streak']}", 
                              health_data)
            else:
                self.log_result("Healthspan Check", False, f"Missing required fields: {missing_fields}")
        else:
            self.log_result("Healthspan Check", False, f"Healthspan check failed: {response}")
    
    async def test_lilo_ai_report(self):
        """Test 5: Lilo AI Report Generation (Real AI)"""
        if not self.access_token or not self.dog_id:
            self.log_result("Lilo AI Report", False, "No access token or dog_id available")
            return
        
        success, response = await self.make_request("POST", f"/lilo-ai/{self.dog_id}", auth=True)
        
        if success:
            required_fields = ["mood", "summary", "insights", "recommendation"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                ai_data = {
                    "mood": response.get("mood"),
                    "summary_length": len(response.get("summary", "")),
                    "insights_count": len(response.get("insights", [])),
                    "recommendation_length": len(response.get("recommendation", "")),
                    "healthspan_delta": response.get("healthspan_delta")
                }
                self.log_result("Lilo AI Report", True, 
                              f"AI report generated successfully. Mood: {response['mood']}, Insights: {len(response.get('insights', []))}", 
                              ai_data)
            else:
                self.log_result("Lilo AI Report", False, f"Missing required fields: {missing_fields}")
        else:
            self.log_result("Lilo AI Report", False, f"Lilo AI report generation failed: {response}")
    
    async def test_subscription_plans(self):
        """Test 6: Subscription Plans"""
        success, response = await self.make_request("GET", "/subscription/plans")
        
        if success and isinstance(response, dict):
            # Check for both monthly and annual plans
            has_monthly = "monthly" in response
            has_annual = "annual" in response
            
            if has_monthly and has_annual:
                monthly_price = response.get("monthly", {}).get("price", 0)
                annual_price = response.get("annual", {}).get("price", 0)
                
                plans_data = {
                    "monthly_price": monthly_price,
                    "annual_price": annual_price,
                    "plans_count": len(response)
                }
                
                # Verify expected prices
                if monthly_price == 9.0 and annual_price == 99.0:
                    self.log_result("Subscription Plans", True, 
                                  f"Subscription plans retrieved correctly. Monthly: ${monthly_price}, Annual: ${annual_price}", 
                                  plans_data)
                else:
                    self.log_result("Subscription Plans", False, 
                                  f"Incorrect pricing. Expected Monthly: $9, Annual: $99. Got Monthly: ${monthly_price}, Annual: ${annual_price}")
            else:
                self.log_result("Subscription Plans", False, "Missing monthly or annual plan")
        else:
            self.log_result("Subscription Plans", False, f"Failed to retrieve subscription plans: {response}")
    
    async def test_checkout_session(self):
        """Test 7: Checkout Session Creation"""
        if not self.access_token:
            self.log_result("Checkout Session", False, "No access token available")
            return
        
        test_data = {
            "plan_id": "monthly",
            "origin_url": "https://dog-fitness-hub.preview.emergentagent.com"
        }
        
        success, response = await self.make_request("POST", "/subscription/checkout", test_data, auth=True)
        
        if success and "checkout_url" in response:
            checkout_data = {
                "checkout_url": response.get("checkout_url"),
                "session_id": response.get("session_id"),
                "url_valid": response.get("checkout_url", "").startswith("https://")
            }
            
            # Verify it's a valid Stripe checkout URL
            if "stripe.com" in response["checkout_url"] or "checkout" in response["checkout_url"]:
                self.log_result("Checkout Session", True, 
                              "Checkout session created successfully with valid Stripe URL", 
                              checkout_data)
            else:
                self.log_result("Checkout Session", False, 
                              f"Checkout URL doesn't appear to be valid Stripe URL: {response['checkout_url']}")
        else:
            self.log_result("Checkout Session", False, f"Checkout session creation failed: {response}")
    
    async def run_all_tests(self):
        """Run all API tests in sequence"""
        print(f"🚀 Starting Canine.Fit Backend API Tests")
        print(f"📍 Base URL: {self.api_base}")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Run tests in sequence
            await self.test_auth_signup()
            await self.test_dog_creation()
            await self.test_daily_log_creation()
            await self.test_healthspan_check()
            await self.test_lilo_ai_report()
            await self.test_subscription_plans()
            await self.test_checkout_session()
            
        finally:
            await self.teardown()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "0.0%")
        
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        # Print failed tests details
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print("🔍 FAILED TESTS DETAILS:")
            for result in failed_tests:
                print(f"❌ {result['test']}")
                print(f"   Error: {result['message']}")
                if result.get("data"):
                    print(f"   Data: {result['data']}")
                print()

async def main():
    """Main test execution function"""
    tester = CanineFitAPITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())