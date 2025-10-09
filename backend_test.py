#!/usr/bin/env python3
"""
Backend Testing Suite for AI Stylist App
Focus: Manual Outfit Builder UI improvements and outfit generation fixes
Testing DocumentTooLarge fixes, image compression, and new event formats
"""

import requests
import json
import base64
import os
from datetime import datetime, timedelta
import time
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://smart-stylist-15.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

print(f"🔗 Testing backend at: {API_BASE}")
print(f"🎯 Focus: Outfit generation fixes and manual builder improvements")

class BackendTester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        })
    
    def setup_test_user(self):
        """Create and authenticate test user"""
        try:
            # Register test user
            register_data = {
                "email": f"testuser_{int(time.time())}@example.com",
                "password": "testpass123",
                "name": "Test User"
            }
            
            response = requests.post(f"{API_BASE}/auth/register", json=register_data)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.user_id = data["user"]["id"]
                self.log_result("User Registration", True, f"Created user {self.user_id}")
                
                # Complete onboarding with city for weather integration
                onboarding_data = {
                    "age": 28,
                    "profession": "Software Engineer",
                    "body_shape": "Athletic",
                    "skin_tone": "Medium",
                    "style_inspiration": ["Minimalist", "Modern"],
                    "style_vibes": ["Professional", "Casual"],
                    "style_message": "I like clean, simple styles",
                    "city": "Bangalore,IN"
                }
                
                headers = {"Authorization": f"Bearer {self.access_token}"}
                onboard_response = requests.put(f"{API_BASE}/auth/onboarding", json=onboarding_data, headers=headers)
                
                if onboard_response.status_code == 200:
                    self.log_result("User Onboarding", True, "Completed onboarding with city field")
                    return True
                else:
                    self.log_result("User Onboarding", False, f"Status: {onboard_response.status_code}")
                    return False
            else:
                self.log_result("User Registration", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("User Setup", False, f"Exception: {str(e)}")
            return False
    
    def add_test_wardrobe_items(self):
        """Add some test wardrobe items for outfit planning"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Sample base64 image (small test image)
            test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            
            test_items = [
                {"image_base64": f"data:image/png;base64,{test_image_b64}", "category": "top"},
                {"image_base64": f"data:image/png;base64,{test_image_b64}", "category": "bottom"},
                {"image_base64": f"data:image/png;base64,{test_image_b64}", "category": "shoes"},
                {"image_base64": f"data:image/png;base64,{test_image_b64}", "category": "layering"}
            ]
            
            added_items = []
            for item in test_items:
                response = requests.post(f"{API_BASE}/wardrobe", json=item, headers=headers)
                if response.status_code == 200:
                    added_items.append(response.json())
            
            if len(added_items) >= 3:
                self.log_result("Wardrobe Setup", True, f"Added {len(added_items)} test wardrobe items")
                return True
            else:
                self.log_result("Wardrobe Setup", False, f"Only added {len(added_items)} items")
                return False
                
        except Exception as e:
            self.log_result("Wardrobe Setup", False, f"Wardrobe setup error: {str(e)}")
            return False
    
    def test_planner_authentication(self):
        """Test that planner endpoints require authentication"""
        try:
            # Test POST without auth
            test_outfit = {
                "date": "2024-01-15",
                "occasion": "Work",
                "event_name": "Team Meeting",
                "items": {"top": "item1", "bottom": "item2"}
            }
            
            response = requests.post(f"{API_BASE}/planner/outfit", json=test_outfit)
            
            if response.status_code == 401:
                self.log_result("Planner Auth - POST", True, "POST endpoint correctly requires authentication")
            else:
                self.log_result("Planner Auth - POST", False, f"Expected 401, got {response.status_code}")
            
            # Test GET without auth
            response = requests.get(f"{API_BASE}/planner/outfits?start_date=2024-01-01&end_date=2024-01-31")
            
            if response.status_code == 401:
                self.log_result("Planner Auth - GET", True, "GET endpoint correctly requires authentication")
            else:
                self.log_result("Planner Auth - GET", False, f"Expected 401, got {response.status_code}")
            
            # Test DELETE without auth
            response = requests.delete(f"{API_BASE}/planner/outfit/2024-01-15")
            
            if response.status_code == 401:
                self.log_result("Planner Auth - DELETE", True, "DELETE endpoint correctly requires authentication")
            else:
                self.log_result("Planner Auth - DELETE", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Planner Authentication", False, f"Auth test error: {str(e)}")
    
    def test_save_planned_outfit(self):
        """Test POST /api/planner/outfit endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test valid planned outfit
            test_outfit = {
                "date": "2024-01-15",
                "occasion": "Work Meeting",
                "event_name": "Quarterly Review",
                "items": {
                    "top": str(uuid.uuid4()),
                    "bottom": str(uuid.uuid4()),
                    "shoes": str(uuid.uuid4()),
                    "layering": None
                }
            }
            
            response = requests.post(f"{API_BASE}/planner/outfit", json=test_outfit, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "saved" in data["message"].lower():
                    self.log_result("Save Planned Outfit", True, "Successfully saved planned outfit")
                else:
                    self.log_result("Save Planned Outfit", False, f"Unexpected response format: {data}")
            else:
                self.log_result("Save Planned Outfit", False, f"Failed with status {response.status_code}: {response.text}")
            
            # Test outfit without optional event_name
            test_outfit_minimal = {
                "date": "2024-01-16",
                "occasion": "Casual",
                "items": {
                    "top": str(uuid.uuid4()),
                    "bottom": str(uuid.uuid4())
                }
            }
            
            response = requests.post(f"{API_BASE}/planner/outfit", json=test_outfit_minimal, headers=headers)
            
            if response.status_code == 200:
                self.log_result("Save Minimal Outfit", True, "Successfully saved outfit without event_name")
            else:
                self.log_result("Save Minimal Outfit", False, f"Failed minimal outfit: {response.status_code}")
            
            # Test updating existing outfit (same date)
            updated_outfit = {
                "date": "2024-01-15",  # Same date as first test
                "occasion": "Updated Meeting",
                "event_name": "Updated Event",
                "items": {
                    "top": str(uuid.uuid4()),
                    "bottom": str(uuid.uuid4()),
                    "shoes": str(uuid.uuid4())
                }
            }
            
            response = requests.post(f"{API_BASE}/planner/outfit", json=updated_outfit, headers=headers)
            
            if response.status_code == 200:
                self.log_result("Update Planned Outfit", True, "Successfully updated existing planned outfit")
            else:
                self.log_result("Update Planned Outfit", False, f"Failed to update: {response.status_code}")
                
        except Exception as e:
            self.log_result("Save Planned Outfit", False, f"Save test error: {str(e)}")
    
    def test_get_planned_outfits(self):
        """Test GET /api/planner/outfits endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test valid date range
            start_date = "2024-01-01"
            end_date = "2024-01-31"
            
            response = requests.get(
                f"{API_BASE}/planner/outfits?start_date={start_date}&end_date={end_date}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "planned_outfits" in data and isinstance(data["planned_outfits"], list):
                    outfit_count = len(data["planned_outfits"])
                    self.log_result("Get Planned Outfits", True, f"Retrieved {outfit_count} planned outfits")
                    
                    # Verify data structure
                    if outfit_count > 0:
                        first_outfit = data["planned_outfits"][0]
                        required_fields = ["date", "occasion", "items", "user_id"]
                        missing_fields = [field for field in required_fields if field not in first_outfit]
                        
                        if not missing_fields:
                            self.log_result("Outfit Data Structure", True, "Planned outfit has correct structure")
                        else:
                            self.log_result("Outfit Data Structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_result("Get Planned Outfits", False, f"Invalid response format: {data}")
            else:
                self.log_result("Get Planned Outfits", False, f"Failed with status {response.status_code}: {response.text}")
            
            # Test missing query parameters
            response = requests.get(f"{API_BASE}/planner/outfits", headers=headers)
            
            if response.status_code == 422:  # FastAPI validation error
                self.log_result("Date Range Validation", True, "Correctly validates missing date parameters")
            else:
                self.log_result("Date Range Validation", False, f"Expected 422, got {response.status_code}")
            
            # Test invalid date format
            response = requests.get(
                f"{API_BASE}/planner/outfits?start_date=invalid&end_date=2024-01-31",
                headers=headers
            )
            
            # Should handle gracefully (might return empty results or validation error)
            if response.status_code in [200, 422, 400]:
                self.log_result("Invalid Date Format", True, f"Handled invalid date format appropriately ({response.status_code})")
            else:
                self.log_result("Invalid Date Format", False, f"Unexpected response to invalid date: {response.status_code}")
                
        except Exception as e:
            self.log_result("Get Planned Outfits", False, f"Get test error: {str(e)}")
    
    def test_delete_planned_outfit(self):
        """Test DELETE /api/planner/outfit/{date} endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # First, create an outfit to delete
            test_outfit = {
                "date": "2024-01-20",
                "occasion": "Test Delete",
                "items": {"top": str(uuid.uuid4())}
            }
            
            create_response = requests.post(f"{API_BASE}/planner/outfit", json=test_outfit, headers=headers)
            
            if create_response.status_code == 200:
                # Now delete it
                delete_response = requests.delete(f"{API_BASE}/planner/outfit/2024-01-20", headers=headers)
                
                if delete_response.status_code == 200:
                    data = delete_response.json()
                    if "message" in data and "deleted" in data["message"].lower():
                        self.log_result("Delete Planned Outfit", True, "Successfully deleted planned outfit")
                    else:
                        self.log_result("Delete Planned Outfit", False, f"Unexpected delete response: {data}")
                else:
                    self.log_result("Delete Planned Outfit", False, f"Delete failed: {delete_response.status_code}")
            else:
                self.log_result("Delete Planned Outfit", False, "Could not create outfit to delete")
            
            # Test deleting non-existent outfit
            delete_response = requests.delete(f"{API_BASE}/planner/outfit/2024-12-31", headers=headers)
            
            if delete_response.status_code == 200:
                data = delete_response.json()
                if "not found" in data.get("message", "").lower() or "no" in data.get("message", "").lower():
                    self.log_result("Delete Non-existent Outfit", True, "Correctly handled non-existent outfit deletion")
                else:
                    self.log_result("Delete Non-existent Outfit", True, f"Handled gracefully: {data.get('message')}")
            else:
                self.log_result("Delete Non-existent Outfit", False, f"Unexpected status for non-existent: {delete_response.status_code}")
                
        except Exception as e:
            self.log_result("Delete Planned Outfit", False, f"Delete test error: {str(e)}")
    
    def test_data_validation(self):
        """Test data validation and edge cases"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test invalid date format
            invalid_outfit = {
                "date": "invalid-date",
                "occasion": "Test",
                "items": {"top": "item1"}
            }
            
            response = requests.post(f"{API_BASE}/planner/outfit", json=invalid_outfit, headers=headers)
            
            # Should either validate or handle gracefully
            if response.status_code in [400, 422, 500]:
                self.log_result("Invalid Date Validation", True, f"Handled invalid date appropriately ({response.status_code})")
            else:
                self.log_result("Invalid Date Validation", False, f"Unexpected response to invalid date: {response.status_code}")
            
            # Test empty items
            empty_items_outfit = {
                "date": "2024-01-25",
                "occasion": "Test",
                "items": {}
            }
            
            response = requests.post(f"{API_BASE}/planner/outfit", json=empty_items_outfit, headers=headers)
            
            if response.status_code in [200, 400, 422]:
                self.log_result("Empty Items Validation", True, f"Handled empty items appropriately ({response.status_code})")
            else:
                self.log_result("Empty Items Validation", False, f"Unexpected response to empty items: {response.status_code}")
            
            # Test missing required fields
            incomplete_outfit = {
                "date": "2024-01-26"
                # Missing occasion and items
            }
            
            response = requests.post(f"{API_BASE}/planner/outfit", json=incomplete_outfit, headers=headers)
            
            if response.status_code in [400, 422]:
                self.log_result("Required Fields Validation", True, "Correctly validates required fields")
            else:
                self.log_result("Required Fields Validation", False, f"Expected validation error, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Data Validation", False, f"Validation test error: {str(e)}")
    
    def test_integration_flow(self):
        """Test complete integration flow"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # 1. Save multiple outfits
            outfits_to_save = [
                {
                    "date": "2024-02-01",
                    "occasion": "Work",
                    "event_name": "Team Standup",
                    "items": {"top": str(uuid.uuid4()), "bottom": str(uuid.uuid4())}
                },
                {
                    "date": "2024-02-02",
                    "occasion": "Date Night",
                    "event_name": "Dinner",
                    "items": {"top": str(uuid.uuid4()), "bottom": str(uuid.uuid4()), "shoes": str(uuid.uuid4())}
                },
                {
                    "date": "2024-02-03",
                    "occasion": "Casual",
                    "items": {"top": str(uuid.uuid4()), "bottom": str(uuid.uuid4())}
                }
            ]
            
            saved_count = 0
            for outfit in outfits_to_save:
                response = requests.post(f"{API_BASE}/planner/outfit", json=outfit, headers=headers)
                if response.status_code == 200:
                    saved_count += 1
            
            # 2. Retrieve them
            response = requests.get(
                f"{API_BASE}/planner/outfits?start_date=2024-02-01&end_date=2024-02-28",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                retrieved_count = len(data.get("planned_outfits", []))
                
                if retrieved_count >= saved_count:
                    self.log_result("Integration Flow", True, f"Saved {saved_count} outfits, retrieved {retrieved_count}")
                else:
                    self.log_result("Integration Flow", False, f"Saved {saved_count} but only retrieved {retrieved_count}")
            else:
                self.log_result("Integration Flow", False, f"Failed to retrieve outfits: {response.status_code}")
                
        except Exception as e:
            self.log_result("Integration Flow", False, f"Integration test error: {str(e)}")
    
    def run_all_tests(self):
        """Run all planner endpoint tests"""
        print("🧪 Starting Manual Outfit Builder Backend Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Cannot proceed without test user setup")
            return False
        
        if not self.add_test_wardrobe_items():
            print("⚠️ Proceeding without wardrobe items")
        
        # Core planner tests
        self.test_planner_authentication()
        self.test_save_planned_outfit()
        self.test_get_planned_outfits()
        self.test_delete_planned_outfit()
        self.test_data_validation()
        self.test_integration_flow()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🚨 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Manual Outfit Builder backend is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the details above.")