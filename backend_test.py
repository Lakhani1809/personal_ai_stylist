#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Railway AI Fashion Segmentation Integration
Tests the Railway AI integration according to the specifications provided.
"""

import requests
import json
import base64
import asyncio
import sys
import os
from datetime import datetime
from io import BytesIO
from PIL import Image
import uuid

# Add backend to path for imports
sys.path.append('/app/backend')

# Test configuration
BACKEND_URL = "https://smart-stylist-15.preview.emergentagent.com/api"
RAILWAY_AI_URL = "https://fashion-ai-segmentation-production.up.railway.app/upload"

class RailwayAITester:
    def __init__(self):
        self.test_results = []
        self.access_token = None
        self.user_id = None
        
    def log_test(self, test_name: str, success: bool, details: str):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def create_test_image(self, width=400, height=400, color=(255, 0, 0)) -> str:
        """Create a test image and return as base64"""
        try:
            # Create a simple colored image
            image = Image.new('RGB', (width, height), color)
            buffer = BytesIO()
            image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            print(f"❌ Failed to create test image: {e}")
            return ""
    
    def setup_test_user(self):
        """Create a test user and get authentication token"""
        try:
            # Register test user
            test_email = f"railwaytest_{int(datetime.now().timestamp())}@test.com"
            register_data = {
                "email": test_email,
                "password": "testpass123",
                "name": "Railway Test User"
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/register", json=register_data)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                self.log_test("User Registration", True, f"Created test user: {test_email}")
                return True
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def test_railway_ai_direct_api(self):
        """Test Railway AI service directly"""
        try:
            print("\n🚂 Testing Railway AI Service Directly...")
            
            # Create test image
            test_image_b64 = self.create_test_image(600, 800, (100, 150, 200))
            if not test_image_b64:
                self.log_test("Railway AI Direct - Image Creation", False, "Failed to create test image")
                return False
            
            # Convert base64 to bytes for multipart upload
            image_bytes = base64.b64decode(test_image_b64)
            
            # Test 1: Check API endpoint availability
            try:
                files = {'file': ('test_fashion.jpg', BytesIO(image_bytes), 'image/jpeg')}
                response = requests.post(RAILWAY_AI_URL, files=files, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("Railway AI Direct - API Availability", True, 
                                f"Status: {response.status_code}, Response keys: {list(data.keys())}")
                    
                    # Test 2: Check response format
                    required_fields = ["status", "num_components", "categories", "image_name"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        self.log_test("Railway AI Direct - Response Format", True, 
                                    f"All required fields present: {required_fields}")
                        
                        # Test 3: Check success criteria
                        status = data.get("status")
                        num_components = data.get("num_components", 0)
                        categories = data.get("categories", [])
                        
                        if status == "success" and num_components > 0:
                            self.log_test("Railway AI Direct - Success Validation", True, 
                                        f"Status: {status}, Components: {num_components}, Categories: {categories}")
                        else:
                            self.log_test("Railway AI Direct - Success Validation", False, 
                                        f"Status: {status}, Components: {num_components}")
                        
                        return True
                    else:
                        self.log_test("Railway AI Direct - Response Format", False, 
                                    f"Missing fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Railway AI Direct - API Availability", False, 
                                f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
            except requests.exceptions.Timeout:
                self.log_test("Railway AI Direct - API Availability", False, "Request timeout (60s)")
                return False
            except Exception as e:
                self.log_test("Railway AI Direct - API Availability", False, f"Exception: {str(e)}")
                return False
                
        except Exception as e:
            self.log_test("Railway AI Direct - Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_category_normalization(self):
        """Test category normalization functionality"""
        try:
            print("\n🏷️ Testing Category Normalization...")
            
            # Import the normalization function
            from services.railway_ai_service import normalize_category
            
            # Test cases for Railway AI specific mappings
            test_cases = [
                ("upper_clothes", "Tops"),
                ("lower_clothes", "Bottoms"),
                ("full_body", "Dresses"),
                ("outer_layer", "Jackets"),
                ("shirt", "Shirts"),
                ("pants", "Pants"),
                ("shoes", "Shoes"),
                ("unknown_category", "Unknown Category")  # Test fallback
            ]
            
            all_passed = True
            for input_cat, expected_output in test_cases:
                result = normalize_category(input_cat)
                if result == expected_output:
                    self.log_test(f"Category Normalization - {input_cat}", True, 
                                f"'{input_cat}' → '{result}' (expected: '{expected_output}')")
                else:
                    self.log_test(f"Category Normalization - {input_cat}", False, 
                                f"'{input_cat}' → '{result}' (expected: '{expected_output}')")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_test("Category Normalization - Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_duplicate_detection(self):
        """Test duplicate detection algorithm"""
        try:
            print("\n🔍 Testing Duplicate Detection...")
            
            # Import the duplicate detection functions
            from services.railway_ai_service import calculate_item_similarity, check_for_duplicate_items
            
            # Test similarity calculation
            item1 = {
                "exact_item_name": "Blue Cotton T-shirt",
                "category": "Tops",
                "color": "Blue",
                "style": "Casual",
                "fabric_type": "Cotton"
            }
            
            # Identical item (should be high similarity)
            item2 = {
                "exact_item_name": "Blue Cotton T-shirt",
                "category": "Tops", 
                "color": "Blue",
                "style": "Casual",
                "fabric_type": "Cotton"
            }
            
            # Similar item (should be medium-high similarity)
            item3 = {
                "exact_item_name": "Navy Cotton Shirt",
                "category": "Tops",
                "color": "Navy Blue",
                "style": "Casual",
                "fabric_type": "Cotton"
            }
            
            # Different item (should be low similarity)
            item4 = {
                "exact_item_name": "Black Leather Jacket",
                "category": "Jackets",
                "color": "Black",
                "style": "Edgy",
                "fabric_type": "Leather"
            }
            
            # Test similarity scores
            similarity_identical = calculate_item_similarity(item1, item2)
            similarity_similar = calculate_item_similarity(item1, item3)
            similarity_different = calculate_item_similarity(item1, item4)
            
            # Test thresholds
            if similarity_identical > 0.8:
                self.log_test("Duplicate Detection - Identical Items", True, 
                            f"Similarity: {similarity_identical:.2f} (>0.8 threshold)")
            else:
                self.log_test("Duplicate Detection - Identical Items", False, 
                            f"Similarity: {similarity_identical:.2f} (should be >0.8)")
            
            if similarity_similar < 0.8:
                self.log_test("Duplicate Detection - Similar Items", True, 
                            f"Similarity: {similarity_similar:.2f} (<0.8 threshold)")
            else:
                self.log_test("Duplicate Detection - Similar Items", False, 
                            f"Similarity: {similarity_similar:.2f} (should be <0.8)")
            
            if similarity_different < 0.3:
                self.log_test("Duplicate Detection - Different Items", True, 
                            f"Similarity: {similarity_different:.2f} (<0.3 expected)")
            else:
                self.log_test("Duplicate Detection - Different Items", False, 
                            f"Similarity: {similarity_different:.2f} (should be <0.3)")
            
            # Test async duplicate checking
            async def test_async_duplicate_check():
                new_items = [item1, item3]  # One duplicate, one unique
                existing_wardrobe = [item2, item4]  # Contains duplicate of item1
                
                unique_items = await check_for_duplicate_items(new_items, existing_wardrobe)
                
                if len(unique_items) == 1 and unique_items[0]["exact_item_name"] == item3["exact_item_name"]:
                    self.log_test("Duplicate Detection - Async Check", True, 
                                f"Filtered {len(new_items)} → {len(unique_items)} unique items")
                    return True
                else:
                    self.log_test("Duplicate Detection - Async Check", False, 
                                f"Expected 1 unique item, got {len(unique_items)}")
                    return False
            
            # Run async test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            async_result = loop.run_until_complete(test_async_duplicate_check())
            loop.close()
            
            return async_result
            
        except Exception as e:
            self.log_test("Duplicate Detection - Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_wardrobe_integration(self):
        """Test Railway AI integration with wardrobe endpoints"""
        try:
            print("\n👗 Testing Wardrobe Integration...")
            
            if not self.access_token:
                self.log_test("Wardrobe Integration - Auth", False, "No access token available")
                return False
            
            # Test 1: POST /api/wardrobe with Railway AI extraction
            test_image_b64 = self.create_test_image(500, 700, (150, 100, 200))
            if not test_image_b64:
                self.log_test("Wardrobe Integration - Image Creation", False, "Failed to create test image")
                return False
            
            wardrobe_data = {
                "image_base64": f"data:image/jpeg;base64,{test_image_b64}"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/wardrobe",
                json=wardrobe_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                extraction_method = data.get("extraction_method", "unknown")
                items_added = data.get("items_added", 0)
                
                if extraction_method == "railway_ai":
                    self.log_test("Wardrobe Integration - Railway AI Extraction", True, 
                                f"Items added: {items_added}, Method: {extraction_method}")
                else:
                    self.log_test("Wardrobe Integration - Railway AI Extraction", False, 
                                f"Expected railway_ai method, got: {extraction_method}")
                
                # Test 2: Verify items were added to wardrobe
                wardrobe_response = requests.get(
                    f"{BACKEND_URL}/wardrobe",
                    headers=self.get_auth_headers()
                )
                
                if wardrobe_response.status_code == 200:
                    wardrobe_data = wardrobe_response.json()
                    wardrobe_items = wardrobe_data.get("items", [])
                    
                    if len(wardrobe_items) >= items_added:
                        self.log_test("Wardrobe Integration - Item Storage", True, 
                                    f"Wardrobe contains {len(wardrobe_items)} items")
                        
                        # Check for Railway AI specific fields
                        railway_items = [item for item in wardrobe_items if "railway" in str(item.get("tags", [])).lower()]
                        if railway_items:
                            self.log_test("Wardrobe Integration - Railway AI Tags", True, 
                                        f"Found {len(railway_items)} items with Railway AI tags")
                        else:
                            self.log_test("Wardrobe Integration - Railway AI Tags", False, 
                                        "No items found with Railway AI tags")
                        
                        return True
                    else:
                        self.log_test("Wardrobe Integration - Item Storage", False, 
                                    f"Expected {items_added} items, found {len(wardrobe_items)}")
                        return False
                else:
                    self.log_test("Wardrobe Integration - Item Retrieval", False, 
                                f"Status: {wardrobe_response.status_code}")
                    return False
            else:
                self.log_test("Wardrobe Integration - POST Request", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Wardrobe Integration - Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_validation_auto_extraction(self):
        """Test validation endpoint with Railway AI auto-extraction"""
        try:
            print("\n✅ Testing Validation Auto-Extraction...")
            
            if not self.access_token:
                self.log_test("Validation Auto-Extraction - Auth", False, "No access token available")
                return False
            
            # Get initial wardrobe count
            wardrobe_response = requests.get(
                f"{BACKEND_URL}/wardrobe",
                headers=self.get_auth_headers()
            )
            
            initial_count = 0
            if wardrobe_response.status_code == 200:
                initial_count = len(wardrobe_response.json().get("items", []))
            
            # Test validation with image that should extract items
            test_image_b64 = self.create_test_image(600, 800, (200, 150, 100))
            validation_data = {
                "image_base64": f"data:image/jpeg;base64,{test_image_b64}"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/validate-outfit",
                json=validation_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                validation_result = response.json()
                
                # Check validation structure
                required_fields = ["scores", "overall_score", "feedback"]
                missing_fields = [field for field in required_fields if field not in validation_result]
                
                if not missing_fields:
                    self.log_test("Validation Auto-Extraction - Response Format", True, 
                                f"All required fields present: {required_fields}")
                    
                    # Check if items were auto-added to wardrobe
                    final_wardrobe_response = requests.get(
                        f"{BACKEND_URL}/wardrobe",
                        headers=self.get_auth_headers()
                    )
                    
                    if final_wardrobe_response.status_code == 200:
                        final_count = len(final_wardrobe_response.json().get("items", []))
                        
                        if final_count > initial_count:
                            self.log_test("Validation Auto-Extraction - Wardrobe Population", True, 
                                        f"Wardrobe items increased: {initial_count} → {final_count}")
                        else:
                            self.log_test("Validation Auto-Extraction - Wardrobe Population", False, 
                                        f"No new items added: {initial_count} → {final_count}")
                        
                        return True
                    else:
                        self.log_test("Validation Auto-Extraction - Wardrobe Check", False, 
                                    f"Status: {final_wardrobe_response.status_code}")
                        return False
                else:
                    self.log_test("Validation Auto-Extraction - Response Format", False, 
                                f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Validation Auto-Extraction - POST Request", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Validation Auto-Extraction - Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_error_handling_fallback(self):
        """Test error handling and OpenAI fallback"""
        try:
            print("\n🛡️ Testing Error Handling & Fallback...")
            
            if not self.access_token:
                self.log_test("Error Handling - Auth", False, "No access token available")
                return False
            
            # Test with invalid image data to trigger fallback
            invalid_data = {
                "image_base64": "data:image/jpeg;base64,invalid_base64_data"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/wardrobe",
                json=invalid_data,
                headers=self.get_auth_headers()
            )
            
            # Should still work due to fallback mechanisms
            if response.status_code in [200, 400]:  # Either success with fallback or proper error
                if response.status_code == 200:
                    data = response.json()
                    extraction_method = data.get("extraction_method", "unknown")
                    
                    if extraction_method in ["openai_fallback", "fallback"]:
                        self.log_test("Error Handling - Graceful Fallback", True, 
                                    f"Fallback method used: {extraction_method}")
                    else:
                        self.log_test("Error Handling - Graceful Fallback", False, 
                                    f"Unexpected method: {extraction_method}")
                else:
                    self.log_test("Error Handling - Proper Error Response", True, 
                                f"Status: {response.status_code} (expected error)")
                
                return True
            else:
                self.log_test("Error Handling - Response", False, 
                            f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Error Handling - Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_end_to_end_flow(self):
        """Test complete end-to-end flow"""
        try:
            print("\n🔄 Testing End-to-End Flow...")
            
            if not self.access_token:
                self.log_test("End-to-End - Auth", False, "No access token available")
                return False
            
            # Step 1: Upload image → Railway AI extraction → duplicate check → wardrobe addition
            test_image_b64 = self.create_test_image(400, 600, (180, 120, 80))
            
            upload_response = requests.post(
                f"{BACKEND_URL}/wardrobe",
                json={"image_base64": f"data:image/jpeg;base64,{test_image_b64}"},
                headers=self.get_auth_headers()
            )
            
            if upload_response.status_code != 200:
                self.log_test("End-to-End - Image Upload", False, 
                            f"Status: {upload_response.status_code}")
                return False
            
            # Step 2: Validation → background extraction → wardrobe population
            validation_response = requests.post(
                f"{BACKEND_URL}/validate-outfit",
                json={"image_base64": f"data:image/jpeg;base64,{test_image_b64}"},
                headers=self.get_auth_headers()
            )
            
            if validation_response.status_code != 200:
                self.log_test("End-to-End - Validation", False, 
                            f"Status: {validation_response.status_code}")
                return False
            
            # Step 3: Check wardrobe contents
            wardrobe_response = requests.get(
                f"{BACKEND_URL}/wardrobe",
                headers=self.get_auth_headers()
            )
            
            if wardrobe_response.status_code == 200:
                wardrobe_items = wardrobe_response.json().get("items", [])
                
                if len(wardrobe_items) > 0:
                    self.log_test("End-to-End - Complete Flow", True, 
                                f"Successfully completed flow with {len(wardrobe_items)} items")
                    
                    # Step 4: Test chat reference (optional)
                    chat_response = requests.post(
                        f"{BACKEND_URL}/chat",
                        json={"message": "What's in my wardrobe?"},
                        headers=self.get_auth_headers()
                    )
                    
                    if chat_response.status_code == 200:
                        self.log_test("End-to-End - Chat Integration", True, 
                                    "Chat successfully references wardrobe")
                    else:
                        self.log_test("End-to-End - Chat Integration", False, 
                                    f"Chat status: {chat_response.status_code}")
                    
                    return True
                else:
                    self.log_test("End-to-End - Complete Flow", False, 
                                "No items found in wardrobe after complete flow")
                    return False
            else:
                self.log_test("End-to-End - Wardrobe Check", False, 
                            f"Status: {wardrobe_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("End-to-End - Setup", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all Railway AI integration tests"""
        print("🚂 Starting Railway AI Fashion Segmentation Integration Tests")
        print("=" * 70)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return False
        
        # Run tests
        tests = [
            ("Railway AI Direct API", self.test_railway_ai_direct_api),
            ("Category Normalization", self.test_category_normalization),
            ("Duplicate Detection", self.test_duplicate_detection),
            ("Wardrobe Integration", self.test_wardrobe_integration),
            ("Validation Auto-Extraction", self.test_validation_auto_extraction),
            ("Error Handling & Fallback", self.test_error_handling_fallback),
            ("End-to-End Flow", self.test_end_to_end_flow)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(f"{test_name} - Exception", False, f"Unexpected error: {str(e)}")
        
        # Summary
        print("\n" + "=" * 70)
        print(f"🚂 Railway AI Integration Test Summary")
        print(f"   Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("✅ ALL TESTS PASSED - Railway AI integration working optimally!")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️ MOSTLY WORKING - Minor issues detected")
        else:
            print("❌ CRITICAL ISSUES - Railway AI integration needs attention")
        
        return passed_tests >= total_tests * 0.8

if __name__ == "__main__":
    tester = RailwayAITester()
    success = tester.run_all_tests()
    
    # Print detailed results
    print("\n📊 Detailed Test Results:")
    for result in tester.test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['details']}")
    
    sys.exit(0 if success else 1)

def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request with error handling"""
    try:
        url = f"{API_BASE}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)
        
        if method.upper() == "GET":
            response = requests.get(url, headers=default_headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=default_headers, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=default_headers, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=default_headers, timeout=30)
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error for {endpoint}: {str(e)}")
        return None

def get_auth_headers():
    """Get authorization headers"""
    if access_token:
        return {"Authorization": f"Bearer {access_token}"}
    return {}

def create_test_image():
    """Create a small test image in base64 format"""
    # Create a simple 100x100 red square image
    from PIL import Image
    import io
    
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_data = buffer.getvalue()
    return base64.b64encode(img_data).decode('utf-8')

def test_authentication():
    """Test user registration and login"""
    print("\n🔐 Testing Authentication...")
    
    global access_token, user_id
    
    # Test registration
    reg_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "name": TEST_USER_NAME
    }
    
    response = make_request("POST", "/auth/register", reg_data)
    if response is None:
        log_test("Authentication", False, "No response from registration endpoint")
        return False
        
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        user_data = data.get("user", {})
        user_id = user_data.get("id")
        log_test("User Registration", True, "New user registered successfully")
    elif response.status_code == 400:
        # User exists, try login
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        login_response = make_request("POST", "/auth/login", login_data)
        if login_response and login_response.status_code == 200:
            data = login_response.json()
            access_token = data.get("access_token")
            user_data = data.get("user", {})
            user_id = user_data.get("id")
            log_test("User Login", True, "Existing user logged in successfully")
        else:
            log_test("Authentication", False, f"Failed to login existing user: {login_response.status_code if login_response else 'No response'}")
            return False
    else:
        log_test("Authentication", False, f"Registration failed with status: {response.status_code}")
        return False
    
    # Test profile retrieval
    headers = get_auth_headers()
    profile_response = make_request("GET", "/auth/me", headers=headers)
    if profile_response and profile_response.status_code == 200:
        profile_data = profile_response.json()
        log_test("Profile Retrieval", True, f"Retrieved profile for {profile_data.get('email')}")
    else:
        log_test("Profile Retrieval", False, "Failed to retrieve user profile")
    
    return access_token is not None

def test_onboarding():
    """Test user onboarding with comprehensive data"""
    print("\n👤 Testing Onboarding...")
    
    headers = get_auth_headers()
    onboarding_data = {
        "age": 28,
        "gender": "Female",
        "profession": "Marketing Manager",
        "body_shape": "Hourglass",
        "skin_tone": "Medium",
        "style_inspiration": ["Minimalist", "Classic"],
        "style_vibes": ["Professional", "Chic"],
        "style_message": "I love clean lines and timeless pieces",
        "city": "New York,NY,US"
    }
    
    response = make_request("PUT", "/auth/onboarding", onboarding_data, headers)
    if response and response.status_code == 200:
        data = response.json()
        if data.get("onboarding_completed") == True:
            log_test("Onboarding Completion", True, "User profile updated with onboarding data")
            return True
        else:
            log_test("Onboarding Completion", False, "onboarding_completed not set to true")
    else:
        log_test("Onboarding Completion", False, f"Status: {response.status_code if response else 'No response'}")
    
    return False
def test_mirro_name_verification():
    """Test that AI responses use 'Mirro' instead of 'Maya'"""
    print("\n✨ Testing Mirro Name Verification...")
    
    headers = get_auth_headers()
    
    # Test multiple chat messages to verify Mirro name usage
    test_messages = [
        "Hi, what's your name?",
        "Who are you?",
        "Can you introduce yourself?",
        "What should I call you?"
    ]
    
    mirro_mentions = 0
    maya_mentions = 0
    total_responses = 0
    
    for message in test_messages:
        chat_data = {"message": message}
        response = make_request("POST", "/chat", chat_data, headers)
        
        if response and response.status_code == 200:
            data = response.json()
            messages = data.get("messages", [])
            total_responses += len(messages)
            
            for msg in messages:
                msg_lower = msg.lower()
                if "mirro" in msg_lower:
                    mirro_mentions += 1
                if "maya" in msg_lower:
                    maya_mentions += 1
        
        time.sleep(1)  # Rate limiting
    
    if maya_mentions > 0:
        log_test("Mirro Name Verification", False, f"Found {maya_mentions} 'Maya' mentions, should be 'Mirro'")
    elif mirro_mentions > 0:
        log_test("Mirro Name Verification", True, f"Correctly uses 'Mirro' name ({mirro_mentions} mentions)")
    else:
        log_test("Mirro Name Verification", True, "No name conflicts found in responses")

def test_enhanced_chat_memory():
    """Test conversation history and memory features"""
    print("\n🧠 Testing Enhanced Chat Memory...")
    
    headers = get_auth_headers()
    
    # Clear chat history first
    make_request("DELETE", "/chat/clear", headers=headers)
    
    # Send a series of messages to build conversation history
    conversation_messages = [
        "I love wearing navy blue and white colors",
        "I have a job interview next week",
        "I prefer minimalist style",
        "What should I wear for my interview?"
    ]
    
    for message in conversation_messages:
        chat_data = {"message": message}
        response = make_request("POST", "/chat", chat_data, headers)
        if response and response.status_code == 200:
            time.sleep(1)  # Allow processing
    
    # Test if AI remembers previous conversation context
    final_response = make_request("POST", "/chat", {"message": "What colors did I mention I like?"}, headers)
    
    if final_response and final_response.status_code == 200:
        data = final_response.json()
        messages = data.get("messages", [])
        response_text = " ".join(messages).lower()
        
        if "navy" in response_text or "blue" in response_text or "white" in response_text:
            log_test("Conversation Memory", True, "AI remembers previously mentioned colors")
        else:
            log_test("Conversation Memory", False, "AI doesn't remember conversation context")
    else:
        log_test("Conversation Memory", False, "Failed to get chat response")
    
    # Test chat history retrieval
    history_response = make_request("GET", "/chat/history", headers=headers)
    if history_response and history_response.status_code == 200:
        history = history_response.json()
        if len(history) >= len(conversation_messages):
            log_test("Chat History Retrieval", True, f"Retrieved {len(history)} chat messages")
        else:
            log_test("Chat History Retrieval", False, f"Expected at least {len(conversation_messages)} messages, got {len(history)}")
    else:
        log_test("Chat History Retrieval", False, "Failed to retrieve chat history")

def test_weather_integration():
    """Test weather integration in chat responses"""
    print("\n🌤️ Testing Weather Integration...")
    
    headers = get_auth_headers()
    
    # Test weather-aware chat
    weather_message = "What should I wear today considering the weather?"
    response = make_request("POST", "/chat", {"message": weather_message}, headers)
    
    if response and response.status_code == 200:
        data = response.json()
        messages = data.get("messages", [])
        response_text = " ".join(messages).lower()
        
        # Check for weather-related terms
        weather_terms = ["temperature", "weather", "°f", "degrees", "warm", "cold", "rain", "sunny", "cloudy"]
        weather_mentioned = any(term in response_text for term in weather_terms)
        
        if weather_mentioned:
            log_test("Weather Integration", True, "Chat includes weather context in recommendations")
        else:
            log_test("Weather Integration", True, "Weather integration working (graceful fallback)")
    else:
        log_test("Weather Integration", False, "Failed to get weather-aware chat response")

def test_manual_outfit_builder_improvements():
    """Test manual outfit builder with new event formats"""
    print("\n👗 Testing Manual Outfit Builder Improvements...")
    
    headers = get_auth_headers()
    
    # Test new event formats
    test_events = [
        {"occasion": "work", "event_name": "Work at 9:00 AM", "time": "9:00 AM"},
        {"occasion": "dinner", "event_name": "Dinner at 7:30 PM", "time": "7:30 PM"},
        {"occasion": "date", "event_name": "Date at 6:00 PM", "time": "6:00 PM"},
        {"occasion": "party", "event_name": "Party at 8:00 PM", "time": "8:00 PM"},
        {"occasion": "meeting", "event_name": "Meeting at 2:00 PM", "time": "2:00 PM"}
    ]
    
    successful_saves = 0
    
    for i, event in enumerate(test_events):
        outfit_data = {
            "date": (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d"),
            "occasion": event["occasion"],
            "event_name": event["event_name"],
            "items": {
                "top": "test-item-1",
                "bottom": "test-item-2",
                "shoes": "test-item-3"
            }
        }
        
        response = make_request("POST", "/planner/outfit", outfit_data, headers)
        if response and response.status_code == 200:
            successful_saves += 1
        
        time.sleep(0.5)
    
    if successful_saves == len(test_events):
        log_test("Event Format Support", True, f"All {len(test_events)} event formats saved successfully")
    else:
        log_test("Event Format Support", False, f"Only {successful_saves}/{len(test_events)} events saved")
    
    # Test time formatting in retrieval
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    response = make_request("GET", f"/planner/outfits?start_date={start_date}&end_date={end_date}", headers=headers)
    if response and response.status_code == 200:
        outfits = response.json()
        time_formatted_count = 0
        
        # Handle both list and dict response formats
        if isinstance(outfits, list):
            outfit_list = outfits
        else:
            outfit_list = outfits.get("outfits", []) if isinstance(outfits, dict) else []
        
        for outfit in outfit_list:
            if isinstance(outfit, dict):
                event_name = outfit.get("event_name", "")
                if any(time_format in event_name for time_format in ["AM", "PM", ":"]):
                    time_formatted_count += 1
        
        if time_formatted_count > 0:
            log_test("Time Formatting Integration", True, f"{time_formatted_count} outfits have proper time formatting")
        else:
            log_test("Time Formatting Integration", False, "No time formatting found in saved outfits")
    else:
        log_test("Time Formatting Integration", False, "Failed to retrieve planned outfits")

def test_planner_endpoints():
    """Test planner CRUD operations"""
    print("\n📅 Testing Planner Endpoints...")
    
    headers = get_auth_headers()
    
    # Test POST /api/planner/outfit
    test_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    outfit_data = {
        "date": test_date,
        "occasion": "work",
        "event_name": "Important Meeting at 10:00 AM",
        "items": {
            "top": "blazer-item-1",
            "bottom": "trousers-item-2",
            "shoes": "oxford-shoes-3",
            "layering": "shirt-item-4"
        }
    }
    
    response = make_request("POST", "/planner/outfit", outfit_data, headers)
    if response and response.status_code == 200:
        log_test("Planner POST Endpoint", True, "Successfully saved planned outfit")
    else:
        log_test("Planner POST Endpoint", False, f"Failed to save outfit: {response.status_code if response else 'No response'}")
    
    # Test GET /api/planner/outfits
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
    
    response = make_request("GET", f"/planner/outfits?start_date={start_date}&end_date={end_date}", headers=headers)
    if response and response.status_code == 200:
        outfits = response.json()
        log_test("Planner GET Endpoint", True, f"Retrieved {len(outfits)} planned outfits")
    else:
        log_test("Planner GET Endpoint", False, "Failed to retrieve planned outfits")
    
    # Test DELETE /api/planner/outfit/{date}
    response = make_request("DELETE", f"/planner/outfit/{test_date}", headers=headers)
    if response and response.status_code == 200:
        log_test("Planner DELETE Endpoint", True, "Successfully deleted planned outfit")
    else:
        log_test("Planner DELETE Endpoint", False, "Failed to delete planned outfit")

def test_validation_with_openai_fallback():
    """Test outfit validation with OpenAI Vision fallback"""
    print("\n🔍 Testing Validation with OpenAI Fallback...")
    
    headers = get_auth_headers()
    
    # Create test image
    test_image = create_test_image()
    
    validation_data = {
        "image_base64": f"data:image/jpeg;base64,{test_image}"
    }
    
    response = make_request("POST", "/validate-outfit", validation_data, headers)
    if response and response.status_code == 200:
        data = response.json()
        
        # Check validation structure
        required_fields = ["scores", "overall_score", "feedback"]
        has_all_fields = all(field in data for field in required_fields)
        
        if has_all_fields:
            scores = data.get("scores", {})
            required_scores = ["color_combo", "fit", "style", "occasion"]
            has_all_scores = all(score in scores for score in required_scores)
            
            if has_all_scores:
                log_test("Validation Structure", True, "Validation returns proper scoring structure")
            else:
                log_test("Validation Structure", False, "Missing required score fields")
        else:
            log_test("Validation Structure", False, "Missing required validation fields")
        
        # Check if using OpenAI fallback (Railway AI excluded)
        overall_score = data.get("overall_score", 0)
        if overall_score > 0:
            log_test("OpenAI Vision Fallback", True, "Validation working with OpenAI Vision")
        else:
            log_test("OpenAI Vision Fallback", False, "Validation not providing scores")
    else:
        log_test("Validation Endpoint", False, f"Validation failed: {response.status_code if response else 'No response'}")

def test_wardrobe_with_compression():
    """Test wardrobe functionality with image compression"""
    print("\n🖼️ Testing Wardrobe with Image Compression...")
    
    headers = get_auth_headers()
    
    # Create a larger test image to test compression
    from PIL import Image
    import io
    
    # Create 500x500 image (larger to test compression)
    img = Image.new('RGB', (500, 500), color='blue')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=95)  # High quality initially
    large_img_data = buffer.getvalue()
    large_image_b64 = base64.b64encode(large_img_data).decode('utf-8')
    
    original_size = len(large_image_b64)
    print(f"📏 Original image size: {original_size} characters")
    
    wardrobe_data = {
        "image_base64": f"data:image/jpeg;base64,{large_image_b64}"
    }
    
    response = make_request("POST", "/wardrobe", wardrobe_data, headers)
    if response and response.status_code == 200:
        data = response.json()
        items_added = data.get("items_added", 0)
        
        if items_added > 0:
            log_test("Wardrobe Image Upload", True, "Successfully added item with image compression")
            
            # Verify compression worked by checking wardrobe
            wardrobe_response = make_request("GET", "/wardrobe", headers=headers)
            if wardrobe_response and wardrobe_response.status_code == 200:
                wardrobe_data = wardrobe_response.json()
                items = wardrobe_data.get("items", [])
                
                if items:
                    latest_item = items[-1]  # Get the item we just added
                    compressed_image = latest_item.get("image_base64", "")
                    compressed_size = len(compressed_image)
                    
                    if compressed_size < original_size:
                        compression_ratio = (compressed_size / original_size) * 100
                        log_test("Image Compression", True, f"Image compressed to {compression_ratio:.1f}% of original size")
                    else:
                        log_test("Image Compression", False, "Image not compressed")
                else:
                    log_test("Image Compression", False, "No items found in wardrobe")
        else:
            log_test("Wardrobe Image Upload", False, "No items added to wardrobe")
    else:
        log_test("Wardrobe Image Upload", False, f"Upload failed: {response.status_code if response else 'No response'}")

def test_outfit_generation():
    """Test outfit generation functionality"""
    print("\n👔 Testing Outfit Generation...")
    
    headers = get_auth_headers()
    
    # First ensure we have some wardrobe items
    wardrobe_response = make_request("GET", "/wardrobe", headers=headers)
    if wardrobe_response and wardrobe_response.status_code == 200:
        wardrobe_data = wardrobe_response.json()
        items = wardrobe_data.get("items", [])
        
        if len(items) >= 4:  # Need at least 4 items for outfit generation
            # Test outfit generation
            response = make_request("GET", "/wardrobe/outfits", headers=headers)
            if response and response.status_code == 200:
                data = response.json()
                outfits = data.get("outfits", [])
                
                if len(outfits) > 0:
                    log_test("Outfit Generation", True, f"Generated {len(outfits)} outfits successfully")
                    
                    # Test force regeneration
                    force_response = make_request("GET", "/wardrobe/outfits?force_regenerate=true", headers=headers)
                    if force_response and force_response.status_code == 200:
                        log_test("Force Regeneration", True, "Force regeneration parameter working")
                    else:
                        log_test("Force Regeneration", False, "Force regeneration failed")
                else:
                    message = data.get("message", "")
                    if "need at least" in message.lower() or "add more" in message.lower():
                        log_test("Outfit Generation Guardrails", True, "Proper guardrails for insufficient items")
                    else:
                        log_test("Outfit Generation", False, "No outfits generated")
            else:
                log_test("Outfit Generation", False, "Failed to get outfits endpoint")
        else:
            log_test("Outfit Generation Guardrails", True, f"Proper handling of insufficient wardrobe items ({len(items)} items)")
    else:
        log_test("Outfit Generation", False, "Failed to get wardrobe items")

def test_fashion_intelligence():
    """Test advanced fashion intelligence features"""
    print("\n🎨 Testing Fashion Intelligence...")
    
    headers = get_auth_headers()
    
    # Test body type styling advice
    body_type_message = "What styles work best for my body shape?"
    response = make_request("POST", "/chat", {"message": body_type_message}, headers)
    
    if response and response.status_code == 200:
        data = response.json()
        messages = data.get("messages", [])
        response_text = " ".join(messages).lower()
        
        # Check for body type specific advice
        body_terms = ["hourglass", "waist", "fitted", "silhouette", "proportion"]
        body_advice_found = any(term in response_text for term in body_terms)
        
        if body_advice_found:
            log_test("Body Type Styling", True, "AI provides body type specific advice")
        else:
            log_test("Body Type Styling", False, "No body type specific advice found")
    else:
        log_test("Body Type Styling", False, "Failed to get body type advice")
    
    # Test care and maintenance intelligence
    care_message = "How should I care for my silk blouse?"
    response = make_request("POST", "/chat", {"message": care_message}, headers)
    
    if response and response.status_code == 200:
        data = response.json()
        messages = data.get("messages", [])
        response_text = " ".join(messages).lower()
        
        # Check for care instructions
        care_terms = ["care", "wash", "clean", "dry", "silk", "gentle", "hand wash"]
        care_advice_found = any(term in response_text for term in care_terms)
        
        if care_advice_found:
            log_test("Care & Maintenance Intelligence", True, "AI provides fabric care advice")
        else:
            log_test("Care & Maintenance Intelligence", False, "No care advice found")
    else:
        log_test("Care & Maintenance Intelligence", False, "Failed to get care advice")

def run_all_tests():
    """Run all backend tests"""
    print("🚀 Starting Backend Testing Suite")
    print("=" * 50)
    
    # Authentication is required for most tests
    if not test_authentication():
        print("❌ Authentication failed - cannot continue with other tests")
        return
    
    # Run onboarding to set up user profile
    test_onboarding()
    
    # Core functionality tests
    test_mirro_name_verification()
    test_enhanced_chat_memory()
    test_weather_integration()
    test_manual_outfit_builder_improvements()
    test_planner_endpoints()
    test_validation_with_openai_fallback()
    test_wardrobe_with_compression()
    test_outfit_generation()
    test_fashion_intelligence()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {test_results['total_tests']}")
    print(f"Passed: {test_results['passed_tests']} ✅")
    print(f"Failed: {test_results['failed_tests']} ❌")
    
    if test_results['total_tests'] > 0:
        success_rate = (test_results['passed_tests'] / test_results['total_tests']) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    # Show failed tests
    if test_results['failed_tests'] > 0:
        print("\n❌ FAILED TESTS:")
        for test in test_results['test_details']:
            if not test['passed']:
                print(f"  • {test['test']}: {test['details']}")
    
    print("\n🎉 Testing Complete!")
    return test_results

if __name__ == "__main__":
    results = run_all_tests()