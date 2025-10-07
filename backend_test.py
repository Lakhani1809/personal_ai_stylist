#!/usr/bin/env python3
"""
Backend Testing Suite for AI Stylist Chat Improvements Round 2
Testing enhanced chat functionality with personal stylist improvements
"""

import requests
import json
import time
import re
import sys
from typing import Dict, List, Any

# Use the production URL from frontend/.env
BASE_URL = "https://ai-wardrobe-buddy.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

class ChatImprovementsTestSuite:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name: str, passed: bool, details: str):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def setup_test_user(self):
        """Create and authenticate a test user"""
        print("\n🔧 Setting up test user...")
        
        # Create unique test user
        timestamp = int(time.time())
        test_email = f"maya_test_{timestamp}@example.com"
        
        # Register user
        register_data = {
            "email": test_email,
            "password": "testpass123",
            "name": "Maya Test User"
        }
        
        try:
            response = requests.post(f"{API_BASE}/auth/register", json=register_data)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.user_id = data["user"]["id"]
                print(f"✅ Test user created: {test_email}")
                
                # Complete onboarding with detailed profile
                onboarding_data = {
                    "gender": "female",
                    "age": "28",
                    "profession": "Marketing Manager",
                    "body_shape": "hourglass",
                    "skin_tone": "medium",
                    "style_inspiration": ["Emma Stone", "Zendaya"],
                    "style_vibes": ["chic", "professional", "trendy"],
                    "style_message": "I love mixing classic pieces with modern trends",
                    "city": "New York"
                }
                
                headers = {"Authorization": f"Bearer {self.access_token}"}
                onboard_response = requests.put(f"{API_BASE}/auth/onboarding", 
                                              json=onboarding_data, headers=headers)
                
                if onboard_response.status_code == 200:
                    print("✅ Onboarding completed with detailed profile")
                    return True
                else:
                    print(f"❌ Onboarding failed: {onboard_response.status_code}")
                    return False
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Setup error: {str(e)}")
            return False
    
    def test_personal_stylist_tone(self):
        """Test 1: Personal Stylist Tone - Should be friendly, personal stylist (not wardrobe manager)"""
        print("\n🎭 Testing Personal Stylist Tone...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        message_data = {"message": "Hi Maya! I need help with my style"}
        
        try:
            response = requests.post(f"{API_BASE}/chat", json=message_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check new response format
                if "messages" in data and "message_ids" in data:
                    messages = data["messages"]
                    full_response = " ".join(messages).lower()
                    
                    # Check for personal stylist tone indicators
                    stylist_indicators = [
                        "stylist", "style", "help", "fashion", "outfit", "look"
                    ]
                    
                    # Check against wardrobe manager language (should NOT contain)
                    manager_phrases = [
                        "wardrobe manager", "let's chat about stylist outfits", 
                        "manage your wardrobe", "organize your clothes"
                    ]
                    
                    has_stylist_tone = any(indicator in full_response for indicator in stylist_indicators)
                    has_manager_tone = any(phrase in full_response for phrase in manager_phrases)
                    
                    # Check for friendly, conversational elements
                    friendly_indicators = ["!", "✨", "💕", "😊", "hey", "hi"]
                    is_friendly = any(indicator in full_response for indicator in friendly_indicators)
                    
                    if has_stylist_tone and not has_manager_tone and is_friendly:
                        self.log_result("Personal Stylist Tone", True, 
                                      f"Response shows personal stylist tone: '{' '.join(messages[:2])}'")
                    else:
                        self.log_result("Personal Stylist Tone", False, 
                                      f"Response lacks personal stylist tone or too manager-like: '{full_response[:100]}'")
                else:
                    self.log_result("Personal Stylist Tone", False, 
                                  f"Response format incorrect - missing 'messages' array: {data}")
            else:
                self.log_result("Personal Stylist Tone", False, 
                              f"API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Personal Stylist Tone", False, f"Exception: {str(e)}")
    
    def test_specific_recommendations(self):
        """Test 2: Hyper-Specific Recommendations - Must include exact colors, shoe types, accessories"""
        print("\n🎯 Testing Hyper-Specific Recommendations...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        message_data = {"message": "I want to create a casual outfit for weekend brunch"}
        
        try:
            response = requests.post(f"{API_BASE}/chat", json=message_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if "messages" in data:
                    messages = data["messages"]
                    full_response = " ".join(messages).lower()
                    
                    # Check for specific color mentions
                    specific_colors = [
                        "navy", "burgundy", "sage green", "tan", "camel", "white", 
                        "black", "brown", "beige", "olive", "cream", "charcoal"
                    ]
                    
                    # Check for specific shoe types
                    specific_shoes = [
                        "chelsea boots", "loafers", "sneakers", "ankle boots", 
                        "oxford", "ballet flats", "sandals", "heels"
                    ]
                    
                    # Check for specific accessories
                    specific_accessories = [
                        "leather strap", "silver watch", "minimalist", "crossbody", 
                        "tote", "clutch", "scarf", "belt"
                    ]
                    
                    # Check for vague terms (should NOT contain)
                    vague_terms = [
                        "nice shoes", "a watch", "some accessories", "good colors",
                        "appropriate footwear", "suitable accessories"
                    ]
                    
                    has_specific_colors = any(color in full_response for color in specific_colors)
                    has_specific_shoes = any(shoe in full_response for shoe in specific_shoes)
                    has_specific_accessories = any(acc in full_response for acc in specific_accessories)
                    has_vague_terms = any(term in full_response for term in vague_terms)
                    
                    specificity_score = sum([has_specific_colors, has_specific_shoes, has_specific_accessories])
                    
                    if specificity_score >= 2 and not has_vague_terms:
                        self.log_result("Hyper-Specific Recommendations", True, 
                                      f"Response contains specific details (score: {specificity_score}/3): '{full_response[:150]}'")
                    else:
                        self.log_result("Hyper-Specific Recommendations", False, 
                                      f"Response lacks specificity (score: {specificity_score}/3) or contains vague terms: '{full_response[:150]}'")
                else:
                    self.log_result("Hyper-Specific Recommendations", False, 
                                  f"Response format incorrect: {data}")
            else:
                self.log_result("Hyper-Specific Recommendations", False, 
                              f"API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Hyper-Specific Recommendations", False, f"Exception: {str(e)}")
    
    def test_message_chunking(self):
        """Test 3: Message Chunking - Responses should be split into 2-3 short messages"""
        print("\n📝 Testing Message Chunking...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        message_data = {"message": "What should I wear to a business meeting tomorrow?"}
        
        try:
            response = requests.post(f"{API_BASE}/chat", json=message_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ["messages", "message_ids", "total_chunks"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Message Chunking Format", False, 
                                  f"Missing required fields: {missing_fields}")
                    return
                
                messages = data["messages"]
                message_ids = data["message_ids"]
                total_chunks = data["total_chunks"]
                
                # Validate chunk count (should be 2-3)
                chunk_count_valid = 2 <= len(messages) <= 3
                
                # Validate each chunk length (15-25 words max, but allow some flexibility)
                chunk_lengths = [len(msg.split()) for msg in messages]
                chunks_proper_length = all(5 <= length <= 30 for length in chunk_lengths)
                
                # Validate arrays match
                arrays_match = len(messages) == len(message_ids) == total_chunks
                
                # Validate message IDs are UUIDs
                uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
                valid_ids = all(uuid_pattern.match(msg_id) for msg_id in message_ids)
                
                if chunk_count_valid and chunks_proper_length and arrays_match and valid_ids:
                    self.log_result("Message Chunking", True, 
                                  f"Proper chunking: {len(messages)} chunks, lengths: {chunk_lengths}, valid IDs")
                else:
                    issues = []
                    if not chunk_count_valid:
                        issues.append(f"chunk count: {len(messages)} (should be 2-3)")
                    if not chunks_proper_length:
                        issues.append(f"chunk lengths: {chunk_lengths} (should be 5-30 words)")
                    if not arrays_match:
                        issues.append(f"array mismatch: {len(messages)}, {len(message_ids)}, {total_chunks}")
                    if not valid_ids:
                        issues.append("invalid message IDs")
                    
                    self.log_result("Message Chunking", False, f"Issues: {', '.join(issues)}")
            else:
                self.log_result("Message Chunking", False, 
                              f"API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Message Chunking", False, f"Exception: {str(e)}")
    
    def test_backward_compatibility(self):
        """Test 4: Backward Compatibility - Verify existing endpoints still work"""
        print("\n🔄 Testing Backward Compatibility...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Test chat history endpoint
        try:
            history_response = requests.get(f"{API_BASE}/chat/history", headers=headers)
            
            if history_response.status_code == 200:
                history_data = history_response.json()
                if isinstance(history_data, list):
                    self.log_result("Chat History Compatibility", True, 
                                  f"Chat history working: {len(history_data)} messages")
                else:
                    self.log_result("Chat History Compatibility", False, 
                                  f"Unexpected history format: {type(history_data)}")
            else:
                self.log_result("Chat History Compatibility", False, 
                              f"History API error: {history_response.status_code}")
        except Exception as e:
            self.log_result("Chat History Compatibility", False, f"History exception: {str(e)}")
        
        # Test feedback endpoint (if we have message IDs from previous tests)
        try:
            # Send a test message first to get a message ID
            test_msg = {"message": "Test message for feedback"}
            chat_response = requests.post(f"{API_BASE}/chat", json=test_msg, headers=headers)
            
            if chat_response.status_code == 200:
                chat_data = chat_response.json()
                if "message_ids" in chat_data and chat_data["message_ids"]:
                    message_id = chat_data["message_ids"][0]
                    
                    # Test feedback
                    feedback_data = {
                        "message_id": message_id,
                        "feedback": "positive"
                    }
                    
                    feedback_response = requests.post(f"{API_BASE}/chat/feedback", 
                                                    json=feedback_data, headers=headers)
                    
                    if feedback_response.status_code == 200:
                        feedback_result = feedback_response.json()
                        if feedback_result.get("status") == "success":
                            self.log_result("Chat Feedback Compatibility", True, 
                                          "Feedback endpoint working correctly")
                        else:
                            self.log_result("Chat Feedback Compatibility", False, 
                                          f"Unexpected feedback response: {feedback_result}")
                    else:
                        self.log_result("Chat Feedback Compatibility", False, 
                                      f"Feedback API error: {feedback_response.status_code}")
                else:
                    self.log_result("Chat Feedback Compatibility", False, 
                                  "No message IDs available for feedback test")
            else:
                self.log_result("Chat Feedback Compatibility", False, 
                              "Could not send test message for feedback test")
                
        except Exception as e:
            self.log_result("Chat Feedback Compatibility", False, f"Feedback exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all chat improvement tests"""
        print("🚀 Starting Chat Improvements Round 2 Testing Suite")
        print("=" * 60)
        
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return False
        
        # Run all tests
        self.test_personal_stylist_tone()
        self.test_specific_recommendations()
        self.test_message_chunking()
        self.test_backward_compatibility()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = [r for r in self.test_results if r["passed"]]
        failed_tests = [r for r in self.test_results if not r["passed"]]
        
        print(f"✅ PASSED: {len(passed_tests)}")
        print(f"❌ FAILED: {len(failed_tests)}")
        
        if failed_tests:
            print("\n🔍 FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        return len(failed_tests) == 0

if __name__ == "__main__":
    test_suite = ChatImprovementsTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Chat improvements are working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please review the issues above.")
    
    sys.exit(0 if success else 1)