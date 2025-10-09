#!/usr/bin/env python3
"""
Phase 2 Specific Backend Tests for Manual Outfit Builder
Testing specific Phase 2 features and data integrity
"""

import requests
import json
import uuid
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://smart-stylist-15.preview.emergentagent.com/api"

class Phase2Tester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def setup_user(self):
        """Setup test user"""
        try:
            # Register user
            timestamp = int(datetime.now().timestamp())
            test_email = f"phase2_test_{timestamp}@example.com"
            
            response = requests.post(f"{BASE_URL}/auth/register", json={
                "email": test_email,
                "password": "TestPass123!",
                "name": "Phase2 Test User"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                self.log_test("Phase 2 User Setup", True, f"User created: {test_email}")
                return True
            else:
                self.log_test("Phase 2 User Setup", False, f"Registration failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Phase 2 User Setup", False, f"Exception: {str(e)}")
            return False
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def test_phase2_data_structure(self):
        """Test that saved outfits have the correct Phase 2 data structure"""
        try:
            # Save outfit with complete Phase 2 structure
            today = datetime.now()
            test_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            
            phase2_outfit = {
                "date": test_date,
                "occasion": "Business Meeting",
                "event_name": "Q1 Planning Session",
                "items": {
                    "top": str(uuid.uuid4()),
                    "bottom": str(uuid.uuid4()),
                    "layering": str(uuid.uuid4()),
                    "shoes": str(uuid.uuid4())
                }
            }
            
            # Save the outfit
            response = requests.post(
                f"{BASE_URL}/planner/outfit",
                json=phase2_outfit,
                headers=self.get_headers()
            )
            
            if response.status_code != 200:
                self.log_test("Phase 2 Data Structure", False, f"Failed to save outfit: {response.status_code}")
                return False
            
            # Retrieve and verify structure
            response = requests.get(
                f"{BASE_URL}/planner/outfits",
                params={"start_date": test_date, "end_date": test_date},
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                outfits = data.get("planned_outfits", [])
                
                if len(outfits) > 0:
                    outfit = outfits[0]
                    
                    # Check required Phase 2 fields
                    required_fields = ["date", "occasion", "event_name", "items", "user_id"]
                    missing_fields = [field for field in required_fields if field not in outfit]
                    
                    if not missing_fields:
                        # Check items structure
                        items = outfit.get("items", {})
                        expected_categories = ["top", "bottom", "layering", "shoes"]
                        
                        items_check = all(category in items for category in expected_categories)
                        
                        if items_check:
                            self.log_test("Phase 2 Data Structure", True, "Complete Phase 2 data structure verified")
                            return True
                        else:
                            self.log_test("Phase 2 Data Structure", False, f"Items structure incomplete: {items}")
                            return False
                    else:
                        self.log_test("Phase 2 Data Structure", False, f"Missing fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Phase 2 Data Structure", False, "No outfits retrieved")
                    return False
            else:
                self.log_test("Phase 2 Data Structure", False, f"Failed to retrieve: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Phase 2 Data Structure", False, f"Exception: {str(e)}")
            return False
    
    def test_week_range_queries(self):
        """Test week-based date range queries for Phase 2 calendar integration"""
        try:
            # Create outfits for a full week
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())  # Monday
            
            week_dates = []
            for i in range(7):  # Full week
                date = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
                week_dates.append(date)
                
                outfit_data = {
                    "date": date,
                    "occasion": f"Day {i+1} Activity",
                    "event_name": f"Week Event {i+1}",
                    "items": {
                        "top": f"top_item_{i}",
                        "bottom": f"bottom_item_{i}"
                    }
                }
                
                response = requests.post(
                    f"{BASE_URL}/planner/outfit",
                    json=outfit_data,
                    headers=self.get_headers()
                )
                
                if response.status_code != 200:
                    self.log_test("Week Range Setup", False, f"Failed to create outfit for {date}")
                    return False
            
            # Query the full week
            start_date = week_dates[0]
            end_date = week_dates[-1]
            
            response = requests.get(
                f"{BASE_URL}/planner/outfits",
                params={"start_date": start_date, "end_date": end_date},
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                outfits = data.get("planned_outfits", [])
                
                if len(outfits) == 7:
                    self.log_test("Week Range Queries", True, f"Successfully retrieved full week ({len(outfits)} outfits)")
                    return True
                else:
                    self.log_test("Week Range Queries", False, f"Expected 7 outfits, got {len(outfits)}")
                    return False
            else:
                self.log_test("Week Range Queries", False, f"Query failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Week Range Queries", False, f"Exception: {str(e)}")
            return False
    
    def test_outfit_replacement_cycle(self):
        """Test multiple outfit save/retrieve/delete cycle for Phase 2"""
        try:
            test_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
            
            # Cycle 1: Save initial outfit
            outfit1 = {
                "date": test_date,
                "occasion": "Work",
                "event_name": "Team Meeting",
                "items": {"top": "shirt1", "bottom": "pants1"}
            }
            
            response = requests.post(f"{BASE_URL}/planner/outfit", json=outfit1, headers=self.get_headers())
            if response.status_code != 200:
                self.log_test("Outfit Replacement Cycle", False, "Failed to save initial outfit")
                return False
            
            # Cycle 2: Replace with different outfit
            outfit2 = {
                "date": test_date,
                "occasion": "Casual",
                "event_name": "Coffee Date",
                "items": {"top": "tshirt1", "bottom": "jeans1", "shoes": "sneakers1"}
            }
            
            response = requests.post(f"{BASE_URL}/planner/outfit", json=outfit2, headers=self.get_headers())
            if response.status_code != 200:
                self.log_test("Outfit Replacement Cycle", False, "Failed to replace outfit")
                return False
            
            # Verify replacement
            response = requests.get(
                f"{BASE_URL}/planner/outfits",
                params={"start_date": test_date, "end_date": test_date},
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                outfits = data.get("planned_outfits", [])
                
                if len(outfits) == 1 and outfits[0]["occasion"] == "Casual":
                    # Cycle 3: Delete the outfit
                    response = requests.delete(f"{BASE_URL}/planner/outfit/{test_date}", headers=self.get_headers())
                    
                    if response.status_code == 200:
                        # Verify deletion
                        response = requests.get(
                            f"{BASE_URL}/planner/outfits",
                            params={"start_date": test_date, "end_date": test_date},
                            headers=self.get_headers()
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            outfits = data.get("planned_outfits", [])
                            
                            if len(outfits) == 0:
                                self.log_test("Outfit Replacement Cycle", True, "Complete save/replace/delete cycle successful")
                                return True
                            else:
                                self.log_test("Outfit Replacement Cycle", False, "Outfit not properly deleted")
                                return False
                        else:
                            self.log_test("Outfit Replacement Cycle", False, "Failed to verify deletion")
                            return False
                    else:
                        self.log_test("Outfit Replacement Cycle", False, "Failed to delete outfit")
                        return False
                else:
                    self.log_test("Outfit Replacement Cycle", False, "Outfit not properly replaced")
                    return False
            else:
                self.log_test("Outfit Replacement Cycle", False, "Failed to verify replacement")
                return False
                
        except Exception as e:
            self.log_test("Outfit Replacement Cycle", False, f"Exception: {str(e)}")
            return False
    
    def test_item_id_mapping(self):
        """Test that items field correctly maps wardrobe item IDs"""
        try:
            # Create outfit with realistic item IDs
            test_date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
            
            # Use UUID format item IDs (as would come from wardrobe)
            item_ids = {
                "top": str(uuid.uuid4()),
                "bottom": str(uuid.uuid4()),
                "layering": str(uuid.uuid4()),
                "shoes": str(uuid.uuid4())
            }
            
            outfit_data = {
                "date": test_date,
                "occasion": "Date Night",
                "event_name": "Anniversary Dinner",
                "items": item_ids
            }
            
            # Save outfit
            response = requests.post(f"{BASE_URL}/planner/outfit", json=outfit_data, headers=self.get_headers())
            
            if response.status_code != 200:
                self.log_test("Item ID Mapping", False, f"Failed to save outfit: {response.status_code}")
                return False
            
            # Retrieve and verify item IDs are preserved
            response = requests.get(
                f"{BASE_URL}/planner/outfits",
                params={"start_date": test_date, "end_date": test_date},
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                outfits = data.get("planned_outfits", [])
                
                if len(outfits) > 0:
                    retrieved_items = outfits[0].get("items", {})
                    
                    # Check that all item IDs are preserved
                    ids_match = all(
                        retrieved_items.get(category) == item_id
                        for category, item_id in item_ids.items()
                    )
                    
                    if ids_match:
                        self.log_test("Item ID Mapping", True, "Wardrobe item IDs correctly preserved")
                        return True
                    else:
                        self.log_test("Item ID Mapping", False, f"Item IDs not preserved. Expected: {item_ids}, Got: {retrieved_items}")
                        return False
                else:
                    self.log_test("Item ID Mapping", False, "No outfits retrieved")
                    return False
            else:
                self.log_test("Item ID Mapping", False, f"Failed to retrieve outfit: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Item ID Mapping", False, f"Exception: {str(e)}")
            return False
    
    def run_phase2_tests(self):
        """Run all Phase 2 specific tests"""
        print("🧪 Starting Phase 2 Manual Outfit Builder Specific Tests")
        print("=" * 65)
        
        if not self.setup_user():
            print("❌ Cannot proceed without user setup")
            return False
        
        # Run Phase 2 specific tests
        self.test_phase2_data_structure()
        self.test_week_range_queries()
        self.test_outfit_replacement_cycle()
        self.test_item_id_mapping()
        
        # Summary
        print("\n" + "=" * 65)
        print("📊 PHASE 2 TEST SUMMARY")
        print("=" * 65)
        
        total = len(self.test_results)
        passed = sum(1 for result in self.test_results if result["success"])
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Phase 2 Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed > 0:
            print("\n🚨 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        return success_rate >= 90

if __name__ == "__main__":
    tester = Phase2Tester()
    success = tester.run_phase2_tests()
    
    if success:
        print("\n🎉 Phase 2 backend functionality is working excellently!")
    else:
        print("\n⚠️ Phase 2 backend has some issues that need attention.")