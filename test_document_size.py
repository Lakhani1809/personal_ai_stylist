#!/usr/bin/env python3
"""
Test to reproduce the DocumentTooLarge error in outfit generation
"""

import requests
import json
import time
import base64

def create_large_base64_image(size_kb=100):
    """Create a larger base64 image to increase document size"""
    # Create a larger PNG-like base64 string
    base_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA60e6kgAAAABJRU5ErkJggg=="
    # Repeat to make it larger
    multiplier = (size_kb * 1024) // len(base_data)
    large_data = base_data * multiplier
    return f"data:image/png;base64,{large_data}"

def test_document_size_limit():
    api_url = 'https://smart-stylist-15.preview.emergentagent.com/api'
    
    # Register a new user
    register_data = {
        'email': f'docsize_test_{int(time.time())}@test.com',
        'password': 'test123',
        'name': 'Document Size Test User'
    }
    
    response = requests.post(f'{api_url}/auth/register', json=register_data)
    if response.status_code != 200:
        print(f"Registration failed: {response.status_code}")
        return
    
    data = response.json()
    token = data['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    print("Adding wardrobe items with large images...")
    
    # Add items with progressively larger images
    for i in range(20):  # Add many items
        # Create a large image (500KB each)
        large_image = create_large_base64_image(500)
        item_data = {'image_base64': large_image}
        
        print(f"Adding item {i+1} (size: ~500KB)...")
        add_resp = requests.post(f'{api_url}/wardrobe', json=item_data, headers=headers, timeout=30)
        
        if add_resp.status_code != 200:
            print(f"Failed to add item {i+1}: {add_resp.status_code}")
            print(f"Error: {add_resp.text[:200]}")
            break
        else:
            print(f"✅ Added item {i+1}")
        
        # Check wardrobe size after each addition
        wardrobe_resp = requests.get(f'{api_url}/wardrobe', headers=headers)
        if wardrobe_resp.status_code == 200:
            wardrobe_data = wardrobe_resp.json()
            items = wardrobe_data.get('items', [])
            
            # Calculate approximate size
            total_size = 0
            for item in items:
                total_size += len(item.get('image_base64', ''))
            size_mb = total_size / (1024 * 1024)
            
            print(f"   Current wardrobe size: {size_mb:.2f} MB ({len(items)} items)")
            
            # If we're getting close to 16MB limit, test outfit generation
            if size_mb > 10:  # Test when approaching limit
                print(f"🧪 Testing outfit generation at {size_mb:.2f} MB...")
                
                outfit_resp = requests.get(f'{api_url}/wardrobe/outfits?force_regenerate=true', 
                                         headers=headers, timeout=60)
                
                print(f"Outfit response status: {outfit_resp.status_code}")
                
                if outfit_resp.status_code == 200:
                    outfit_data = outfit_resp.json()
                    outfits = outfit_data.get('outfits', [])
                    message = outfit_data.get('message', '')
                    
                    print(f"Outfits generated: {len(outfits)}")
                    print(f"Message: '{message}'")
                    
                    if len(outfits) == 0:
                        print("🚨 DOCUMENT SIZE ISSUE REPRODUCED!")
                        print(f"   Wardrobe size: {size_mb:.2f} MB")
                        print(f"   Number of items: {len(items)}")
                        if message:
                            print(f"   Error message: {message}")
                        return True
                    else:
                        print(f"✅ Outfit generation still works at {size_mb:.2f} MB")
                else:
                    print(f"❌ Outfit generation API failed: {outfit_resp.status_code}")
                    print(f"Response: {outfit_resp.text[:300]}")
                    return True
            
            # Stop if we hit MongoDB's 16MB limit
            if size_mb > 15:
                print(f"⚠️ Approaching MongoDB 16MB document limit at {size_mb:.2f} MB")
                break
        
        time.sleep(0.5)  # Small delay between requests
    
    print("Test completed without reproducing the issue")
    return False

if __name__ == "__main__":
    print("🧪 Testing MongoDB Document Size Limit Issue")
    print("=" * 60)
    
    try:
        issue_reproduced = test_document_size_limit()
        if issue_reproduced:
            print("\n🎯 CONCLUSION: Document size limit issue confirmed!")
            print("💡 SOLUTION: Store images separately or compress them")
        else:
            print("\n✅ No document size issues detected in this test")
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()