#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Railway AI Fashion Segmentation Integration
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
    
    def run_comprehensive_tests(self):
        """Run all comprehensive memory and intelligence tests"""
        print("🚀 Starting Comprehensive Chat Memory & Fashion Intelligence Testing")
        print("=" * 80)
        
        # Setup phase
        if not self.setup_test_user():
            print("❌ Setup failed, aborting tests")
            return
        
        if not self.add_diverse_wardrobe():
            print("❌ Wardrobe setup failed, aborting tests")
            return
        
        if not self.create_planned_outfits():
            print("❌ Planned outfits setup failed, aborting tests")
            return
        
        if not self.create_conversation_history():
            print("❌ Conversation history setup failed, aborting tests")
            return
        
        # Wait for data to be processed
        print("\n⏳ Waiting for data processing...")
        time.sleep(2)
        
        # Memory System Tests
        print("\n" + "="*50)
        print("🧠 MEMORY SYSTEM TESTS")
        print("="*50)
        
        memory_tests = [
            self.test_conversation_memory_retrieval,
            self.test_user_preference_learning,
            self.test_wardrobe_awareness,
            self.test_outfit_memory_integration
        ]
        
        memory_passed = sum(test() for test in memory_tests)
        
        # Intelligence Features Tests
        print("\n" + "="*50)
        print("🎨 FASHION INTELLIGENCE TESTS")
        print("="*50)
        
        intelligence_tests = [
            self.test_color_theory_analysis,
            self.test_body_type_styling,
            self.test_seasonal_advice,
            self.test_care_maintenance_intelligence,
            self.test_trend_intelligence
        ]
        
        intelligence_passed = sum(test() for test in intelligence_tests)
        
        # Integration Tests
        print("\n" + "="*50)
        print("🔗 INTEGRATION TESTS")
        print("="*50)
        
        integration_tests = [
            self.test_weather_integration,
            self.test_enhanced_system_prompt,
            self.test_message_chunking_format
        ]
        
        integration_passed = sum(test() for test in integration_tests)
        
        # Summary
        total_tests = len(memory_tests) + len(intelligence_tests) + len(integration_tests)
        total_passed = memory_passed + intelligence_passed + integration_passed
        
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*80)
        print(f"🧠 Memory System Tests: {memory_passed}/{len(memory_tests)} passed")
        print(f"🎨 Fashion Intelligence Tests: {intelligence_passed}/{len(intelligence_tests)} passed")
        print(f"🔗 Integration Tests: {integration_passed}/{len(integration_tests)} passed")
        print(f"\n🎯 OVERALL SUCCESS RATE: {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)")
        
        if total_passed >= total_tests * 0.8:  # 80% success rate
            print("✅ COMPREHENSIVE TESTING PASSED - Memory & Intelligence features working excellently!")
        elif total_passed >= total_tests * 0.6:  # 60% success rate
            print("⚠️ PARTIAL SUCCESS - Most features working, some issues identified")
        else:
            print("❌ TESTING FAILED - Significant issues with memory and intelligence features")
        
        return total_passed, total_tests

def main():
    """Main test execution"""
    tester = ChatMemoryIntelligenceTest()
    passed, total = tester.run_comprehensive_tests()
    
    # Return appropriate exit code
    if passed >= total * 0.8:
        exit(0)  # Success
    else:
        exit(1)  # Failure

if __name__ == "__main__":
    main()