#!/usr/bin/env python3
"""
Test different crop path patterns to find the correct Railway AI naming convention
"""

import requests
import base64
from io import BytesIO
from PIL import Image, ImageDraw
import time

RAILWAY_AI_URL = "https://fashion-ai-segmentation-production.up.railway.app"

def create_test_image():
    """Create a simple test image"""
    image = Image.new('RGB', (400, 600), (240, 240, 240))
    draw = ImageDraw.Draw(image)
    
    # Draw shirt
    draw.rectangle([100, 100, 300, 300], fill=(70, 130, 180), outline=(50, 100, 150), width=3)
    # Draw pants  
    draw.rectangle([120, 300, 280, 500], fill=(25, 25, 112), outline=(15, 15, 80), width=3)
    
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=90)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def test_railway_upload():
    """Upload image to Railway AI and get response"""
    test_image_b64 = create_test_image()
    image_bytes = base64.b64decode(test_image_b64)
    
    # Generate unique filename
    timestamp = int(time.time())
    actual_filename = f"test_crop_paths_{timestamp}"
    
    files = {
        'file': (f'{actual_filename}.jpg', BytesIO(image_bytes), 'image/jpeg')
    }
    
    print(f"📡 Uploading with filename: {actual_filename}.jpg")
    
    response = requests.post(f"{RAILWAY_AI_URL}/upload", files=files, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Railway AI Response: {data}")
        return data, actual_filename
    else:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
        return None, None

def test_crop_path_patterns(railway_data, actual_filename):
    """Test different crop path patterns to find the correct one"""
    if not railway_data:
        return
    
    categories = railway_data.get("categories", [])
    image_name = railway_data.get("image_name", "")
    
    print(f"\n🔍 Testing crop path patterns...")
    print(f"   Image name from Railway: {image_name}")
    print(f"   Actual filename used: {actual_filename}")
    print(f"   Categories: {categories}")
    
    # Test different naming patterns
    patterns_to_test = []
    
    for idx, category in enumerate(categories):
        # Pattern 1: crops_centered/{actual_filename}_{category}_{number}.png
        pattern1 = f"crops_centered/{actual_filename}_{category.lower().replace('-', '_')}_{idx + 1}.png"
        patterns_to_test.append(pattern1)
        
        # Pattern 2: crops_centered/{image_name}_{category}_{number}.png  
        pattern2 = f"crops_centered/{image_name}_{category.lower().replace('-', '_')}_{idx + 1}.png"
        patterns_to_test.append(pattern2)
        
        # Pattern 3: crops/{actual_filename}_{category}_{number}.png
        pattern3 = f"crops/{actual_filename}_{category.lower().replace('-', '_')}_{idx + 1}.png"
        patterns_to_test.append(pattern3)
        
        # Pattern 4: outputs/{actual_filename}_{category}_{number}.png
        pattern4 = f"outputs/{actual_filename}_{category.lower().replace('-', '_')}_{idx + 1}.png"
        patterns_to_test.append(pattern4)
        
        # Pattern 5: {actual_filename}_{category}_{number}.png (no directory)
        pattern5 = f"{actual_filename}_{category.lower().replace('-', '_')}_{idx + 1}.png"
        patterns_to_test.append(pattern5)
        
        # Pattern 6: crops_centered/{actual_filename}_{category}.png (no number)
        pattern6 = f"crops_centered/{actual_filename}_{category.lower().replace('-', '_')}.png"
        patterns_to_test.append(pattern6)
    
    # Test each pattern
    for pattern in patterns_to_test:
        test_url = f"{RAILWAY_AI_URL}/outputs/{pattern}"
        print(f"\n📥 Testing: {pattern}")
        print(f"   URL: {test_url}")
        
        try:
            response = requests.get(test_url, timeout=10)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                print(f"   ✅ SUCCESS! Status: {response.status_code}, Content-Type: {content_type}, Size: {len(response.content)} bytes")
                
                # Try to verify it's a valid image
                if 'image' in content_type.lower() and len(response.content) > 100:
                    print(f"   🖼️ Valid image found!")
                    return pattern
            else:
                print(f"   ❌ Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print(f"\n❌ No valid crop paths found with any tested pattern")
    return None

def main():
    """Main test execution"""
    print("🧪 Testing Railway AI Crop Path Patterns")
    print("=" * 60)
    
    # Upload image and get response
    railway_data, actual_filename = test_railway_upload()
    
    if railway_data and actual_filename:
        # Test different crop path patterns
        successful_pattern = test_crop_path_patterns(railway_data, actual_filename)
        
        if successful_pattern:
            print(f"\n✅ FOUND WORKING PATTERN: {successful_pattern}")
        else:
            print(f"\n❌ NO WORKING PATTERNS FOUND")
            print(f"   This suggests either:")
            print(f"   1. Railway AI doesn't create crop files for this type of image")
            print(f"   2. The naming convention is different than expected")
            print(f"   3. There's a delay in file creation")
            print(f"   4. The files are stored in a different location")
    else:
        print(f"\n❌ Failed to upload image to Railway AI")

if __name__ == "__main__":
    main()