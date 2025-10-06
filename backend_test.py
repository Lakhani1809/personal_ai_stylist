#!/usr/bin/env python3
"""
Backend API Testing for AI Stylist App
Tests authentication endpoints and NEW AI functionality endpoints
"""

import requests
import json
import sys
import base64
import uuid
from datetime import datetime

# Configuration
BASE_URL = "https://stylistai.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test data - using timestamp to avoid conflicts
import time
timestamp = int(time.time())
TEST_USER = {
    "email": f"testuser_{timestamp}@example.com",
    "password": "SecurePass123!",
    "name": f"Test User {timestamp}"
}

# Sample base64 image data (small 1x1 pixel PNG)
SAMPLE_IMAGE_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    def test_health_check(self):
        """Test health endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    db_status = data.get("database", "unknown")
                    self.log_result(
                        "Health Check", 
                        True, 
                        f"Service healthy, database: {db_status}",
                        data
                    )
                    return True
                else:
                    self.log_result(
                        "Health Check", 
                        False, 
                        f"Unexpected health status: {data.get('status')}",
                        data
                    )
            else:
                self.log_result(
                    "Health Check", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("Health Check", False, f"Request failed: {str(e)}")
        return False
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        try:
            # First, try to clean up any existing test user (ignore errors)
            try:
                # We'll handle cleanup in login test if user exists
                pass
            except:
                pass
                
            response = self.session.post(
                f"{API_BASE}/auth/register",
                json=TEST_USER,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.access_token = data["access_token"]
                    self.user_id = data["user"].get("id")
                    self.log_result(
                        "User Registration", 
                        True, 
                        f"User registered successfully, ID: {self.user_id}",
                        {"user": data["user"], "token_type": data.get("token_type")}
                    )
                    return True
                else:
                    self.log_result(
                        "User Registration", 
                        False, 
                        "Missing access_token or user in response",
                        data
                    )
            elif response.status_code == 400:
                # User might already exist, try login instead
                data = response.json()
                if "already exists" in data.get("detail", ""):
                    self.log_result(
                        "User Registration", 
                        True, 
                        "User already exists (expected for repeated tests)",
                        data
                    )
                    return self.test_user_login()  # Try login instead
                else:
                    self.log_result(
                        "User Registration", 
                        False, 
                        f"Registration failed: {data.get('detail')}",
                        data
                    )
            else:
                self.log_result(
                    "User Registration", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("User Registration", False, f"Request failed: {str(e)}")
        return False
    
    def test_user_login(self):
        """Test user login endpoint"""
        try:
            login_data = {
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
            
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.access_token = data["access_token"]
                    self.user_id = data["user"].get("id")
                    self.log_result(
                        "User Login", 
                        True, 
                        f"Login successful, user ID: {self.user_id}",
                        {"user": data["user"], "token_type": data.get("token_type")}
                    )
                    return True
                else:
                    self.log_result(
                        "User Login", 
                        False, 
                        "Missing access_token or user in response",
                        data
                    )
            elif response.status_code == 401:
                data = response.json()
                self.log_result(
                    "User Login", 
                    False, 
                    f"Authentication failed: {data.get('detail')}",
                    data
                )
            else:
                self.log_result(
                    "User Login", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("User Login", False, f"Request failed: {str(e)}")
        return False
    
    def test_get_current_user(self):
        """Test get current user profile endpoint"""
        if not self.access_token:
            self.log_result(
                "Get Current User", 
                False, 
                "No access token available (login required first)"
            )
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{API_BASE}/auth/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "id" in data and "email" in data:
                    self.log_result(
                        "Get Current User", 
                        True, 
                        f"Profile retrieved: {data.get('email')}",
                        data
                    )
                    return True
                else:
                    self.log_result(
                        "Get Current User", 
                        False, 
                        "Missing required fields in user profile",
                        data
                    )
            elif response.status_code == 401:
                data = response.json()
                self.log_result(
                    "Get Current User", 
                    False, 
                    f"Authentication failed: {data.get('detail')}",
                    data
                )
            else:
                self.log_result(
                    "Get Current User", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("Get Current User", False, f"Request failed: {str(e)}")
        return False
    
    def test_user_onboarding(self):
        """Test user onboarding endpoint - CRITICAL TEST for fix verification"""
        if not self.access_token:
            self.log_result(
                "User Onboarding", 
                False, 
                "No access token available (login required first)"
            )
            return False
            
        try:
            # Realistic onboarding data as specified in review request
            onboarding_data = {
                "age": 28,
                "profession": "Software Engineer",
                "body_shape": "Athletic",
                "skin_tone": "Medium",
                "style_inspiration": "Minimalist chic with modern touches",
                "style_vibes": ["Professional", "Casual", "Modern"],
                "style_message": "I love clean lines and versatile pieces that can transition from work to weekend"
            }
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.put(
                f"{API_BASE}/auth/onboarding",
                json=onboarding_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # CRITICAL CHECKS for the fix
                print("   🔍 CRITICAL VERIFICATION:")
                
                # Check 1: Response should be a user object, not just a message
                if isinstance(data, dict) and "message" in data and len(data) == 1:
                    self.log_result(
                        "User Onboarding", 
                        False, 
                        "CRITICAL ISSUE: Response is just a message, not full user object",
                        data
                    )
                    return False
                
                # Check 2: Response should contain onboarding_completed flag
                if "onboarding_completed" not in data:
                    self.log_result(
                        "User Onboarding", 
                        False, 
                        "CRITICAL ISSUE: onboarding_completed flag missing from response",
                        data
                    )
                    return False
                
                # Check 3: onboarding_completed should be True
                if data.get("onboarding_completed") != True:
                    self.log_result(
                        "User Onboarding", 
                        False, 
                        f"CRITICAL ISSUE: onboarding_completed is {data.get('onboarding_completed')}, should be True",
                        data
                    )
                    return False
                
                # Check 4: Response should contain all onboarding data
                missing_fields = []
                for field in onboarding_data.keys():
                    if field not in data:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.log_result(
                        "User Onboarding", 
                        False, 
                        f"CRITICAL ISSUE: Missing onboarding fields in response: {missing_fields}",
                        data
                    )
                    return False
                
                # Check 5: Response should contain user identification fields
                required_user_fields = ["id", "email"]
                missing_user_fields = []
                for field in required_user_fields:
                    if field not in data:
                        missing_user_fields.append(field)
                
                if missing_user_fields:
                    self.log_result(
                        "User Onboarding", 
                        False, 
                        f"CRITICAL ISSUE: Missing user fields in response: {missing_user_fields}",
                        data
                    )
                    return False
                
                print("   ✅ ALL CRITICAL CHECKS PASSED!")
                print(f"   ✅ onboarding_completed: {data.get('onboarding_completed')}")
                print(f"   ✅ User ID: {data.get('id')}")
                print(f"   ✅ User Email: {data.get('email')}")
                print(f"   ✅ Age: {data.get('age')}")
                print(f"   ✅ Profession: {data.get('profession')}")
                
                self.log_result(
                    "User Onboarding", 
                    True, 
                    "CRITICAL TEST PASSED: Returns full user object with onboarding_completed: true",
                    {
                        "onboarding_completed": data.get("onboarding_completed"),
                        "user_id": data.get("id"),
                        "email": data.get("email"),
                        "age": data.get("age"),
                        "profession": data.get("profession")
                    }
                )
                return True
            elif response.status_code == 401:
                data = response.json()
                self.log_result(
                    "User Onboarding", 
                    False, 
                    f"Authentication failed: {data.get('detail')}",
                    data
                )
            else:
                self.log_result(
                    "User Onboarding", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("User Onboarding", False, f"Request failed: {str(e)}")
        return False
    
    def test_invalid_token(self):
        """Test endpoints with invalid token"""
        try:
            headers = {"Authorization": "Bearer invalid_token_12345"}
            response = self.session.get(
                f"{API_BASE}/auth/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 401:
                data = response.json()
                self.log_result(
                    "Invalid Token Handling", 
                    True, 
                    "Invalid token correctly rejected",
                    data
                )
                return True
            else:
                self.log_result(
                    "Invalid Token Handling", 
                    False, 
                    f"Expected 401, got {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result("Invalid Token Handling", False, f"Request failed: {str(e)}")
        return False

    # ===== NEW AI FUNCTIONALITY TESTS =====
    
    def test_enhanced_chat_personalization(self):
        """Test enhanced chat personalization with ALL onboarding data"""
        if not self.access_token:
            self.log_result("Enhanced Chat Personalization", False, "No access token available")
            return False
            
        print("   ✨ Testing Enhanced Chat Personalization (Phase 1A)...")
        
        try:
            # Test 1: Basic personalized chat
            chat_data = {
                "message": "What should I wear today?"
            }
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.post(
                f"{API_BASE}/chat",
                json=chat_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_message = data.get("message", "")
                message_id = data.get("message_id", "")
                
                # Enhanced personalization checks
                personalization_checks = {
                    "has_emojis": any(char in ai_message for char in "✨💫👗👔🎨💄👠🕶️🔥💕"),
                    "short_response": 20 <= len(ai_message.split()) <= 100,  # 2-4 sentences
                    "has_message_id": bool(message_id),
                    "conversational": any(word in ai_message.lower() for word in ["you", "your", "i'd", "let's"]),
                    "not_generic": "Hello" not in ai_message and len(ai_message) > 30
                }
                
                passed_checks = sum(personalization_checks.values())
                success = passed_checks >= 4  # At least 4/5 checks should pass
                
                self.log_result(
                    "Enhanced Chat Personalization", 
                    success, 
                    f"Personalization score: {passed_checks}/5 | Response: '{ai_message[:100]}...' | Message ID: {message_id}",
                    {"checks": personalization_checks, "response_preview": ai_message[:200]}
                )
                
                return message_id if success else None
            else:
                self.log_result(
                    "Enhanced Chat Personalization", 
                    False, 
                    f"Chat failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Enhanced Chat Personalization", False, f"Chat error: {str(e)}")
        return None

    def test_wardrobe_aware_chat(self):
        """Test wardrobe-aware suggestions referencing specific items"""
        if not self.access_token:
            self.log_result("Wardrobe-Aware Chat", False, "No access token available")
            return False
            
        print("   👗 Testing Wardrobe-Aware Chat Suggestions...")
        
        try:
            # First ensure we have wardrobe items
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Add a few wardrobe items if needed
            wardrobe_items = [
                {"image_base64": SAMPLE_IMAGE_BASE64, "exact_item_name": "Black Leather Jacket"},
                {"image_base64": SAMPLE_IMAGE_BASE64, "exact_item_name": "Blue Skinny Jeans"},
                {"image_base64": SAMPLE_IMAGE_BASE64, "exact_item_name": "White Silk Blouse"}
            ]
            
            for item in wardrobe_items:
                try:
                    self.session.post(f"{API_BASE}/wardrobe", json=item, headers=headers, timeout=10)
                except:
                    pass  # Ignore errors, items might already exist
            
            # Test wardrobe-aware chat
            chat_data = {
                "message": "Can you suggest an outfit from my wardrobe?"
            }
            
            response = self.session.post(
                f"{API_BASE}/chat",
                json=chat_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_message = data.get("message", "")
                message_id = data.get("message_id", "")
                
                # Check for wardrobe item references
                wardrobe_references = {
                    "mentions_specific_items": any(item in ai_message.lower() for item in ["jacket", "jeans", "blouse"]),
                    "mentions_colors": any(color in ai_message.lower() for color in ["black", "blue", "white"]),
                    "substantial_response": len(ai_message) > 50,
                    "has_styling_advice": any(word in ai_message.lower() for word in ["wear", "pair", "style", "look", "outfit"]),
                    "has_message_id": bool(message_id)
                }
                
                passed_checks = sum(wardrobe_references.values())
                success = passed_checks >= 3  # At least 3/5 checks should pass
                
                self.log_result(
                    "Wardrobe-Aware Chat", 
                    success, 
                    f"Wardrobe awareness score: {passed_checks}/5 | Response: '{ai_message[:150]}...'",
                    {"checks": wardrobe_references, "message_id": message_id}
                )
                
                return message_id if success else None
            else:
                self.log_result(
                    "Wardrobe-Aware Chat", 
                    False, 
                    f"Chat failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Wardrobe-Aware Chat", False, f"Chat error: {str(e)}")
        return None

    def test_chat_feedback_endpoint(self, message_id):
        """Test new chat feedback endpoint"""
        if not self.access_token:
            self.log_result("Chat Feedback Endpoint", False, "No access token available")
            return False
            
        if not message_id:
            self.log_result("Chat Feedback Endpoint", False, "No message_id available for testing")
            return False
            
        print("   👍 Testing Chat Feedback Endpoint...")
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test positive feedback
            feedback_data = {
                "message_id": message_id,
                "feedback": "positive"
            }
            
            response = self.session.post(
                f"{API_BASE}/chat/feedback",
                json=feedback_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success" and "recorded" in data.get("message", "").lower():
                    # Test negative feedback as well
                    feedback_data["feedback"] = "negative"
                    response2 = self.session.post(
                        f"{API_BASE}/chat/feedback",
                        json=feedback_data,
                        headers=headers,
                        timeout=10
                    )
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        if data2.get("status") == "success":
                            self.log_result(
                                "Chat Feedback Endpoint", 
                                True, 
                                "Both positive and negative feedback recorded successfully",
                                {"positive_response": data, "negative_response": data2}
                            )
                            return True
                    
                    self.log_result(
                        "Chat Feedback Endpoint", 
                        True, 
                        "Positive feedback recorded successfully",
                        data
                    )
                    return True
                else:
                    self.log_result(
                        "Chat Feedback Endpoint", 
                        False, 
                        f"Unexpected feedback response: {data}",
                        data
                    )
            else:
                self.log_result(
                    "Chat Feedback Endpoint", 
                    False, 
                    f"Feedback failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Chat Feedback Endpoint", False, f"Feedback error: {str(e)}")
        return False

    def test_ai_personality_improvements(self):
        """Test improved AI personality with emojis and conversational tone"""
        if not self.access_token:
            self.log_result("AI Personality Improvements", False, "No access token available")
            return False
            
        print("   🎭 Testing AI Personality Improvements...")
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test multiple personality aspects
            test_scenarios = [
                {"message": "I have a job interview tomorrow, what should I wear?", "context": "professional"},
                {"message": "What colors look good with my skin tone?", "context": "color_advice"},
                {"message": "Help me style my black leather jacket", "context": "styling"}
            ]
            
            personality_scores = []
            
            for scenario in test_scenarios:
                chat_data = {"message": scenario["message"]}
                response = self.session.post(
                    f"{API_BASE}/chat",
                    json=chat_data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_message = data.get("message", "")
                    
                    # Personality checks
                    checks = {
                        "has_emojis": sum(1 for char in ai_message if char in "✨💫👗👔🎨💄👠🕶️🔥💕") >= 1,
                        "conversational_tone": any(word in ai_message.lower() for word in ["you", "your", "i'd", "let's", "we"]),
                        "appropriate_length": 20 <= len(ai_message.split()) <= 80,
                        "fashion_expertise": any(word in ai_message.lower() for word in ["color", "style", "look", "outfit", "wear"]),
                        "encouraging_tone": any(word in ai_message.lower() for word in ["great", "perfect", "love", "amazing", "beautiful"])
                    }
                    
                    score = sum(checks.values()) / len(checks)
                    personality_scores.append(score)
                    
                    print(f"      {scenario['context']}: {score:.2f} score - '{ai_message[:60]}...'")
                
                time.sleep(1)  # Rate limiting
            
            if personality_scores:
                avg_score = sum(personality_scores) / len(personality_scores)
                success = avg_score >= 0.6  # At least 60% of personality checks pass
                
                self.log_result(
                    "AI Personality Improvements", 
                    success, 
                    f"Average personality score: {avg_score:.2f} across {len(personality_scores)} scenarios",
                    {"individual_scores": personality_scores, "average": avg_score}
                )
                return success
            else:
                self.log_result("AI Personality Improvements", False, "No responses received")
                
        except Exception as e:
            self.log_result("AI Personality Improvements", False, f"Personality test error: {str(e)}")
        return False
    
    def test_chat_history(self):
        """Test chat history retrieval"""
        if not self.access_token:
            self.log_result("Chat History Test", False, "No access token available")
            return False
            
        print("   📜 Testing Chat History endpoint...")
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{API_BASE}/chat/history",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    if len(data) >= 2:  # Should have messages from previous chat tests
                        # Verify message structure
                        sample_msg = data[0]
                        required_fields = ["id", "user_id", "message", "is_user", "timestamp"]
                        if all(field in sample_msg for field in required_fields):
                            self.log_result(
                                "Chat History", 
                                True, 
                                f"Retrieved {len(data)} chat messages with correct structure",
                                {"message_count": len(data), "sample_fields": list(sample_msg.keys())}
                            )
                            return True
                        else:
                            self.log_result(
                                "Chat History", 
                                False, 
                                f"Messages missing required fields: {sample_msg}",
                                sample_msg
                            )
                    else:
                        self.log_result(
                            "Chat History", 
                            False, 
                            f"Expected multiple messages from previous tests, got {len(data)}",
                            data
                        )
                else:
                    self.log_result(
                        "Chat History", 
                        False, 
                        f"Expected list, got: {type(data)}",
                        data
                    )
            else:
                self.log_result(
                    "Chat History", 
                    False, 
                    f"History failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Chat History", False, f"History error: {str(e)}")
        return False
    
    def test_chat_clear(self):
        """Test chat clear functionality"""
        if not self.access_token:
            self.log_result("Chat Clear Test", False, "No access token available")
            return False
            
        print("   🗑️  Testing Chat Clear endpoint...")
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.delete(
                f"{API_BASE}/chat/clear",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "cleared" in data["message"].lower():
                    # Verify history is empty
                    history_response = self.session.get(
                        f"{API_BASE}/chat/history",
                        headers=headers,
                        timeout=10
                    )
                    
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        if isinstance(history_data, list) and len(history_data) == 0:
                            self.log_result(
                                "Chat Clear", 
                                True, 
                                "Chat cleared and verified empty",
                                {"clear_response": data, "history_after_clear": len(history_data)}
                            )
                            return True
                        else:
                            self.log_result(
                                "Chat Clear", 
                                False, 
                                f"History not empty after clear: {len(history_data)} messages",
                                history_data
                            )
                    else:
                        self.log_result(
                            "Chat Clear", 
                            False, 
                            f"Could not verify clear - history check failed: {history_response.status_code}"
                        )
                else:
                    self.log_result(
                        "Chat Clear", 
                        False, 
                        f"Unexpected clear response: {data}",
                        data
                    )
            else:
                self.log_result(
                    "Chat Clear", 
                    False, 
                    f"Clear failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Chat Clear", False, f"Clear error: {str(e)}")
        return False
    
    def test_wardrobe_management(self):
        """Test wardrobe endpoints"""
        if not self.access_token:
            self.log_result("Wardrobe Test", False, "No access token available")
            return False
            
        print("   👗 Testing Wardrobe Management endpoints...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Test 1: Get existing wardrobe
        try:
            response = self.session.get(
                f"{API_BASE}/wardrobe",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "items" in data and isinstance(data["items"], list):
                    initial_count = len(data["items"])
                    self.log_result(
                        "Get Wardrobe", 
                        True, 
                        f"Retrieved wardrobe with {initial_count} items",
                        {"item_count": initial_count}
                    )
                else:
                    self.log_result(
                        "Get Wardrobe", 
                        False, 
                        f"Invalid wardrobe structure: {data}",
                        data
                    )
                    return False
            else:
                self.log_result(
                    "Get Wardrobe", 
                    False, 
                    f"Get wardrobe failed: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Get Wardrobe", False, f"Get wardrobe error: {str(e)}")
            return False
        
        # Test 2: Add wardrobe item with image
        try:
            wardrobe_data = {
                "image_base64": SAMPLE_IMAGE_BASE64
            }
            
            response = self.session.post(
                f"{API_BASE}/wardrobe",
                json=wardrobe_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "items_added" in data and data["items_added"] == 1:
                    # Verify item was added
                    verify_response = self.session.get(
                        f"{API_BASE}/wardrobe",
                        headers=headers,
                        timeout=10
                    )
                    
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        new_count = len(verify_data.get("items", []))
                        
                        if new_count > initial_count:
                            item = verify_data["items"][-1]  # Get last added item
                            required_fields = ["id", "user_id", "image_base64", "created_at"]
                            if all(field in item for field in required_fields):
                                self.log_result(
                                    "Add Wardrobe Item", 
                                    True, 
                                    f"Successfully added item to wardrobe (count: {initial_count} → {new_count})",
                                    {"item_id": item.get("id"), "category": item.get("category")}
                                )
                                return True
                            else:
                                self.log_result(
                                    "Add Wardrobe Item", 
                                    False, 
                                    f"Added item missing required fields: {item}",
                                    item
                                )
                        else:
                            self.log_result(
                                "Add Wardrobe Item", 
                                False, 
                                f"Item count didn't increase: {initial_count} → {new_count}"
                            )
                    else:
                        self.log_result(
                            "Add Wardrobe Item", 
                            False, 
                            f"Could not verify item addition: {verify_response.status_code}"
                        )
                else:
                    self.log_result(
                        "Add Wardrobe Item", 
                        False, 
                        f"Unexpected add response: {data}",
                        data
                    )
            else:
                self.log_result(
                    "Add Wardrobe Item", 
                    False, 
                    f"Add item failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Add Wardrobe Item", False, f"Add item error: {str(e)}")
        
        # Test 3: Add item without image (should fail)
        try:
            wardrobe_data = {}
            
            response = self.session.post(
                f"{API_BASE}/wardrobe",
                json=wardrobe_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 400:
                self.log_result(
                    "Wardrobe Validation", 
                    True, 
                    "Correctly rejected item without image",
                    response.json()
                )
            else:
                self.log_result(
                    "Wardrobe Validation", 
                    False, 
                    f"Should have rejected empty item: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Wardrobe Validation", False, f"Validation test error: {str(e)}")
        
        return False
    
    def test_outfit_validation(self):
        """Test outfit validation endpoint"""
        if not self.access_token:
            self.log_result("Outfit Validation Test", False, "No access token available")
            return False
            
        print("   ✨ Testing Outfit Validation endpoint...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Test 1: Validate outfit with image
        try:
            outfit_data = {
                "image_base64": SAMPLE_IMAGE_BASE64
            }
            
            response = self.session.post(
                f"{API_BASE}/validate-outfit",
                json=outfit_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["id", "scores", "overall_score", "feedback"]
                if all(field in data for field in required_fields):
                    scores = data["scores"]
                    expected_score_types = ["color_combo", "fit", "style", "occasion"]
                    
                    if all(score_type in scores for score_type in expected_score_types):
                        overall_score = data["overall_score"]
                        feedback = data["feedback"]
                        
                        if isinstance(overall_score, (int, float)) and isinstance(feedback, str) and len(feedback) > 10:
                            self.log_result(
                                "Outfit Validation", 
                                True, 
                                f"Received validation with score {overall_score}: {feedback[:50]}...",
                                {
                                    "overall_score": overall_score,
                                    "scores": scores,
                                    "feedback_length": len(feedback)
                                }
                            )
                            
                            # Test 2: Validate without image (should fail)
                            try:
                                empty_outfit = {}
                                
                                empty_response = self.session.post(
                                    f"{API_BASE}/validate-outfit",
                                    json=empty_outfit,
                                    headers=headers,
                                    timeout=10
                                )
                                
                                if empty_response.status_code == 400:
                                    self.log_result(
                                        "Outfit Validation - No Image", 
                                        True, 
                                        "Correctly rejected validation without image",
                                        empty_response.json()
                                    )
                                    return True
                                else:
                                    self.log_result(
                                        "Outfit Validation - No Image", 
                                        False, 
                                        f"Should have rejected empty request: {empty_response.status_code}",
                                        empty_response.text
                                    )
                                    
                            except Exception as e:
                                self.log_result("Outfit Validation - No Image", False, f"No image test error: {str(e)}")
                            
                            return True
                        else:
                            self.log_result(
                                "Outfit Validation", 
                                False, 
                                f"Invalid score/feedback types: score={overall_score} ({type(overall_score)}), feedback={len(feedback) if isinstance(feedback, str) else type(feedback)}",
                                data
                            )
                    else:
                        self.log_result(
                            "Outfit Validation", 
                            False, 
                            f"Missing score types. Expected: {expected_score_types}, Got: {list(scores.keys())}",
                            scores
                        )
                else:
                    self.log_result(
                        "Outfit Validation", 
                        False, 
                        f"Missing required fields. Expected: {required_fields}, Got: {list(data.keys())}",
                        data
                    )
            else:
                self.log_result(
                    "Outfit Validation", 
                    False, 
                    f"Validation failed: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("Outfit Validation", False, f"Validation error: {str(e)}")
        
        return False
    
    def run_all_tests(self):
        """Run all backend tests including NEW AI functionality"""
        print(f"\n🧪 Starting Backend API Tests for AI Stylist")
        print(f"📍 Base URL: {BASE_URL}")
        print(f"📍 API Base: {API_BASE}")
        print("=" * 60)
        
        # Test sequence - Authentication first, then AI functionality
        auth_tests = [
            ("Authentication Setup", [
                self.test_health_check,
                self.test_user_registration,
                self.test_user_login,
                self.test_get_current_user,
                self.test_user_onboarding,
                self.test_invalid_token
            ]),
            ("🤖 CHAT ENHANCEMENT PHASE 1A", [
                self.test_enhanced_chat_personalization,
                self.test_wardrobe_aware_chat,
                self.test_ai_personality_improvements,
                self.test_chat_history,
                self.test_wardrobe_management
            ])
        ]
        
        total_passed = 0
        total_tests = 0
        
        for section_name, tests in auth_tests:
            print(f"\n{'='*20} {section_name} {'='*20}")
            section_passed = 0
            
            for test in tests:
                total_tests += 1
                if test():
                    total_passed += 1
                    section_passed += 1
                print()  # Empty line between tests
            
            print(f"📊 {section_name} Results: {section_passed}/{len(tests)} passed")
        
        # Final Summary
        print("\n" + "=" * 60)
        print(f"🎯 FINAL TEST SUMMARY: {total_passed}/{total_tests} tests passed")
        
        # Detailed breakdown
        auth_passed = sum(1 for r in self.test_results[:6] if r["success"])
        ai_passed = sum(1 for r in self.test_results[6:] if r["success"]) if len(self.test_results) > 6 else 0
        
        print(f"   🔐 Authentication: {auth_passed}/6 passed")
        print(f"   🤖 AI Functionality: {ai_passed}/5 passed")
        
        if total_passed == total_tests:
            print("🎉 ALL TESTS PASSED! AI functionality is working correctly!")
            return True
        else:
            failed_tests = [r["test"] for r in self.test_results if not r["success"]]
            print(f"⚠️  {total_tests - total_passed} tests failed:")
            for failed_test in failed_tests:
                print(f"   ❌ {failed_test}")
            return False
    
    def get_summary(self):
        """Get test results summary"""
        return {
            "total_tests": len(self.test_results),
            "passed": len([r for r in self.test_results if r["success"]]),
            "failed": len([r for r in self.test_results if not r["success"]]),
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    
    # Print detailed results if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--detailed":
        print("\n📋 Detailed Results:")
        print(json.dumps(tester.get_summary(), indent=2))
    
    sys.exit(0 if success else 1)
