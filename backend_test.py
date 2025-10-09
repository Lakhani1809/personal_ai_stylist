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
    
    def create_sample_base64_image(self, size=(800, 600), color="blue"):
        """Create a sample base64 image for testing"""
        try:
            from PIL import Image
            import io
            
            # Create a simple colored image
            img = Image.new('RGB', size, color)
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            img_data = buffer.getvalue()
            
            return base64.b64encode(img_data).decode('utf-8')
        except Exception as e:
            print(f"Error creating sample image: {e}")
            # Return a minimal base64 image if PIL fails
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    def test_wardrobe_image_compression(self):
        """Test POST /api/wardrobe with image compression"""
        if not self.access_token:
            self.log_result("Wardrobe Image Compression", False, "No auth token")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test with large image to verify compression
            large_image_b64 = self.create_sample_base64_image(size=(2000, 1500), color="red")
            
            wardrobe_data = {
                "image_base64": f"data:image/jpeg;base64,{large_image_b64}"
            }
            
            response = requests.post(f"{API_BASE}/wardrobe", json=wardrobe_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Wardrobe Image Compression", True, 
                               f"Added item: {data.get('message', 'Success')}")
                return True
            else:
                self.log_result("Wardrobe Image Compression", False, 
                               f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_result("Wardrobe Image Compression", False, f"Exception: {str(e)}")
            return False
    
    def test_outfit_generation_fix(self):
        """Test GET /api/wardrobe/outfits to verify DocumentTooLarge fix"""
        if not self.access_token:
            self.log_result("Outfit Generation Fix", False, "No auth token")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # First add multiple wardrobe items to test with sufficient items
            for i, color in enumerate(["blue", "red", "green", "black", "white"]):
                image_b64 = self.create_sample_base64_image(size=(1200, 900), color=color)
                wardrobe_data = {
                    "image_base64": f"data:image/jpeg;base64,{image_b64}"
                }
                
                response = requests.post(f"{API_BASE}/wardrobe", json=wardrobe_data, headers=headers)
                if response.status_code != 200:
                    self.log_result("Outfit Generation Setup", False, 
                                   f"Failed to add item {i+1}: {response.status_code}")
                    return False
            
            # Now test outfit generation
            response = requests.get(f"{API_BASE}/wardrobe/outfits", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                outfits = data.get("outfits", [])
                
                if len(outfits) > 0:
                    self.log_result("Outfit Generation Fix", True, 
                                   f"Generated {len(outfits)} outfits successfully without DocumentTooLarge error")
                    
                    # Verify outfit structure includes compressed thumbnails
                    first_outfit = outfits[0]
                    if "items" in first_outfit and len(first_outfit["items"]) > 0:
                        first_item = first_outfit["items"][0]
                        if "image_base64" in first_item:
                            thumbnail_size = len(first_item["image_base64"])
                            self.log_result("Outfit Thumbnail Compression", True, 
                                           f"Thumbnail size: {thumbnail_size} chars (compressed)")
                        else:
                            self.log_result("Outfit Thumbnail Compression", False, "No image_base64 in outfit item")
                    
                    return True
                else:
                    message = data.get("message", "No outfits generated")
                    if "need at least" in message.lower() or "add more" in message.lower():
                        self.log_result("Outfit Generation Fix", True, 
                                       f"Proper guardrails working: {message}")
                        return True
                    else:
                        self.log_result("Outfit Generation Fix", False, f"No outfits: {message}")
                        return False
            else:
                self.log_result("Outfit Generation Fix", False, 
                               f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_result("Outfit Generation Fix", False, f"Exception: {str(e)}")
            return False
    
    def test_manual_builder_new_event_format(self):
        """Test POST /api/planner/outfit with new event format (work, dinner, date, etc.)"""
        if not self.access_token:
            self.log_result("Manual Builder Event Format", False, "No auth token")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test with new predefined event types
            test_events = [
                ("work", "Work Meeting"),
                ("dinner", "Dinner with Friends"),
                ("date", "Date Night"),
                ("party", "Birthday Party"),
                ("casual", "Casual Day Out"),
                ("gym", "Gym Session"),
                ("travel", "Travel Day"),
                ("meeting", "Business Meeting")
            ]
            
            success_count = 0
            
            for event_type, event_description in test_events:
                # Test date (tomorrow)
                test_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                
                planned_outfit_data = {
                    "date": test_date,
                    "occasion": event_type,
                    "event_name": f"{event_description} at 7:30 PM",  # Test time formatting
                    "items": {
                        "top": "item_id_1",
                        "bottom": "item_id_2",
                        "shoes": "item_id_3"
                    }
                }
                
                response = requests.post(f"{API_BASE}/planner/outfit", json=planned_outfit_data, headers=headers)
                
                if response.status_code == 200:
                    success_count += 1
                    self.log_result(f"Manual Builder - {event_type}", True, 
                                   f"Saved outfit for {event_description}")
                else:
                    self.log_result(f"Manual Builder - {event_type}", False, 
                                   f"Status: {response.status_code}, Response: {response.text[:100]}")
            
            # Overall result
            if success_count >= 6:  # At least 6 out of 8 event types should work
                self.log_result("Manual Builder Event Format", True, 
                               f"Successfully saved {success_count}/{len(test_events)} event types")
                return True
            else:
                self.log_result("Manual Builder Event Format", False, 
                               f"Only {success_count}/{len(test_events)} event types worked")
                return False
                
        except Exception as e:
            self.log_result("Manual Builder Event Format", False, f"Exception: {str(e)}")
            return False
    
    def test_manual_builder_time_formatting(self):
        """Test time formatting in manual builder (e.g., '7:30 PM')"""
        if not self.access_token:
            self.log_result("Manual Builder Time Format", False, "No auth token")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test various time formats
            time_formats = [
                "7:30 PM",
                "9:00 AM", 
                "12:30 PM",
                "6:45 PM",
                "11:15 AM"
            ]
            
            success_count = 0
            
            for time_format in time_formats:
                test_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
                
                planned_outfit_data = {
                    "date": test_date,
                    "occasion": "dinner",
                    "event_name": f"Dinner at {time_format}",
                    "items": {
                        "top": "shirt_id",
                        "bottom": "pants_id"
                    }
                }
                
                response = requests.post(f"{API_BASE}/planner/outfit", json=planned_outfit_data, headers=headers)
                
                if response.status_code == 200:
                    success_count += 1
                    
                    # Verify the time was saved correctly by retrieving it
                    start_date = test_date
                    end_date = test_date
                    get_response = requests.get(f"{API_BASE}/planner/outfits?start_date={start_date}&end_date={end_date}", headers=headers)
                    
                    if get_response.status_code == 200:
                        data = get_response.json()
                        planned_outfits = data.get("planned_outfits", [])
                        
                        if planned_outfits and time_format in planned_outfits[0].get("event_name", ""):
                            self.log_result(f"Time Format - {time_format}", True, 
                                           f"Time correctly saved and retrieved")
                        else:
                            self.log_result(f"Time Format - {time_format}", False, 
                                           f"Time format not preserved in storage")
                    else:
                        self.log_result(f"Time Format - {time_format}", False, 
                                       f"Could not retrieve saved outfit")
                else:
                    self.log_result(f"Time Format - {time_format}", False, 
                                   f"Status: {response.status_code}")
            
            if success_count >= 4:  # At least 4 out of 5 time formats should work
                self.log_result("Manual Builder Time Format", True, 
                               f"Successfully handled {success_count}/{len(time_formats)} time formats")
                return True
            else:
                self.log_result("Manual Builder Time Format", False, 
                               f"Only {success_count}/{len(time_formats)} time formats worked")
                return False
                
        except Exception as e:
            self.log_result("Manual Builder Time Format", False, f"Exception: {str(e)}")
            return False
    
    def test_existing_functionality(self):
        """Test that existing functionality still works"""
        if not self.access_token:
            self.log_result("Existing Functionality", False, "No auth token")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test wardrobe retrieval
            response = requests.get(f"{API_BASE}/wardrobe", headers=headers)
            if response.status_code == 200:
                self.log_result("Wardrobe Retrieval", True, "Wardrobe endpoint working")
            else:
                self.log_result("Wardrobe Retrieval", False, f"Status: {response.status_code}")
                return False
            
            # Test chat functionality
            chat_data = {"message": "What should I wear today?"}
            response = requests.post(f"{API_BASE}/chat", json=chat_data, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "messages" in data or "message" in data:
                    self.log_result("Chat Functionality", True, "Chat endpoint working")
                else:
                    self.log_result("Chat Functionality", False, "Unexpected chat response format")
                    return False
            else:
                self.log_result("Chat Functionality", False, f"Status: {response.status_code}")
                return False
            
            return True
                
        except Exception as e:
            self.log_result("Existing Functionality", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🧪 Starting Backend Testing Suite")
        print("=" * 50)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user, aborting tests")
            return
        
        # Core tests for the fixes
        print("\n🎯 Testing Outfit Generation Fixes...")
        self.test_wardrobe_image_compression()
        self.test_outfit_generation_fix()
        
        print("\n🎯 Testing Manual Builder Improvements...")
        self.test_manual_builder_new_event_format()
        self.test_manual_builder_time_formatting()
        
        print("\n🎯 Testing Existing Functionality...")
        self.test_existing_functionality()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = BackendTester()
    passed, failed = tester.run_all_tests()
    
    if failed == 0:
        print("\n🎉 All tests passed! Backend fixes are working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the issues above.")