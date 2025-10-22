#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Chat Memory & Fashion Intelligence Enhancements
Testing the advanced memory system and deep fashion intelligence features
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
print(f"🎯 Focus: Chat Memory & Fashion Intelligence Enhancements")

class ChatMemoryIntelligenceTest:
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
        """Create and setup a test user with comprehensive profile"""
        print("\n🔧 Setting up test user with comprehensive profile...")
        
        # Register user
        register_data = {
            "email": f"maya_memory_test_{int(time.time())}@test.com",
            "password": "testpass123",
            "name": "Maya Memory Tester"
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
        
        # Complete comprehensive onboarding with all profile data
        onboarding_data = {
            "age": 28,
            "gender": "female",
            "profession": "Marketing Manager",
            "body_shape": "hourglass",
            "skin_tone": "warm",
            "style_inspiration": ["Minimalist", "Classic", "Modern"],
            "style_vibes": ["Professional", "Chic", "Versatile"],
            "style_message": "I love timeless pieces that can transition from work to weekend",
            "city": "New York,NY,US",
            "color_preferences": ["navy", "white", "beige", "burgundy"],
            "budget_range": "mid-range"
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.put(f"{self.base_url}/auth/onboarding", json=onboarding_data, headers=headers)
        
        if response.status_code == 200:
            self.log_test("Comprehensive Onboarding", True, "All profile data set")
            return True
        else:
            self.log_test("Comprehensive Onboarding", False, f"Status: {response.status_code}")
            return False
    
    def add_diverse_wardrobe(self):
        """Add diverse wardrobe items for memory and intelligence testing"""
        print("\n👗 Adding diverse wardrobe items...")
        
        # Sample base64 image (small test image)
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        wardrobe_items = [
            {"image_base64": test_image, "description": "Navy blazer"},
            {"image_base64": test_image, "description": "White silk blouse"},
            {"image_base64": test_image, "description": "Black wool trousers"},
            {"image_base64": test_image, "description": "Burgundy cashmere sweater"},
            {"image_base64": test_image, "description": "Beige trench coat"},
            {"image_base64": test_image, "description": "Dark wash jeans"}
        ]
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        added_items = 0
        
        for item in wardrobe_items:
            response = requests.post(f"{self.base_url}/wardrobe", json=item, headers=headers)
            if response.status_code == 200:
                added_items += 1
                time.sleep(0.5)  # Small delay between additions
        
        self.log_test("Diverse Wardrobe Addition", added_items >= 4, f"Added {added_items}/6 items")
        return added_items >= 4
    
    def create_planned_outfits(self):
        """Create planned outfits for outfit memory testing"""
        print("\n📅 Creating planned outfits for memory testing...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Create planned outfits for different dates
        planned_outfits = [
            {
                "date": "2024-01-15",
                "occasion": "work",
                "event_name": "Important client meeting at 9:00 AM",
                "items": {"top": "item1", "bottom": "item2", "layering": "item3"}
            },
            {
                "date": "2024-01-16", 
                "occasion": "date",
                "event_name": "Dinner date at 7:30 PM",
                "items": {"top": "item4", "bottom": "item5"}
            },
            {
                "date": "2024-01-17",
                "occasion": "casual",
                "event_name": "Weekend brunch with friends",
                "items": {"top": "item2", "bottom": "item6", "layering": "item5"}
            }
        ]
        
        created_outfits = 0
        for outfit in planned_outfits:
            response = requests.post(f"{self.base_url}/planner/outfit", json=outfit, headers=headers)
            if response.status_code == 200:
                created_outfits += 1
                time.sleep(0.3)
        
        self.log_test("Planned Outfits Creation", created_outfits >= 2, f"Created {created_outfits}/3 outfits")
        return created_outfits >= 2
    
    def create_conversation_history(self):
        """Create conversation history for memory testing"""
        print("\n💬 Creating conversation history for memory testing...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Create a series of conversations to build memory
        conversations = [
            "Hi Maya! I love wearing navy and white together, they're my favorite colors",
            "I have a work presentation tomorrow, what should I wear?",
            "I really liked that burgundy sweater suggestion you gave me last time",
            "Do you think red would look good with my warm skin tone?",
            "I'm going on a date this weekend, something casual but stylish",
            "I prefer minimalist styles over busy patterns",
            "What colors work best for professional settings?",
            "I love classic pieces that never go out of style",
            "Can you help me with outfit ideas for winter weather?",
            "I want to build a capsule wardrobe with versatile pieces"
        ]
        
        successful_chats = 0
        for i, message in enumerate(conversations):
            response = requests.post(f"{self.base_url}/chat", json={"message": message}, headers=headers)
            if response.status_code == 200:
                successful_chats += 1
                # Add some feedback to certain messages for learning
                if i in [1, 2, 4]:  # Add positive feedback to some responses
                    chat_data = response.json()
                    if "message_ids" in chat_data and chat_data["message_ids"]:
                        feedback_data = {
                            "message_id": chat_data["message_ids"][0],
                            "feedback": "positive"
                        }
                        requests.post(f"{self.base_url}/chat/feedback", json=feedback_data, headers=headers)
                
                time.sleep(0.5)  # Small delay between messages
        
        self.log_test("Conversation History Creation", successful_chats >= 8, f"Created {successful_chats}/10 conversations")
        return successful_chats >= 8
    
    def test_conversation_memory_retrieval(self):
        """Test that chat retrieves and uses conversation history"""
        print("\n🧠 Testing Conversation Memory Retrieval...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Ask about previous conversations
        test_message = "What colors did I mention I like in our previous conversations?"
        response = requests.post(f"{self.base_url}/chat", json={"message": test_message}, headers=headers)
        
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get("messages", [])
            full_response = " ".join(messages).lower()
            
            # Check if response references previous conversations
            memory_indicators = ["navy", "white", "burgundy", "previous", "mentioned", "talked about", "remember"]
            memory_found = any(indicator in full_response for indicator in memory_indicators)
            
            self.log_test("Conversation Memory Retrieval", memory_found, 
                         f"Response references previous conversations: {memory_found}")
            return memory_found
        else:
            self.log_test("Conversation Memory Retrieval", False, f"Status: {response.status_code}")
            return False
    
    def test_user_preference_learning(self):
        """Test user preference analysis from conversation patterns"""
        print("\n🎨 Testing User Preference Learning...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Ask about style preferences to see if AI learned from conversations
        test_message = "Based on our conversations, what do you think my style preferences are?"
        response = requests.post(f"{self.base_url}/chat", json={"message": test_message}, headers=headers)
        
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get("messages", [])
            full_response = " ".join(messages).lower()
            
            # Check if response shows learned preferences
            learned_preferences = ["minimalist", "classic", "navy", "white", "professional", "versatile", "timeless"]
            preferences_found = sum(1 for pref in learned_preferences if pref in full_response)
            
            success = preferences_found >= 3
            self.log_test("User Preference Learning", success, 
                         f"Found {preferences_found}/7 learned preferences in response")
            return success
        else:
            self.log_test("User Preference Learning", False, f"Status: {response.status_code}")
            return False
    
    def test_wardrobe_awareness(self):
        """Test wardrobe-aware suggestions with specific item references"""
        print("\n👔 Testing Wardrobe Awareness...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Ask for outfit suggestions using wardrobe items
        test_message = "Can you suggest an outfit using items from my wardrobe for a work meeting?"
        response = requests.post(f"{self.base_url}/chat", json={"message": test_message}, headers=headers)
        
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get("messages", [])
            full_response = " ".join(messages).lower()
            
            # Check if response references specific wardrobe items
            wardrobe_references = ["blazer", "blouse", "trousers", "sweater", "navy", "white", "black", "burgundy"]
            references_found = sum(1 for ref in wardrobe_references if ref in full_response)
            
            success = references_found >= 3
            self.log_test("Wardrobe Awareness", success, 
                         f"Found {references_found}/8 wardrobe references in response")
            return success
        else:
            self.log_test("Wardrobe Awareness", False, f"Status: {response.status_code}")
            return False
    
    def test_outfit_memory_integration(self):
        """Test outfit history memory from planned outfits"""
        print("\n📅 Testing Outfit Memory Integration...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Ask about recent outfit planning
        test_message = "What outfits have I planned recently? Any upcoming events?"
        response = requests.post(f"{self.base_url}/chat", json={"message": test_message}, headers=headers)
        
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get("messages", [])
            full_response = " ".join(messages).lower()
            
            # Check if response references planned outfits
            outfit_references = ["meeting", "date", "brunch", "planned", "upcoming", "client", "dinner"]
            references_found = sum(1 for ref in outfit_references if ref in full_response)
            
            success = references_found >= 2
            self.log_test("Outfit Memory Integration", success, 
                         f"Found {references_found}/7 outfit memory references")
            return success
        else:
            self.log_test("Outfit Memory Integration", False, f"Status: {response.status_code}")
            return False
    
    def test_color_theory_analysis(self):
        """Test advanced color theory analysis"""
        print("\n🎨 Testing Color Theory Analysis...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Ask about color combinations
        test_message = "What colors work well together in my wardrobe? Can you explain the color theory?"
        response = requests.post(f"{self.base_url}/chat", json={"message": test_message}, headers=headers)
        
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get("messages", [])
            full_response = " ".join(messages).lower()
            
            # Check for color theory concepts
            color_theory_terms = ["harmony", "complementary", "palette", "warm", "cool", "neutral", "theory", "coordination"]
            theory_found = sum(1 for term in color_theory_terms if term in full_response)
            
            success = theory_found >= 3
            self.log_test("Color Theory Analysis", success, 
                         f"Found {theory_found}/8 color theory concepts")
            return success
        else:
            self.log_test("Color Theory Analysis", False, f"Status: {response.status_code}")
            return False
    
    def test_body_type_styling(self):
        """Test body type styling expertise"""
        print("\n👤 Testing Body Type Styling...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Ask for body type specific advice
        test_message = "What styles work best for my body shape? Any specific fit recommendations?"
        response = requests.post(f"{self.base_url}/chat", json={"message": test_message}, headers=headers)
        
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get("messages", [])
            full_response = " ".join(messages).lower()
            
            # Check for body type styling advice
            body_styling_terms = ["hourglass", "waist", "fitted", "silhouette", "proportions", "shape", "flatter", "highlight"]
            styling_found = sum(1 for term in body_styling_terms if term in full_response)
            
            success = styling_found >= 3
            self.log_test("Body Type Styling", success, 
                         f"Found {styling_found}/8 body type styling terms")
            return success
        else:
            self.log_test("Body Type Styling", False, f"Status: {response.status_code}")
            return False
    
    def test_seasonal_advice(self):
        """Test seasonal fashion advice based on current date"""
        print("\n🍂 Testing Seasonal Advice...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Ask for seasonal advice
        test_message = "What should I wear for this time of year? Any seasonal styling tips?"
        response = requests.post(f"{self.base_url}/chat", json={"message": test_message}, headers=headers)
        
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get("messages", [])
            full_response = " ".join(messages).lower()
            
            # Check for seasonal advice (winter/spring/summer/fall terms)
            seasonal_terms = ["winter", "spring", "summer", "fall", "season", "weather", "layer", "fabric", "temperature"]
            seasonal_found = sum(1 for term in seasonal_terms if term in full_response)
            
            success = seasonal_found >= 2
            self.log_test("Seasonal Advice", success, 
                         f"Found {seasonal_found}/9 seasonal styling terms")
            return success
        else:
            self.log_test("Seasonal Advice", False, f"Status: {response.status_code}")
            return False
    
    def test_weather_integration(self):
        """Test weather-aware recommendations"""
        print("\n🌤️ Testing Weather Integration...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Ask about weather-appropriate clothing
        test_message = "What should I wear today based on the weather in New York?"
        response = requests.post(f"{self.base_url}/chat", json={"message": test_message}, headers=headers)
        
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get("messages", [])
            full_response = " ".join(messages).lower()
            
            # Check for weather-aware recommendations
            weather_terms = ["temperature", "weather", "degrees", "warm", "cold", "fabric", "layer", "condition"]
            weather_found = sum(1 for term in weather_terms if term in full_response)
            
            success = weather_found >= 2
            self.log_test("Weather Integration", success, 
                         f"Found {weather_found}/8 weather-aware terms")
            return success
        else:
            self.log_test("Weather Integration", False, f"Status: {response.status_code}")
            return False
    
    def test_care_maintenance_intelligence(self):
        """Test fabric care and maintenance intelligence"""
        print("\n🧽 Testing Care & Maintenance Intelligence...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Ask about fabric care
        test_message = "How should I care for my silk blouse and wool trousers? Any maintenance tips?"
        response = requests.post(f"{self.base_url}/chat", json={"message": test_message}, headers=headers)
        
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get("messages", [])
            full_response = " ".join(messages).lower()
            
            # Check for care instructions
            care_terms = ["care", "wash", "clean", "dry", "silk", "wool", "maintenance", "fabric", "gentle"]
            care_found = sum(1 for term in care_terms if term in full_response)
            
            success = care_found >= 4
            self.log_test("Care & Maintenance Intelligence", success, 
                         f"Found {care_found}/9 care-related terms")
            return success
        else:
            self.log_test("Care & Maintenance Intelligence", False, f"Status: {response.status_code}")
            return False
    
    def test_trend_intelligence(self):
        """Test fashion trend integration"""
        print("\n🔥 Testing Trend Intelligence...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Ask about current trends
        test_message = "What are the current fashion trends? How can I incorporate them into my style?"
        response = requests.post(f"{self.base_url}/chat", json={"message": test_message}, headers=headers)
        
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get("messages", [])
            full_response = " ".join(messages).lower()
            
            # Check for trend-related content
            trend_terms = ["trend", "current", "fashion", "style", "popular", "season", "modern", "contemporary"]
            trend_found = sum(1 for term in trend_terms if term in full_response)
            
            success = trend_found >= 3
            self.log_test("Trend Intelligence", success, 
                         f"Found {trend_found}/8 trend-related terms")
            return success
        else:
            self.log_test("Trend Intelligence", False, f"Status: {response.status_code}")
            return False
    
    def test_enhanced_system_prompt(self):
        """Test that enhanced system prompt includes all context types"""
        print("\n📝 Testing Enhanced System Prompt Integration...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Ask a comprehensive question that should trigger all context types
        test_message = "I need a complete style consultation. Consider my profile, wardrobe, recent conversations, planned outfits, current weather, and give me your best fashion advice with color theory and body type considerations."
        response = requests.post(f"{self.base_url}/chat", json={"message": test_message}, headers=headers)
        
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get("messages", [])
            full_response = " ".join(messages).lower()
            
            # Check for comprehensive context integration
            context_indicators = [
                "profile", "wardrobe", "hourglass", "warm", "professional", 
                "navy", "white", "weather", "temperature", "season"
            ]
            context_found = sum(1 for indicator in context_indicators if indicator in full_response)
            
            success = context_found >= 6
            self.log_test("Enhanced System Prompt Integration", success, 
                         f"Found {context_found}/10 context indicators")
            return success
        else:
            self.log_test("Enhanced System Prompt Integration", False, f"Status: {response.status_code}")
            return False
    
    def test_message_chunking_format(self):
        """Test that responses are properly chunked into short messages"""
        print("\n📱 Testing Message Chunking Format...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Ask a question that should generate multiple chunks
        test_message = "Give me detailed styling advice for three different occasions: work, date night, and casual weekend."
        response = requests.post(f"{self.base_url}/chat", json={"message": test_message}, headers=headers)
        
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get("messages", [])
            message_ids = chat_data.get("message_ids", [])
            total_chunks = chat_data.get("total_chunks", 0)
            
            # Check chunking format
            has_multiple_chunks = len(messages) >= 2
            has_message_ids = len(message_ids) == len(messages)
            has_total_chunks = total_chunks == len(messages)
            
            # Check message length (should be short, conversational)
            avg_length = sum(len(msg.split()) for msg in messages) / len(messages) if messages else 0
            appropriate_length = avg_length <= 30  # Max ~30 words per chunk
            
            success = has_multiple_chunks and has_message_ids and has_total_chunks and appropriate_length
            self.log_test("Message Chunking Format", success, 
                         f"Chunks: {len(messages)}, Avg words: {avg_length:.1f}")
            return success
        else:
            self.log_test("Message Chunking Format", False, f"Status: {response.status_code}")
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