#!/usr/bin/env python3
"""
Backend Testing Suite for AI Stylist App - Wardrobe Fixes Testing
Tests the fixes for wardrobe issues: image compression, outfit generation guardrails, and category analysis
"""

import asyncio
import requests
import json
import os
import sys
import base64
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image
from io import BytesIO

# Add backend to path for imports
sys.path.append('/app/backend')

class WardrobeFixesTester:
    def __init__(self):
        # Get backend URL from frontend env
        with open('/app/frontend/.env', 'r') as f:
            env_content = f.read()
            for line in env_content.split('\n'):
                if line.startswith('EXPO_PUBLIC_BACKEND_URL='):
                    self.base_url = line.split('=')[1].strip()
                    break
        
        if not hasattr(self, 'base_url'):
            self.base_url = "https://ai-wardrobe-buddy.preview.emergentagent.com"
        
        self.api_url = f"{self.base_url}/api"
        self.headers = {"Content-Type": "application/json"}
        self.test_results = []
        self.auth_token = None
        self.user_id = None
        
        print(f"🔧 Outfit Generation Tester initialized")
        print(f"   API URL: {self.api_url}")
        print(f"🎯 Focus: Testing outfit generation system to debug 'no outfits yet' issue")
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def create_sample_base64_image(self, color="blue"):
        """Create a simple base64 encoded image for testing"""
        # Create a minimal 1x1 pixel PNG in base64
        if color == "blue":
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA60e6kgAAAABJRU5ErkJggg=="
        elif color == "red":
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        else:
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA60e6kgAAAABJRU5ErkJggg=="
    
    async def setup_test_user(self):
        """Create and authenticate a test user for outfit testing"""
        try:
            # Register test user
            register_data = {
                "email": f"outfittest_{int(datetime.now().timestamp())}@example.com",
                "password": "TestPassword123!",
                "name": "Outfit Test User"
            }
            
            response = requests.post(f"{self.api_url}/auth/register", 
                                   json=register_data, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                self.headers["Authorization"] = f"Bearer {self.auth_token}"
                
                # Complete onboarding
                onboarding_data = {
                    "age": 28,
                    "profession": "Software Engineer",
                    "body_shape": "Athletic",
                    "skin_tone": "Medium",
                    "style_inspiration": ["Minimalist", "Professional"],
                    "style_vibes": ["Clean", "Modern"],
                    "style_message": "I love clean, professional looks",
                    "city": "Bangalore,IN"
                }
                
                onboard_response = requests.put(f"{self.api_url}/auth/onboarding",
                                              json=onboarding_data, headers=self.headers, timeout=10)
                
                if onboard_response.status_code == 200:
                    self.log_test("User Setup for Outfit Testing", "PASS", 
                                f"Created user: {register_data['email']}")
                    return True
                else:
                    self.log_test("User Setup for Outfit Testing", "FAIL", 
                                f"Onboarding failed: {onboard_response.status_code}")
                    return False
            else:
                self.log_test("User Setup for Outfit Testing", "FAIL", 
                            f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("User Setup for Outfit Testing", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def add_wardrobe_item(self, item_description: str):
        """Add a wardrobe item and analyze AI categorization"""
        try:
            item_data = {
                "image_base64": self.create_sample_base64_image()
            }
            
            response = requests.post(f"{self.api_url}/wardrobe", 
                                   json=item_data, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"Add Wardrobe Item ({item_description})", "PASS", 
                            f"Added: {data.get('message', 'Item added')}")
                return True
            else:
                self.log_test(f"Add Wardrobe Item ({item_description})", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test(f"Add Wardrobe Item ({item_description})", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def get_wardrobe_analysis(self):
        """Get wardrobe items and analyze categorization"""
        try:
            response = requests.get(f"{self.api_url}/wardrobe", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Analyze categorization
                categories = {}
                colors = {}
                fabric_types = {}
                
                for item in items:
                    category = item.get("category", "Unknown")
                    color = item.get("color", "Unknown")
                    fabric = item.get("fabric_type", "Unknown")
                    
                    categories[category] = categories.get(category, 0) + 1
                    colors[color] = colors.get(color, 0) + 1
                    fabric_types[fabric] = fabric_types.get(fabric, 0) + 1
                
                category_analysis = ", ".join([f"{cat}: {count}" for cat, count in categories.items()])
                
                self.log_test("Wardrobe Categorization Analysis", "PASS", 
                            f"Found {len(items)} items. Categories: {category_analysis}")
                
                # Log detailed analysis for debugging
                print(f"   📊 CATEGORIZATION ANALYSIS:")
                print(f"      Categories: {dict(categories)}")
                print(f"      Colors: {dict(colors)}")
                print(f"      Fabrics: {dict(fabric_types)}")
                
                # Check for category specificity
                broad_categories = ["Tops", "Bottoms", "Clothing"]
                specific_categories = ["T-shirts", "Shirts", "Pants", "Jeans", "Jackets", "Dresses"]
                
                broad_count = sum(categories.get(cat, 0) for cat in broad_categories)
                specific_count = sum(categories.get(cat, 0) for cat in specific_categories)
                
                if specific_count > broad_count:
                    self.log_test("Category Specificity Check", "PASS", 
                                f"AI using specific categories ({specific_count} specific vs {broad_count} broad)")
                else:
                    self.log_test("Category Specificity Check", "WARN", 
                                f"AI using broad categories ({broad_count} broad vs {specific_count} specific)")
                
                return items
            else:
                self.log_test("Wardrobe Categorization Analysis", "FAIL", 
                            f"Status: {response.status_code}")
                return []
                
        except Exception as e:
            self.log_test("Wardrobe Categorization Analysis", "FAIL", f"Exception: {str(e)}")
            return []
    
    async def test_outfit_generation_insufficient_items(self):
        """Test outfit generation with insufficient items (< 2)"""
        try:
            response = requests.get(f"{self.api_url}/wardrobe/outfits", 
                                  headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                outfits = data.get("outfits", [])
                message = data.get("message", "")
                
                print(f"   🔍 DEBUG - Insufficient items response:")
                print(f"      Outfits count: {len(outfits)}")
                print(f"      Message: {message}")
                
                if len(outfits) == 0 and "at least 2 items" in message.lower():
                    self.log_test("Outfit Generation (Insufficient Items)", "PASS", 
                                f"Correctly handled insufficient items: {message}")
                    return True
                else:
                    self.log_test("Outfit Generation (Insufficient Items)", "FAIL", 
                                f"Unexpected response: {len(outfits)} outfits, message: {message}")
                    return False
            else:
                self.log_test("Outfit Generation (Insufficient Items)", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Outfit Generation (Insufficient Items)", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def test_outfit_generation_sufficient_items(self, expected_items_count):
        """Test outfit generation with sufficient items"""
        try:
            print(f"   🧪 Testing outfit generation with {expected_items_count} wardrobe items...")
            
            response = requests.get(f"{self.api_url}/wardrobe/outfits?force_regenerate=true", 
                                  headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                outfits = data.get("outfits", [])
                message = data.get("message", "")
                
                print(f"   🔍 DEBUG - Outfit generation response:")
                print(f"      Number of outfits: {len(outfits)}")
                print(f"      Message: {message}")
                print(f"      Raw response keys: {list(data.keys())}")
                
                if len(outfits) > 0:
                    self.log_test(f"Outfit Generation ({expected_items_count} items)", "PASS", 
                                f"Generated {len(outfits)} outfits successfully")
                    
                    # Analyze outfit details
                    for i, outfit in enumerate(outfits[:3], 1):
                        occasion = outfit.get("occasion", "Unknown")
                        items_count = len(outfit.get("items", []))
                        explanation = outfit.get("explanation", "No explanation")
                        print(f"      👗 Outfit {i}: {occasion} ({items_count} items) - {explanation}")
                    
                    return True
                else:
                    # This is the critical issue we're investigating
                    self.log_test(f"Outfit Generation ({expected_items_count} items)", "FAIL", 
                                f"🚨 CRITICAL: No outfits generated despite {expected_items_count} items. Message: {message}")
                    
                    # Check for specific error patterns
                    if "error" in message.lower():
                        print(f"      🚨 ERROR DETECTED in message: {message}")
                    
                    return False
            else:
                self.log_test(f"Outfit Generation ({expected_items_count} items)", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text[:300]}")
                return False
                
        except Exception as e:
            self.log_test(f"Outfit Generation ({expected_items_count} items)", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def test_openai_integration(self):
        """Test OpenAI integration for outfit generation"""
        try:
            # Test chat endpoint to verify OpenAI connectivity
            chat_data = {"message": "Hello, can you help me with outfit suggestions?"}
            response = requests.post(f"{self.api_url}/chat", 
                                   json=chat_data, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                if messages and len(messages) > 0:
                    self.log_test("OpenAI Integration Check", "PASS", 
                                "OpenAI API responding correctly for chat")
                    return True
                else:
                    self.log_test("OpenAI Integration Check", "FAIL", 
                                "OpenAI API not responding with expected format")
                    return False
            else:
                self.log_test("OpenAI Integration Check", "FAIL", 
                            f"Chat endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OpenAI Integration Check", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def test_document_size_issue(self):
        """Test for MongoDB document size issues that might cause outfit generation to fail"""
        try:
            print(f"   🔍 Testing for document size issues...")
            
            # Get current user profile to check document size
            response = requests.get(f"{self.api_url}/auth/me", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                # Try to estimate document size by checking wardrobe
                wardrobe_response = requests.get(f"{self.api_url}/wardrobe", headers=self.headers, timeout=10)
                
                if wardrobe_response.status_code == 200:
                    wardrobe_data = wardrobe_response.json()
                    items = wardrobe_data.get("items", [])
                    
                    # Calculate approximate size
                    total_base64_size = 0
                    for item in items:
                        base64_data = item.get("image_base64", "")
                        total_base64_size += len(base64_data)
                    
                    # MongoDB has a 16MB document limit
                    size_mb = total_base64_size / (1024 * 1024)
                    
                    print(f"      📏 Wardrobe data size: ~{size_mb:.2f} MB")
                    print(f"      📦 Number of items: {len(items)}")
                    
                    if size_mb > 15:  # Close to 16MB limit
                        self.log_test("Document Size Check", "FAIL", 
                                    f"🚨 CRITICAL: Wardrobe data too large ({size_mb:.2f}MB). This likely causes outfit generation to fail!")
                        return False
                    elif size_mb > 10:
                        self.log_test("Document Size Check", "WARN", 
                                    f"Wardrobe data getting large ({size_mb:.2f}MB). May cause issues soon.")
                        return True
                    else:
                        self.log_test("Document Size Check", "PASS", 
                                    f"Wardrobe data size acceptable ({size_mb:.2f}MB)")
                        return True
                else:
                    self.log_test("Document Size Check", "FAIL", 
                                f"Could not get wardrobe data: {wardrobe_response.status_code}")
                    return False
            else:
                self.log_test("Document Size Check", "FAIL", 
                            f"Could not get user profile: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Document Size Check", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def test_json_parsing_errors(self):
        """Test for JSON parsing errors in outfit generation"""
        try:
            print(f"   🔍 Testing for JSON parsing errors...")
            
            # Try outfit generation and look for parsing issues
            response = requests.get(f"{self.api_url}/wardrobe/outfits?force_regenerate=true", 
                                  headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.log_test("JSON Parsing Check", "PASS", 
                                "Outfit generation API returns valid JSON")
                    
                    # Check if the response structure is correct
                    if "outfits" in data:
                        outfits = data["outfits"]
                        if isinstance(outfits, list):
                            self.log_test("Response Structure Check", "PASS", 
                                        f"Outfits field is properly formatted list with {len(outfits)} items")
                        else:
                            self.log_test("Response Structure Check", "FAIL", 
                                        f"Outfits field is not a list: {type(outfits)}")
                    else:
                        self.log_test("Response Structure Check", "FAIL", 
                                    "Response missing 'outfits' field")
                    
                    return True
                except json.JSONDecodeError as e:
                    self.log_test("JSON Parsing Check", "FAIL", 
                                f"🚨 JSON parsing error: {str(e)}")
                    return False
            else:
                self.log_test("JSON Parsing Check", "FAIL", 
                            f"API returned non-200 status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("JSON Parsing Check", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def run_comprehensive_outfit_tests(self):
        """Run comprehensive outfit generation tests to debug 'no outfits yet' issue"""
        print("🧪 Starting Comprehensive Outfit Generation Debugging")
        print("=" * 70)
        print("🎯 Goal: Identify why users are seeing 'no outfits yet'")
        print("=" * 70)
        
        # Step 1: Setup
        if not await self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return False
        
        # Step 2: Test OpenAI integration
        print(f"\n🤖 Testing OpenAI Integration...")
        await self.test_openai_integration()
        
        # Step 3: Test with no items (should show appropriate message)
        print(f"\n📋 Testing with empty wardrobe...")
        await self.test_outfit_generation_insufficient_items()
        
        # Step 4: Add one item and test (should still show insufficient message)
        print(f"\n📋 Testing with 1 item...")
        await self.add_wardrobe_item("Blue Cotton T-shirt")
        await self.test_outfit_generation_insufficient_items()
        
        # Step 5: Add second item and test (critical test)
        print(f"\n📋 Testing with 2 items (minimum requirement)...")
        await self.add_wardrobe_item("Black Denim Jeans")
        wardrobe_items = await self.get_wardrobe_analysis()
        
        if len(wardrobe_items) >= 2:
            await self.test_document_size_issue()
            await self.test_json_parsing_errors()
            await self.test_outfit_generation_sufficient_items(2)
        
        # Step 6: Test with more items
        print(f"\n📋 Testing with 5 items...")
        await self.add_wardrobe_item("White Button Shirt")
        await self.add_wardrobe_item("Navy Blazer")
        await self.add_wardrobe_item("Brown Leather Shoes")
        
        final_wardrobe = await self.get_wardrobe_analysis()
        if len(final_wardrobe) >= 5:
            await self.test_document_size_issue()
            await self.test_outfit_generation_sufficient_items(5)
        
        # Step 7: Test with even more items to trigger document size issues
        print(f"\n📋 Testing with 8+ items (potential document size issues)...")
        await self.add_wardrobe_item("Red Summer Dress")
        await self.add_wardrobe_item("Gray Wool Sweater")
        await self.add_wardrobe_item("Black Formal Pants")
        
        large_wardrobe = await self.get_wardrobe_analysis()
        if len(large_wardrobe) >= 8:
            await self.test_document_size_issue()
            await self.test_outfit_generation_sufficient_items(8)
        
        # Step 8: Summary and diagnosis
        self.print_diagnostic_summary()
        
        return True
    
    def print_diagnostic_summary(self):
        """Print comprehensive diagnostic summary focused on outfit generation issues"""
        print("\n" + "=" * 70)
        print("🔍 OUTFIT GENERATION DIAGNOSTIC SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        warned_tests = len([r for r in self.test_results if r["status"] == "WARN"])
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Warnings: {warned_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Analyze specific outfit generation issues
        outfit_tests = [r for r in self.test_results if "Outfit Generation" in r["test"]]
        outfit_failures = [r for r in outfit_tests if r["status"] == "FAIL"]
        
        print(f"\n🎯 OUTFIT GENERATION ANALYSIS:")
        print(f"   Total outfit tests: {len(outfit_tests)}")
        print(f"   Failed outfit tests: {len(outfit_failures)}")
        
        if len(outfit_failures) > 0:
            print(f"\n🚨 CRITICAL OUTFIT GENERATION ISSUES:")
            for failure in outfit_failures:
                print(f"   • {failure['test']}: {failure['details']}")
        
        # Check for specific issue patterns
        document_size_issues = [r for r in self.test_results if "Document Size" in r["test"] and r["status"] == "FAIL"]
        json_issues = [r for r in self.test_results if "JSON" in r["test"] and r["status"] == "FAIL"]
        openai_issues = [r for r in self.test_results if "OpenAI" in r["test"] and r["status"] == "FAIL"]
        
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        
        if document_size_issues:
            print(f"   🚨 DOCUMENT SIZE ISSUE DETECTED:")
            for issue in document_size_issues:
                print(f"      • {issue['details']}")
            print(f"      💡 SOLUTION: Reduce image sizes or store images separately")
        
        if json_issues:
            print(f"   🚨 JSON PARSING ISSUES DETECTED:")
            for issue in json_issues:
                print(f"      • {issue['details']}")
            print(f"      💡 SOLUTION: Fix OpenAI response parsing logic")
        
        if openai_issues:
            print(f"   🚨 OPENAI INTEGRATION ISSUES DETECTED:")
            for issue in openai_issues:
                print(f"      • {issue['details']}")
            print(f"      💡 SOLUTION: Check API keys and rate limits")
        
        # Check categorization issues
        categorization_issues = [r for r in self.test_results if "Category" in r["test"] and r["status"] == "WARN"]
        if categorization_issues:
            print(f"   ⚠️  CATEGORIZATION ISSUES:")
            for issue in categorization_issues:
                print(f"      • {issue['details']}")
            print(f"      💡 SUGGESTION: Improve AI prompts for more specific categories")
        
        print(f"\n📋 RECOMMENDATIONS:")
        
        if len(outfit_failures) == 0:
            print(f"   ✅ Outfit generation appears to be working correctly")
        else:
            print(f"   🔧 IMMEDIATE ACTIONS NEEDED:")
            if document_size_issues:
                print(f"      1. 🚨 CRITICAL: Fix MongoDB document size limit issue")
                print(f"         - Store images in separate collection or external storage")
                print(f"         - Compress base64 images before storing")
            if json_issues:
                print(f"      2. Fix JSON parsing in outfit generation endpoint")
            if openai_issues:
                print(f"      3. Verify OpenAI API configuration and limits")
            
            print(f"   🔍 FURTHER INVESTIGATION:")
            print(f"      - Check backend logs for 'DocumentTooLarge' errors")
            print(f"      - Monitor MongoDB document sizes")
            print(f"      - Test with smaller/compressed images")
        
        print("\n" + "=" * 70)

async def main():
    """Main test execution for outfit generation debugging"""
    print("🚀 Starting Outfit Generation Debugging Tests...")
    print("🎯 Focus: Identifying why users see 'no outfits yet'")
    print("=" * 70)
    
    tester = OutfitGenerationTester()
    
    try:
        await tester.run_comprehensive_outfit_tests()
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())