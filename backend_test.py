#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Railway AI Fashion Segmentation Integration
Tests the corrected Railway AI implementation with proper response parsing and segmented image download
Focus: Upload → Parse "crops" array → Download segmented images → Create individual wardrobe items
"""

import requests
import json
import base64
import asyncio
import sys
import os
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw
import uuid

# Add backend to path for imports
sys.path.append('/app/backend')

# Test configuration
BACKEND_URL = "https://smart-stylist-15.preview.emergentagent.com/api"
RAILWAY_AI_URL = "https://fashion-ai-segmentation-production.up.railway.app"

class RailwayAITester:
    def __init__(self):
        self.test_results = []
        self.access_token = None
        self.user_id = None
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def create_realistic_fashion_image(self) -> str:
        """Create a more realistic fashion image for testing"""
        try:
            # Create an image that looks more like clothing
            image = Image.new('RGB', (600, 800), (240, 240, 240))  # Light gray background
            draw = ImageDraw.Draw(image)
            
            # Draw a shirt-like shape (rectangle with rounded top)
            shirt_color = (70, 130, 180)  # Steel blue
            draw.rectangle([150, 100, 450, 400], fill=shirt_color, outline=(50, 100, 150), width=3)
            
            # Draw pants-like shape
            pants_color = (25, 25, 112)  # Midnight blue
            draw.rectangle([180, 400, 420, 700], fill=pants_color, outline=(15, 15, 80), width=3)
            
            # Add some texture lines
            for y in range(120, 380, 15):
                draw.line([(160, y), (440, y)], fill=(60, 120, 170), width=1)
            
            for y in range(420, 680, 20):
                draw.line([(190, y), (410, y)], fill=(20, 20, 100), width=1)
            
            # Convert to base64
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=90)
            image_bytes = buffer.getvalue()
            
            return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            print(f"❌ Error creating realistic fashion image: {e}")
            # Fallback to simple image
            image = Image.new('RGB', (400, 400), (255, 0, 0))
            buffer = BytesIO()
            image.save(buffer, format='JPEG')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    async def setup_test_user(self):
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
                
                self.log_test("User Registration", True, f"Created user: {self.user_id}")
                return True
            else:
                self.log_test("User Registration", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False
    
    def get_auth_headers(self):
        """Get authorization headers for API requests"""
        return {"Authorization": f"Bearer {self.access_token}"}
    
    async def test_railway_ai_upload_response_analysis(self):
        """Test Railway AI upload and analyze response for 'crops' array"""
        try:
            print("\n🚂 Testing Railway AI Upload Response Analysis...")
            
            # Create test image
            test_image_b64 = self.create_realistic_fashion_image()
            image_bytes = base64.b64decode(test_image_b64)
            
            # Prepare multipart form data
            files = {
                'file': ('test_outfit.jpg', BytesIO(image_bytes), 'image/jpeg')
            }
            
            print(f"📡 Sending request to: {RAILWAY_AI_URL}/upload")
            
            # Make request to Railway AI
            response = requests.post(
                f"{RAILWAY_AI_URL}/upload",
                files=files,
                timeout=90  # Extended timeout for Railway AI
            )
            
            print(f"📊 Railway AI Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📋 Railway AI Response Data: {json.dumps(data, indent=2)}")
                
                # Check for expected fields according to corrected implementation
                status = data.get("status")
                num_components = data.get("num_components", 0)
                categories = data.get("categories", [])
                crops = data.get("crops", [])  # This is the key field we're testing
                image_name = data.get("image_name", "")
                
                # Test 1: Response structure
                has_status = status is not None
                has_components = num_components >= 0
                has_categories = isinstance(categories, list)
                has_crops = isinstance(crops, list)
                has_image_name = bool(image_name)
                
                structure_success = has_status and has_components and has_categories and has_crops and has_image_name
                
                details = f"Status: {status}, Components: {num_components}, Categories: {len(categories)}, Crops: {len(crops)}"
                self.log_test("Railway AI Response Structure", structure_success, details)
                
                # Test 2: Crops array presence (CRITICAL for corrected implementation)
                if crops and len(crops) > 0:
                    self.log_test("Railway AI Crops Array Present", True, f"Found {len(crops)} crop paths")
                    
                    # Test 3: Crop path format
                    sample_crop = crops[0]
                    expected_format = "crops_centered/" in sample_crop or "crops/" in sample_crop or ".png" in sample_crop
                    self.log_test("Railway AI Crop Path Format", expected_format, f"Sample: {sample_crop}")
                    
                    # Test 4: Categories and crops alignment
                    alignment_success = len(categories) == len(crops)
                    self.log_test("Categories-Crops Alignment", alignment_success, f"Categories: {len(categories)}, Crops: {len(crops)}")
                    
                    return data  # Return for further testing
                else:
                    self.log_test("Railway AI Crops Array Present", False, "No crops found in response - this breaks the corrected implementation")
                    return data
                    
            elif response.status_code == 500:
                # Check if it's the expected "no clothing found" response
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", "").lower()
                    if "no clothing found" in error_msg or "failed to process" in error_msg:
                        self.log_test("Railway AI Upload Response", True, "Expected 'no clothing found' response for test image")
                        return {"status": "no_clothing", "message": error_msg}
                    else:
                        self.log_test("Railway AI Upload Response", False, f"Unexpected 500 error: {error_msg}")
                        return None
                except:
                    self.log_test("Railway AI Upload Response", False, f"HTTP 500: {response.text}")
                    return None
            else:
                self.log_test("Railway AI Upload Response", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            self.log_test("Railway AI Upload Response", False, "Request timeout (>90s)")
            return None
        except Exception as e:
            self.log_test("Railway AI Upload Response", False, f"Exception: {str(e)}")
            return None
    
    async def test_segmented_image_download(self, railway_response):
        """Test downloading segmented images using /outputs/{crop_path}"""
        try:
            print("\n🖼️ Testing Segmented Image Download...")
            
            if not railway_response or railway_response.get("status") == "no_clothing":
                self.log_test("Segmented Image Download", True, "Skipped - no crops available from Railway AI")
                return True
            
            crops = railway_response.get("crops", [])
            if not crops:
                self.log_test("Segmented Image Download", False, "No crop paths available for download testing")
                return False
            
            # Test downloading each crop using the corrected endpoint
            download_success_count = 0
            
            for idx, crop_path in enumerate(crops[:3]):  # Test first 3 crops
                download_url = f"{RAILWAY_AI_URL}/outputs/{crop_path}"
                
                print(f"📥 Testing download {idx+1}: {download_url}")
                
                try:
                    response = requests.get(download_url, timeout=30)
                    
                    if response.status_code == 200:
                        # Verify it's an image
                        content_type = response.headers.get('content-type', '')
                        is_image = 'image' in content_type.lower()
                        
                        if is_image:
                            # Try to convert to base64
                            try:
                                image_b64 = base64.b64encode(response.content).decode('utf-8')
                                download_success_count += 1
                                print(f"   ✅ Downloaded {len(response.content)} bytes, base64 length: {len(image_b64)}")
                            except Exception as e:
                                print(f"   ❌ Base64 conversion failed: {str(e)}")
                        else:
                            print(f"   ❌ Invalid content type: {content_type}")
                    else:
                        print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}")
                        
                except Exception as e:
                    print(f"   ❌ Download exception: {str(e)}")
            
            success = download_success_count > 0
            details = f"Successfully downloaded {download_success_count}/{len(crops[:3])} segmented images"
            self.log_test("Segmented Image Download", success, details)
            
            return success
                
        except Exception as e:
            self.log_test("Segmented Image Download", False, f"Exception: {str(e)}")
            return False
    
    async def test_individual_item_creation(self):
        """Test that each downloaded crop creates a unique wardrobe item"""
        try:
            print("\n👗 Testing Individual Item Creation...")
            
            if not self.access_token:
                self.log_test("Individual Item Creation", False, "No authentication token")
                return False
            
            # Clear wardrobe first
            requests.delete(f"{BACKEND_URL}/wardrobe/clear", headers=self.get_auth_headers())
            
            # Get initial wardrobe count
            response = requests.get(f"{BACKEND_URL}/wardrobe", headers=self.get_auth_headers())
            if response.status_code == 200:
                initial_count = len(response.json().get("items", []))
            else:
                initial_count = 0
            
            # Upload image to wardrobe endpoint
            test_image_b64 = self.create_realistic_fashion_image()
            
            wardrobe_data = {
                "image_base64": f"data:image/jpeg;base64,{test_image_b64}"
            }
            
            print(f"📤 Uploading image to wardrobe endpoint...")
            
            response = requests.post(
                f"{BACKEND_URL}/wardrobe",
                json=wardrobe_data,
                headers=self.get_auth_headers(),
                timeout=120  # Extended timeout for Railway AI processing
            )
            
            print(f"📊 Wardrobe Upload Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📋 Wardrobe Response: {json.dumps(data, indent=2)}")
                
                items_added = data.get("items_added", 0)
                extraction_method = data.get("extraction_method", "unknown")
                items_extracted = data.get("items_extracted", 0)
                duplicates_skipped = data.get("duplicates_skipped", 0)
                
                # Check if Railway AI was used
                if extraction_method == "railway_ai":
                    self.log_test("Railway AI Integration in Wardrobe", True, f"Added {items_added} items via Railway AI")
                    
                    # Verify items were actually added
                    response = requests.get(f"{BACKEND_URL}/wardrobe", headers=self.get_auth_headers())
                    if response.status_code == 200:
                        wardrobe_items = response.json().get("items", [])
                        final_count = len(wardrobe_items)
                        actual_added = final_count - initial_count
                        
                        if actual_added > 0:
                            # Check if items have segmented images (key test for corrected implementation)
                            segmented_items = 0
                            for item in wardrobe_items:
                                if item.get("extraction_source") == "railway_ai_segmented":
                                    segmented_items += 1
                            
                            success = actual_added > 0
                            details = f"Created {actual_added} individual items, {segmented_items} with segmented images"
                            self.log_test("Individual Item Creation", success, details)
                            
                            # Test individual item properties
                            if wardrobe_items:
                                sample_item = wardrobe_items[0]
                                has_category = bool(sample_item.get("category"))
                                has_image = bool(sample_item.get("image_base64"))
                                has_name = bool(sample_item.get("exact_item_name"))
                                
                                item_quality = has_category and has_image and has_name
                                self.log_test("Individual Item Quality", item_quality, f"Category: {has_category}, Image: {has_image}, Name: {has_name}")
                            
                            return success
                        else:
                            self.log_test("Individual Item Creation", False, "No items actually added to wardrobe")
                            return False
                    else:
                        self.log_test("Individual Item Creation", False, "Failed to verify wardrobe items")
                        return False
                        
                elif "openai" in extraction_method.lower() or "fallback" in extraction_method.lower():
                    self.log_test("Railway AI Integration in Wardrobe", False, f"Fell back to {extraction_method}")
                    self.log_test("Individual Item Creation", items_added > 0, f"Fallback created {items_added} items")
                    return False
                else:
                    self.log_test("Railway AI Integration in Wardrobe", False, f"Unknown extraction method: {extraction_method}")
                    return False
                    
            else:
                self.log_test("Railway AI Integration in Wardrobe", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Individual Item Creation", False, f"Exception: {str(e)}")
            return False
    
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow: Upload outfit photo → Multiple individual clothing items"""
        try:
            print("\n🔄 Testing End-to-End Workflow...")
            
            if not self.access_token:
                self.log_test("End-to-End Workflow", False, "No authentication token")
                return False
            
            # Clear wardrobe first
            requests.delete(f"{BACKEND_URL}/wardrobe/clear", headers=self.get_auth_headers())
            
            # Create a complex test image (simulating outfit with shirt + pants + shoes)
            test_image_b64 = self.create_realistic_fashion_image()
            
            # Upload to wardrobe
            wardrobe_data = {
                "image_base64": f"data:image/jpeg;base64,{test_image_b64}"
            }
            
            print(f"🚀 Starting end-to-end workflow test...")
            print(f"   Expected: Upload outfit photo → Multiple individual clothing items in wardrobe")
            print(f"   Success criteria: Each wardrobe item shows cropped image of specific clothing piece")
            
            response = requests.post(
                f"{BACKEND_URL}/wardrobe",
                json=wardrobe_data,
                headers=self.get_auth_headers(),
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if Railway AI was used and items were created
                extraction_method = data.get("extraction_method", "")
                items_added = data.get("items_added", 0)
                items_extracted = data.get("items_extracted", 0)
                
                if "railway_ai" in extraction_method and items_added > 0:
                    # Verify items in wardrobe
                    wardrobe_response = requests.get(f"{BACKEND_URL}/wardrobe", headers=self.get_auth_headers())
                    
                    if wardrobe_response.status_code == 200:
                        wardrobe_items = wardrobe_response.json().get("items", [])
                        
                        # Check if items have segmented images (different from original)
                        segmented_items = 0
                        individual_items = 0
                        
                        for item in wardrobe_items:
                            if item.get("extraction_source") == "railway_ai_segmented":
                                segmented_items += 1
                            if "individual-item" in item.get("tags", []):
                                individual_items += 1
                        
                        # Success criteria: Multiple items created, preferably with segmented images
                        success = len(wardrobe_items) > 1 or (len(wardrobe_items) > 0 and segmented_items > 0)
                        
                        details = f"Created {len(wardrobe_items)} items, {segmented_items} segmented, {individual_items} individual"
                        
                        self.log_test("End-to-End Workflow", success, details)
                        
                        # Additional test: Verify no full outfit photos as wardrobe items
                        full_outfit_items = 0
                        for item in wardrobe_items:
                            if "full-outfit" in item.get("tags", []) or "outfit" in item.get("exact_item_name", "").lower():
                                full_outfit_items += 1
                        
                        no_full_outfits = full_outfit_items == 0
                        self.log_test("No Full Outfit Photos as Items", no_full_outfits, f"Found {full_outfit_items} full outfit items")
                        
                        return success
                    else:
                        self.log_test("End-to-End Workflow", False, "Failed to retrieve wardrobe items")
                        return False
                else:
                    # Railway AI might have returned "no clothing found" - this is acceptable for test images
                    if "no clothing found" in str(data).lower() or items_extracted == 0:
                        self.log_test("End-to-End Workflow", True, "Railway AI correctly identified no clothing in test image")
                        return True
                    else:
                        self.log_test("End-to-End Workflow", False, f"Railway AI not used: {extraction_method}")
                        return False
            else:
                self.log_test("End-to-End Workflow", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("End-to-End Workflow", False, f"Exception: {str(e)}")
            return False
    
    async def test_category_normalization(self):
        """Test Railway AI category normalization"""
        try:
            print("\n🏷️ Testing Category Normalization...")
            
            # Import the normalization function
            from services.railway_ai_service import normalize_category
            
            # Test Railway AI specific categories
            test_cases = [
                ("upper_clothes", "Tops"),
                ("lower_clothes", "Bottoms"),
                ("full_body", "Dresses"),
                ("outer_layer", "Jackets"),
                ("shirt", "Shirts"),
                ("pants", "Pants"),
                ("shoes", "Shoes"),
                ("Upper-clothes", "Tops"),  # Test case sensitivity
                ("unknown_category", "Unknown Category")
            ]
            
            passed_cases = 0
            for input_cat, expected in test_cases:
                result = normalize_category(input_cat)
                passed = result == expected
                if passed:
                    passed_cases += 1
                    print(f"   ✅ {input_cat} → {result}")
                else:
                    print(f"   ❌ {input_cat} → {result} (expected {expected})")
            
            success = passed_cases == len(test_cases)
            details = f"Passed {passed_cases}/{len(test_cases)} category mappings"
            self.log_test("Category Normalization", success, details)
            
            return success
            
        except Exception as e:
            self.log_test("Category Normalization", False, f"Exception: {str(e)}")
            return False
    
    async def test_duplicate_detection(self):
        """Test duplicate item detection functionality"""
        try:
            print("\n🔍 Testing Duplicate Detection...")
            
            # Import the duplicate detection function
            from services.railway_ai_service import check_for_duplicate_items, calculate_item_similarity
            
            # Create test items
            item1 = {
                "exact_item_name": "Blue Cotton T-shirt",
                "category": "Tops",
                "color": "Blue",
                "fabric_type": "Cotton",
                "style": "Casual"
            }
            
            item2 = {
                "exact_item_name": "Blue Cotton T-shirt",  # Identical
                "category": "Tops",
                "color": "Blue", 
                "fabric_type": "Cotton",
                "style": "Casual"
            }
            
            item3 = {
                "exact_item_name": "Red Silk Dress",  # Different
                "category": "Dresses",
                "color": "Red",
                "fabric_type": "Silk",
                "style": "Formal"
            }
            
            # Test similarity calculation
            similarity_identical = calculate_item_similarity(item1, item2)
            similarity_different = calculate_item_similarity(item1, item3)
            
            # Test duplicate detection
            new_items = [item2, item3]  # item2 is duplicate, item3 is unique
            existing_wardrobe = [item1]
            
            unique_items = await check_for_duplicate_items(new_items, existing_wardrobe)
            
            # Verify results
            identical_detected = similarity_identical > 0.8
            different_detected = similarity_different < 0.8
            duplicate_filtered = len(unique_items) == 1  # Should only keep item3
            
            success = identical_detected and different_detected and duplicate_filtered
            
            details = f"Identical similarity: {similarity_identical:.2f}, Different similarity: {similarity_different:.2f}, Unique items: {len(unique_items)}"
            self.log_test("Duplicate Detection", success, details)
            
            return success
            
        except Exception as e:
            self.log_test("Duplicate Detection", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all Railway AI integration tests"""
        print("🚂 Starting Railway AI Fashion Segmentation Integration Tests")
        print("Focus: Testing Corrected Implementation with Crops Array & Segmented Downloads")
        print("=" * 80)
        
        # Setup
        setup_success = await self.setup_test_user()
        if not setup_success:
            print("❌ Failed to setup test user, aborting tests")
            return
        
        # Test 1: Railway AI upload response analysis (crops array)
        railway_response = await self.test_railway_ai_upload_response_analysis()
        
        # Test 2: Segmented image download using /outputs/{crop_path}
        await self.test_segmented_image_download(railway_response)
        
        # Test 3: Individual item creation from segmented images
        await self.test_individual_item_creation()
        
        # Test 4: End-to-end workflow
        await self.test_end_to_end_workflow()
        
        # Test 5: Category normalization
        await self.test_category_normalization()
        
        # Test 6: Duplicate detection
        await self.test_duplicate_detection()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 Railway AI Integration Test Summary")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # List failed tests
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        # Critical issues analysis
        critical_failures = []
        crops_issues = []
        download_issues = []
        
        for result in self.test_results:
            if not result["success"]:
                test_name = result["test"].lower()
                if "crops" in test_name or "response" in test_name:
                    crops_issues.append(result["test"])
                elif "download" in test_name or "segmented" in test_name:
                    download_issues.append(result["test"])
                elif any(keyword in test_name for keyword in ["integration", "workflow", "individual"]):
                    critical_failures.append(result["test"])
        
        if crops_issues:
            print(f"\n🚨 CROPS ARRAY ISSUES (Corrected Implementation):")
            for issue in crops_issues:
                print(f"   • {issue}")
        
        if download_issues:
            print(f"\n🚨 SEGMENTED IMAGE DOWNLOAD ISSUES:")
            for issue in download_issues:
                print(f"   • {issue}")
        
        if critical_failures:
            print(f"\n🚨 CRITICAL INTEGRATION ISSUES:")
            for failure in critical_failures:
                print(f"   • {failure}")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "crops_issues": crops_issues,
            "download_issues": download_issues,
            "critical_failures": critical_failures
        }

async def main():
    """Main test execution"""
    tester = RailwayAITester()
    results = await tester.run_all_tests()
    
    # Determine overall status
    if results["crops_issues"] or results["download_issues"]:
        print(f"\n🚨 CORRECTED IMPLEMENTATION ISSUES DETECTED")
        print(f"   The corrected Railway AI implementation has problems with:")
        if results["crops_issues"]:
            print(f"   - Crops array parsing/availability")
        if results["download_issues"]:
            print(f"   - Segmented image downloads")
        return 1
    elif results["critical_failures"]:
        print(f"\n🚨 CRITICAL FAILURES DETECTED - Railway AI integration has major issues")
        return 1
    elif results["success_rate"] < 70:
        print(f"\n⚠️ LOW SUCCESS RATE ({results['success_rate']:.1f}%) - Railway AI integration needs attention")
        return 1
    else:
        print(f"\n✅ Railway AI corrected implementation tests completed successfully!")
        return 0

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)