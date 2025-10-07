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
    
    def create_sample_base64_image(self, size=(800, 1000), color=(100, 150, 200), quality=95):
        """Create a realistic test image for wardrobe testing"""
        try:
            # Create a test image with specified size and color
            img = Image.new('RGB', size, color)
            
            # Add some simple pattern to make it more realistic
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            
            # Add some rectangles to simulate clothing patterns
            for i in range(0, size[0], 100):
                for j in range(0, size[1], 100):
                    if (i + j) % 200 == 0:
                        draw.rectangle([i, j, i+50, j+50], fill=(color[0]+20, color[1]+20, color[2]+20))
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            img_data = buffer.getvalue()
            
            base64_string = base64.b64encode(img_data).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_string}"
            
        except Exception as e:
            print(f"Error creating test image: {e}")
            # Fallback to simple base64 image
            return "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A8A"
    
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
    
    async def test_image_compression_fix(self):
        """Test 1: Image Compression & Outfit Generation Fix"""
        print("\n🧪 Testing Image Compression & Outfit Generation Fix...")
        
        # Clear wardrobe first
        try:
            response = requests.delete(f"{self.api_url}/wardrobe/clear", headers=self.headers, timeout=10)
        except:
            pass
        
        # Test with large image to trigger compression
        large_image = self.create_sample_base64_image(size=(2000, 2500), quality=95)
        original_size_mb = len(large_image.split(',')[1]) * 0.75 / (1024 * 1024)
        
        print(f"   📏 Original image size: {original_size_mb:.2f} MB")
        
        item_data = {"image_base64": large_image}
        
        try:
            response = requests.post(f"{self.api_url}/wardrobe", json=item_data, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                self.log_test("Image Compression - Large Image Upload", "PASS", 
                            "Large image successfully uploaded and processed")
                
                # Check if image was compressed by getting wardrobe
                wardrobe_response = requests.get(f"{self.api_url}/wardrobe", headers=self.headers, timeout=10)
                if wardrobe_response.status_code == 200:
                    wardrobe = wardrobe_response.json()
                    items = wardrobe.get("items", [])
                    if items:
                        stored_image = items[-1].get("image_base64", "")
                        compressed_size_mb = len(stored_image) * 0.75 / (1024 * 1024)
                        compression_ratio = compressed_size_mb / original_size_mb * 100
                        
                        print(f"   📏 Compressed size: {compressed_size_mb:.2f} MB ({compression_ratio:.1f}% of original)")
                        
                        if compressed_size_mb < original_size_mb:
                            self.log_test("Image Compression - Verification", "PASS", 
                                        f"Image compressed from {original_size_mb:.2f}MB to {compressed_size_mb:.2f}MB")
                        else:
                            self.log_test("Image Compression - Verification", "FAIL", 
                                        "No compression detected")
                    else:
                        self.log_test("Image Compression - Verification", "FAIL", 
                                    "No items found in wardrobe after upload")
            else:
                self.log_test("Image Compression - Large Image Upload", "FAIL", 
                            f"Upload failed: {response.status_code}, {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Image Compression - Large Image Upload", "FAIL", f"Exception: {str(e)}")
    
    async def test_outfit_generation_guardrails(self):
        """Test 2: Enhanced Outfit Generation Guardrails"""
        print("\n🧪 Testing Enhanced Outfit Generation Guardrails...")
        
        # Clear wardrobe
        try:
            requests.delete(f"{self.api_url}/wardrobe/clear", headers=self.headers, timeout=10)
        except:
            pass
        
        # Test 0 items
        await self.test_guardrail_scenario(0, "Your wardrobe is empty!")
        
        # Test 1 item
        await self.add_wardrobe_item("Blue T-shirt")
        await self.test_guardrail_scenario(1, "Add more items to your wardrobe")
        
        # Test 2-3 items
        await self.add_wardrobe_item("Black Jeans")
        await self.test_guardrail_scenario(2, "You have 2 items. Add a few more")
        
        await self.add_wardrobe_item("White Shirt")
        await self.test_guardrail_scenario(3, "You have 3 items. Add a few more")
        
        # Test 4+ items (should generate outfits)
        await self.add_wardrobe_item("Navy Jacket")
        await self.test_guardrail_scenario(4, None, should_generate=True)
    
    async def test_guardrail_scenario(self, expected_count, expected_message, should_generate=False):
        """Test a specific guardrail scenario"""
        try:
            response = requests.get(f"{self.api_url}/wardrobe/outfits", headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                outfits = result.get("outfits", [])
                message = result.get("message", "")
                
                print(f"   📊 {expected_count} items: {len(outfits)} outfits, message: '{message}'")
                
                if should_generate:
                    if len(outfits) > 0:
                        self.log_test(f"Guardrail {expected_count} Items", "PASS", 
                                    f"Generated {len(outfits)} outfits as expected")
                    else:
                        self.log_test(f"Guardrail {expected_count} Items", "FAIL", 
                                    f"Expected outfits but got message: {message}")
                else:
                    if expected_message and expected_message.lower() in message.lower():
                        self.log_test(f"Guardrail {expected_count} Items", "PASS", 
                                    f"Correct message: {message}")
                    else:
                        self.log_test(f"Guardrail {expected_count} Items", "FAIL", 
                                    f"Expected '{expected_message}' but got: {message}")
            else:
                self.log_test(f"Guardrail {expected_count} Items", "FAIL", 
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test(f"Guardrail {expected_count} Items", "FAIL", f"Exception: {str(e)}")
    
    async def test_wardrobe_category_analysis(self):
        """Test 3: Wardrobe Category Analysis"""
        print("\n🧪 Testing Wardrobe Category Analysis...")
        
        # Clear wardrobe
        try:
            requests.delete(f"{self.api_url}/wardrobe/clear", headers=self.headers, timeout=10)
        except:
            pass
        
        # Add test items and analyze categorization
        test_items = [
            {"name": "Red T-shirt", "color": (200, 50, 50)},
            {"name": "Blue Jeans", "color": (50, 100, 150)},
            {"name": "Black Jacket", "color": (30, 30, 30)}
        ]
        
        for item in test_items:
            test_image = self.create_sample_base64_image(color=item["color"])
            item_data = {"image_base64": test_image}
            
            try:
                response = requests.post(f"{self.api_url}/wardrobe", json=item_data, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    print(f"   ✅ Added {item['name']}")
                else:
                    print(f"   ❌ Failed to add {item['name']}")
            except Exception as e:
                print(f"   ❌ Exception adding {item['name']}: {e}")
        
        # Analyze categorization
        await self.get_wardrobe_analysis()
    
    async def test_mongodb_document_size_fix(self):
        """Test 4: MongoDB DocumentTooLarge Fix"""
        print("\n🧪 Testing MongoDB DocumentTooLarge Fix...")
        
        # Clear wardrobe
        try:
            requests.delete(f"{self.api_url}/wardrobe/clear", headers=self.headers, timeout=10)
        except:
            pass
        
        # Add multiple large items to test document size limits
        print("   📦 Adding multiple large images to test document size limits...")
        
        for i in range(8):  # Add 8 large items
            large_image = self.create_sample_base64_image(size=(1500, 2000), quality=85)
            item_data = {"image_base64": large_image}
            
            try:
                response = requests.post(f"{self.api_url}/wardrobe", json=item_data, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    print(f"   ✅ Added large item {i+1}")
                else:
                    self.log_test("MongoDB Size Fix", "FAIL", 
                                f"Failed to add item {i+1}: {response.status_code}")
                    return
            except Exception as e:
                self.log_test("MongoDB Size Fix", "FAIL", 
                            f"Exception adding item {i+1}: {str(e)}")
                return
        
        print("   🧪 Testing outfit generation with large wardrobe...")
        
        # Test outfit generation (this previously failed due to document size)
        try:
            response = requests.get(f"{self.api_url}/wardrobe/outfits?force_regenerate=true", 
                                  headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                outfits = result.get("outfits", [])
                message = result.get("message", "")
                
                if len(outfits) > 0:
                    self.log_test("MongoDB Size Fix", "PASS", 
                                f"Successfully generated {len(outfits)} outfits with large wardrobe")
                    
                    # Test persistence
                    response2 = requests.get(f"{self.api_url}/wardrobe/outfits", headers=self.headers, timeout=15)
                    if response2.status_code == 200:
                        result2 = response2.json()
                        outfits2 = result2.get("outfits", [])
                        
                        if len(outfits2) == len(outfits):
                            self.log_test("Outfit Persistence", "PASS", 
                                        "Outfits successfully saved and retrieved from database")
                        else:
                            self.log_test("Outfit Persistence", "FAIL", 
                                        "Outfits not properly persisted")
                else:
                    self.log_test("MongoDB Size Fix", "FAIL", 
                                f"No outfits generated. Message: {message}")
            else:
                self.log_test("MongoDB Size Fix", "FAIL", 
                            f"Outfit generation failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("MongoDB Size Fix", "FAIL", 
                        f"Exception during outfit generation: {str(e)}")
    
    async def test_full_flow(self):
        """Test 5: Complete End-to-End Flow"""
        print("\n🧪 Testing Complete End-to-End Flow...")
        
        # Clear wardrobe
        try:
            requests.delete(f"{self.api_url}/wardrobe/clear", headers=self.headers, timeout=10)
        except:
            pass
        
        # Add diverse wardrobe items
        test_items = [
            {"name": "White T-shirt", "color": (255, 255, 255)},
            {"name": "Blue Jeans", "color": (50, 100, 150)},
            {"name": "Black Jacket", "color": (30, 30, 30)},
            {"name": "Red Dress", "color": (200, 50, 50)},
            {"name": "Brown Shoes", "color": (139, 69, 19)},
            {"name": "Green Shirt", "color": (50, 150, 50)}
        ]
        
        added_items = 0
        for item in test_items:
            test_image = self.create_sample_base64_image(color=item["color"])
            item_data = {"image_base64": test_image}
            
            try:
                response = requests.post(f"{self.api_url}/wardrobe", json=item_data, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    added_items += 1
                    print(f"   ✅ Added {item['name']}")
                else:
                    print(f"   ❌ Failed to add {item['name']}: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Exception adding {item['name']}: {e}")
        
        if added_items >= 4:
            self.log_test("Full Flow - Item Addition", "PASS", 
                        f"Successfully added {added_items} items")
            
            # Generate outfits
            try:
                response = requests.get(f"{self.api_url}/wardrobe/outfits", headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    outfits = result.get("outfits", [])
                    
                    if len(outfits) > 0:
                        self.log_test("Full Flow - Outfit Generation", "PASS", 
                                    f"Generated {len(outfits)} outfits")
                        
                        # Analyze outfit quality
                        for i, outfit in enumerate(outfits[:3]):
                            occasion = outfit.get("occasion", "Unknown")
                            items = outfit.get("items", [])
                            explanation = outfit.get("explanation", "")
                            
                            print(f"   👗 Outfit {i+1} ({occasion}): {len(items)} items - {explanation}")
                            
                            if len(items) >= 2:
                                self.log_test(f"Full Flow - Outfit {i+1} Quality", "PASS", 
                                            f"{occasion} outfit with {len(items)} items")
                            else:
                                self.log_test(f"Full Flow - Outfit {i+1} Quality", "FAIL", 
                                            f"Insufficient items in {occasion} outfit")
                    else:
                        message = result.get("message", "No message")
                        self.log_test("Full Flow - Outfit Generation", "FAIL", 
                                    f"No outfits generated: {message}")
                else:
                    self.log_test("Full Flow - Outfit Generation", "FAIL", 
                                f"Failed: {response.status_code}")
            except Exception as e:
                self.log_test("Full Flow - Outfit Generation", "FAIL", f"Exception: {str(e)}")
        else:
            self.log_test("Full Flow - Item Addition", "FAIL", 
                        f"Only added {added_items} items, need at least 4")

    async def run_wardrobe_fixes_tests(self):
        """Run all wardrobe fixes tests"""
        print("🧪 Starting Wardrobe Fixes Testing Suite")
        print("=" * 70)
        print("🎯 Testing: Image compression, outfit guardrails, category analysis")
        print("=" * 70)
        
        # Step 1: Setup
        if not await self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return False
        
        # Step 2: Test image compression fix
        await self.test_image_compression_fix()
        
        # Step 3: Test outfit generation guardrails
        await self.test_outfit_generation_guardrails()
        
        # Step 4: Test wardrobe category analysis
        await self.test_wardrobe_category_analysis()
        
        # Step 5: Test MongoDB document size fix
        await self.test_mongodb_document_size_fix()
        
        # Step 6: Test complete flow
        await self.test_full_flow()
        
        # Step 7: Summary
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
    """Main test execution for wardrobe fixes testing"""
    print("🚀 Starting Wardrobe Fixes Testing...")
    print("🎯 Focus: Testing image compression, outfit guardrails, and category analysis")
    print("=" * 70)
    
    tester = WardrobeFixesTester()
    
    try:
        await tester.run_wardrobe_fixes_tests()
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())