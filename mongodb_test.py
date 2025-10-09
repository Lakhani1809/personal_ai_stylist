#!/usr/bin/env python3
"""
Quick test for MongoDB document size fix
"""

import requests
import json
import base64
from PIL import Image
from io import BytesIO
import time

# Backend URL
API_BASE = "https://smart-stylist-15.preview.emergentagent.com/api"

def create_test_image(size=(1500, 2000), quality=85):
    """Create a large test image"""
    img = Image.new('RGB', size, (100, 150, 200))
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=True)
    img_data = buffer.getvalue()
    base64_string = base64.b64encode(img_data).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_string}"

def test_mongodb_fix():
    # Register user
    user_data = {
        "email": f"mongotest_{int(time.time())}@test.com",
        "password": "testpass123",
        "name": "MongoDB Tester"
    }
    
    response = requests.post(f"{API_BASE}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.status_code}")
        return
    
    data = response.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    
    print("✅ User registered successfully")
    
    # Add 6 large items
    print("📦 Adding 6 large images...")
    for i in range(6):
        large_image = create_test_image()
        item_data = {"image_base64": large_image}
        
        response = requests.post(f"{API_BASE}/wardrobe", json=item_data, headers=headers)
        if response.status_code == 200:
            print(f"   ✅ Added large item {i+1}")
        else:
            print(f"   ❌ Failed to add item {i+1}: {response.status_code}")
            return
    
    # Test outfit generation
    print("🧪 Testing outfit generation with large wardrobe...")
    response = requests.get(f"{API_BASE}/wardrobe/outfits?force_regenerate=true", headers=headers, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        outfits = result.get("outfits", [])
        message = result.get("message", "")
        
        if len(outfits) > 0:
            print(f"✅ SUCCESS: Generated {len(outfits)} outfits with large wardrobe")
            print("✅ MongoDB document size fix is working!")
        else:
            print(f"❌ FAILED: No outfits generated. Message: {message}")
    else:
        print(f"❌ FAILED: Status {response.status_code}")

if __name__ == "__main__":
    test_mongodb_fix()