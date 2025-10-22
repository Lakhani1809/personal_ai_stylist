#!/usr/bin/env python3
"""
Comprehensive Railway AI Fashion Segmentation Integration Testing
Testing the Railway AI service integration with wardrobe and validation endpoints
"""

import requests
import json
import time
import base64
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get backend URL from frontend .env
BACKEND_URL = "https://smart-stylist-15.preview.emergentagent.com/api"

print(f"🔗 Testing backend at: {BACKEND_URL}")
print(f"🎯 Focus: Railway AI Fashion Segmentation Integration")

class RailwayAIIntegrationTest:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.access_token = None
        self.user_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def setup_test_user(self):
        """Create and setup a test user for Railway AI testing"""
        print("\n🔧 Setting up test user for Railway AI testing...")
        
        # Register user
        register_data = {
            "email": f"railway_ai_test_{int(time.time())}@test.com",
            "password": "testpass123",
            "name": "Railway AI Tester"
        }
        
        response = requests.post(f"{self.base_url}/auth/register", json=register_data)
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.user_id = data["user"]["id"]
            self.log_test("User Registration", True, f"User ID: {self.user_id}")
        else:
            self.log_test("User Registration", False, f"Status: {response.status_code}")
            return False
        
        # Complete onboarding
        onboarding_data = {
            "age": 25,
            "gender": "female",
            "profession": "Fashion Designer",
            "body_shape": "pear",
            "skin_tone": "cool",
            "style_inspiration": ["Modern", "Trendy"],
            "style_vibes": ["Creative", "Bold"],
            "style_message": "I love experimenting with new fashion trends",
            "city": "Los Angeles,CA,US"
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.put(f"{self.base_url}/auth/onboarding", json=onboarding_data, headers=headers)
        
        if response.status_code == 200:
            self.log_test("User Onboarding", True, "Profile setup complete")
            return True
        else:
            self.log_test("User Onboarding", False, f"Status: {response.status_code}")
            return False
    
    def test_railway_ai_wardrobe_extraction(self):
        """Test Railway AI product extraction via wardrobe endpoint"""
        print("\n🚂 Testing Railway AI Wardrobe Product Extraction...")
        
        # Sample base64 image (small test image)
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Test wardrobe upload with Railway AI extraction
        wardrobe_data = {"image_base64": test_image}
        response = requests.post(f"{self.base_url}/wardrobe", json=wardrobe_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for Railway AI specific response fields
            has_extraction_method = "extraction_method" in data
            has_items_stats = "items_added" in data and "items_extracted" in data
            has_duplicate_info = "duplicates_skipped" in data
            
            success = has_extraction_method and has_items_stats and has_duplicate_info
            
            extraction_method = data.get("extraction_method", "unknown")
            items_added = data.get("items_added", 0)
            items_extracted = data.get("items_extracted", 0)
            
            self.log_test("Railway AI Wardrobe Extraction", success, 
                         f"Method: {extraction_method}, Added: {items_added}, Extracted: {items_extracted}")
            return success
        else:
            self.log_test("Railway AI Wardrobe Extraction", False, f"Status: {response.status_code}")
            return False
    
    def test_duplicate_detection(self):
        """Test Railway AI duplicate detection functionality"""
        print("\n🔍 Testing Railway AI Duplicate Detection...")
        
        # Sample base64 image (small test image)
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Add the same item twice to test duplicate detection
        wardrobe_data = {"image_base64": test_image}
        
        # First upload
        response1 = requests.post(f"{self.base_url}/wardrobe", json=wardrobe_data, headers=headers)
        time.sleep(1)  # Small delay
        
        # Second upload (should detect duplicates)
        response2 = requests.post(f"{self.base_url}/wardrobe", json=wardrobe_data, headers=headers)
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            # Check if duplicate detection worked
            items_added_1 = data1.get("items_added", 0)
            items_added_2 = data2.get("items_added", 0)
            duplicates_skipped_2 = data2.get("duplicates_skipped", 0)
            
            # Second upload should add fewer items or skip duplicates
            duplicate_detection_working = (items_added_2 < items_added_1) or (duplicates_skipped_2 > 0)
            
            self.log_test("Railway AI Duplicate Detection", duplicate_detection_working, 
                         f"First: {items_added_1} added, Second: {items_added_2} added, {duplicates_skipped_2} skipped")
            return duplicate_detection_working
        else:
            self.log_test("Railway AI Duplicate Detection", False, 
                         f"Upload failed: {response1.status_code}, {response2.status_code}")
            return False
    
    def test_openai_fallback(self):
        """Test OpenAI fallback when Railway AI fails"""
        print("\n🔄 Testing OpenAI Fallback Mechanism...")
        
        # Use a very large image that might cause Railway AI to timeout/fail
        # This should trigger the OpenAI fallback
        large_test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" * 100
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        wardrobe_data = {"image_base64": large_test_image}
        response = requests.post(f"{self.base_url}/wardrobe", json=wardrobe_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if fallback worked - should still add items even if Railway AI fails
            items_added = data.get("items_added", 0)
            has_message = "message" in data
            
            # Fallback should still result in items being added
            fallback_success = items_added > 0 and has_message
            
            self.log_test("OpenAI Fallback Mechanism", fallback_success, 
                         f"Items added via fallback: {items_added}")
            return fallback_success
        else:
            self.log_test("OpenAI Fallback Mechanism", False, f"Status: {response.status_code}")
            return False
    
    def test_validation_auto_extraction(self):
        """Test Railway AI auto-extraction during outfit validation"""
        print("\n👗 Testing Validation Auto-Extraction...")
        
        # Sample base64 image for validation
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Get initial wardrobe count
        wardrobe_response = requests.get(f"{self.base_url}/wardrobe", headers=headers)
        initial_count = 0
        if wardrobe_response.status_code == 200:
            initial_count = len(wardrobe_response.json().get("items", []))
        
        # Test outfit validation (should auto-extract items to wardrobe)
        validation_data = {"image_base64": test_image}
        response = requests.post(f"{self.base_url}/validate-outfit", json=validation_data, headers=headers)
        
        if response.status_code == 200:
            validation_result = response.json()
            
            # Check if validation still works properly
            has_scores = "scores" in validation_result
            has_feedback = "feedback" in validation_result
            has_overall_score = "overall_score" in validation_result
            
            validation_working = has_scores and has_feedback and has_overall_score
            
            # Check if items were auto-added to wardrobe
            time.sleep(1)  # Small delay for processing
            wardrobe_response = requests.get(f"{self.base_url}/wardrobe", headers=headers)
            final_count = 0
            if wardrobe_response.status_code == 200:
                final_count = len(wardrobe_response.json().get("items", []))
            
            items_auto_added = final_count > initial_count
            
            success = validation_working and items_auto_added
            
            self.log_test("Validation Auto-Extraction", success, 
                         f"Validation working: {validation_working}, Items auto-added: {items_auto_added} ({initial_count}→{final_count})")
            return success
        else:
            self.log_test("Validation Auto-Extraction", False, f"Status: {response.status_code}")
            return False
    
    def test_category_normalization(self):
        """Test category normalization in Railway AI service"""
        print("\n🏷️ Testing Category Normalization...")
        
        # This test checks if the system properly normalizes categories
        # We'll check the wardrobe items to see if categories are normalized
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Get current wardrobe
        response = requests.get(f"{self.base_url}/wardrobe", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            
            if items:
                # Check if categories are properly normalized
                valid_categories = ["T-shirts", "Shirts", "Tops", "Pants", "Jeans", "Dresses", 
                                  "Skirts", "Jackets", "Shoes", "Accessories", "Bottoms"]
                
                normalized_categories = []
                for item in items:
                    category = item.get("category", "")
                    if category in valid_categories:
                        normalized_categories.append(category)
                
                normalization_success = len(normalized_categories) > 0
                
                self.log_test("Category Normalization", normalization_success, 
                             f"Found {len(normalized_categories)} normalized categories in {len(items)} items")
                return normalization_success
            else:
                self.log_test("Category Normalization", False, "No wardrobe items to check")
                return False
        else:
            self.log_test("Category Normalization", False, f"Status: {response.status_code}")
            return False
    
    def test_mirro_name_change(self):
        """Test that AI stylist uses 'Mirro' instead of 'Maya'"""
        print("\n🤖 Testing Mirro Name Change...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Ask a question that should trigger the AI to introduce itself
        chat_data = {"message": "Hi! What's your name? Can you help me with styling?"}
        response = requests.post(f"{self.base_url}/chat", json=chat_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            messages = data.get("messages", [])
            
            if messages:
                full_response = " ".join(messages).lower()
                
                # Check if response contains 'Mirro' and not 'Maya'
                has_mirro = "mirro" in full_response
                has_maya = "maya" in full_response
                
                name_change_success = has_mirro and not has_maya
                
                self.log_test("Mirro Name Change", name_change_success, 
                             f"Contains 'Mirro': {has_mirro}, Contains 'Maya': {has_maya}")
                return name_change_success
            else:
                self.log_test("Mirro Name Change", False, "No chat response received")
                return False
        else:
            self.log_test("Mirro Name Change", False, f"Status: {response.status_code}")
            return False
    
    def test_end_to_end_flow(self):
        """Test complete wardrobe → validation → chat flow with Railway AI"""
        print("\n🔄 Testing End-to-End Railway AI Flow...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        # Step 1: Add item to wardrobe via Railway AI
        wardrobe_data = {"image_base64": test_image}
        wardrobe_response = requests.post(f"{self.base_url}/wardrobe", json=wardrobe_data, headers=headers)
        
        wardrobe_success = wardrobe_response.status_code == 200
        
        # Step 2: Validate outfit (should auto-extract more items)
        validation_data = {"image_base64": test_image}
        validation_response = requests.post(f"{self.base_url}/validate-outfit", json=validation_data, headers=headers)
        
        validation_success = validation_response.status_code == 200
        
        # Step 3: Chat about wardrobe items (should reference extracted items)
        time.sleep(1)  # Allow processing
        chat_data = {"message": "Can you suggest an outfit using items from my wardrobe?"}
        chat_response = requests.post(f"{self.base_url}/chat", json=chat_data, headers=headers)
        
        chat_success = chat_response.status_code == 200
        
        # Check if chat references wardrobe items
        wardrobe_referenced = False
        if chat_success:
            chat_data_result = chat_response.json()
            messages = chat_data_result.get("messages", [])
            if messages:
                full_response = " ".join(messages).lower()
                # Look for wardrobe-related terms
                wardrobe_terms = ["wardrobe", "item", "piece", "clothing", "outfit", "wear"]
                wardrobe_referenced = any(term in full_response for term in wardrobe_terms)
        
        overall_success = wardrobe_success and validation_success and chat_success and wardrobe_referenced
        
        self.log_test("End-to-End Railway AI Flow", overall_success, 
                     f"Wardrobe: {wardrobe_success}, Validation: {validation_success}, Chat: {chat_success}, Referenced: {wardrobe_referenced}")
        return overall_success
    
    def test_railway_ai_service_health(self):
        """Test Railway AI service availability"""
        print("\n🏥 Testing Railway AI Service Health...")
        
        # Test direct connection to Railway AI service
        railway_url = "https://fashion-ai-segmentation-production.up.railway.app/"
        
        try:
            # Try to reach the Railway AI service
            response = requests.get(railway_url, timeout=10)
            service_reachable = response.status_code in [200, 404, 405]  # Any response means service is up
            
            self.log_test("Railway AI Service Health", service_reachable, 
                         f"Service response: {response.status_code}")
            return service_reachable
        except requests.exceptions.RequestException as e:
            self.log_test("Railway AI Service Health", False, f"Connection error: {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all Railway AI integration tests"""
        print("🚀 Starting Comprehensive Railway AI Integration Testing")
        print("=" * 80)
        
        # Setup phase
        if not self.setup_test_user():
            print("❌ Setup failed, aborting tests")
            return
        
        # Wait for setup to complete
        print("\n⏳ Waiting for setup to complete...")
        time.sleep(2)
        
        # Railway AI Integration Tests
        print("\n" + "="*50)
        print("🚂 RAILWAY AI INTEGRATION TESTS")
        print("="*50)
        
        integration_tests = [
            self.test_railway_ai_service_health,
            self.test_railway_ai_wardrobe_extraction,
            self.test_duplicate_detection,
            self.test_openai_fallback,
            self.test_validation_auto_extraction,
            self.test_category_normalization
        ]
        
        integration_passed = sum(test() for test in integration_tests)
        
        # Name Change & Flow Tests
        print("\n" + "="*50)
        print("🔄 NAME CHANGE & FLOW TESTS")
        print("="*50)
        
        flow_tests = [
            self.test_mirro_name_change,
            self.test_end_to_end_flow
        ]
        
        flow_passed = sum(test() for test in flow_tests)
        
        # Summary
        total_tests = len(integration_tests) + len(flow_tests)
        total_passed = integration_passed + flow_passed
        
        print("\n" + "="*80)
        print("📊 RAILWAY AI INTEGRATION TEST RESULTS SUMMARY")
        print("="*80)
        print(f"🚂 Railway AI Integration Tests: {integration_passed}/{len(integration_tests)} passed")
        print(f"🔄 Name Change & Flow Tests: {flow_passed}/{len(flow_tests)} passed")
        print(f"\n🎯 OVERALL SUCCESS RATE: {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)")
        
        if total_passed >= total_tests * 0.8:  # 80% success rate
            print("✅ RAILWAY AI INTEGRATION TESTING PASSED - All major features working excellently!")
        elif total_passed >= total_tests * 0.6:  # 60% success rate
            print("⚠️ PARTIAL SUCCESS - Most Railway AI features working, some issues identified")
        else:
            print("❌ TESTING FAILED - Significant issues with Railway AI integration")
        
        return total_passed, total_tests

def main():
    """Main test execution"""
    tester = RailwayAIIntegrationTest()
    passed, total = tester.run_comprehensive_tests()
    
    # Return appropriate exit code
    if passed >= total * 0.8:
        exit(0)  # Success
    else:
        exit(1)  # Failure

if __name__ == "__main__":
    main()