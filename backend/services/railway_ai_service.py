"""
Railway Fashion AI Segmentation Service
Integrates with Railway microservice for intelligent product extraction
"""
import requests
import asyncio
from typing import List, Dict, Optional
import uuid

RAILWAY_API_URL = "https://fashion-ai-segmentation-production.up.railway.app/"
RAILWAY_API_KEY = "a7fbf9bf-6718-4e18-ac5c-d85575fa3c9a"

async def extract_products_from_image(image_base64: str, user_id: str) -> List[Dict]:
    """
    Extract individual fashion products from an image using Railway AI segmentation service
    
    Args:
        image_base64: Base64 encoded image data
        user_id: User ID for logging/tracking
        
    Returns:
        List of extracted products with metadata
    """
    try:
        print(f"🤖 Railway AI: Extracting products for user {user_id}")
        
        # Convert base64 to bytes for multipart upload
        import base64
        from io import BytesIO
        
        image_bytes = base64.b64decode(image_base64)
        
        # Prepare multipart form data
        files = {
            'image': ('image.jpg', BytesIO(image_bytes), 'image/jpeg')
        }
        
        headers = {
            "Authorization": f"Bearer {RAILWAY_API_KEY}",
        }
        
        # Try multiple possible endpoints
        endpoints_to_try = [
            "/segment/image",
            "/upload", 
            "/api/segment",
            "/api/upload",
            "/extract-products"
        ]
        
        response = None
        for endpoint in endpoints_to_try:
            try:
                print(f"🔄 Trying Railway AI endpoint: {endpoint}")
                
                # Make async request to Railway API
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda ep=endpoint: requests.post(
                        f"{RAILWAY_API_URL}{ep}",
                        files=files,
                        headers=headers,
                        timeout=30
                    )
                )
                
                if response.status_code == 200:
                    print(f"✅ Railway AI responded successfully on {endpoint}")
                    break
                else:
                    print(f"❌ Endpoint {endpoint} failed with status {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Endpoint {endpoint} error: {str(e)}")
                continue
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("products", [])
            
            print(f"✅ Railway AI: Extracted {len(products)} products")
            
            # Process and format the extracted products
            formatted_products = []
            for idx, product in enumerate(products):
                formatted_product = {
                    "id": str(uuid.uuid4()),
                    "exact_item_name": product.get("name", f"Extracted Item {idx + 1}"),
                    "category": normalize_category(product.get("category", "Tops")),
                    "color": product.get("color", "Unknown"),
                    "pattern": product.get("pattern", "Solid"),
                    "fabric_type": product.get("fabric", "Cotton"),
                    "style": product.get("style", "Casual"),
                    "confidence_score": product.get("confidence", 0.8),
                    "image_base64": product.get("segmented_image", image_base64),  # Use segmented image if available
                    "extraction_source": "railway_ai",
                    "tags": ["extracted", "ai-segmented"] + product.get("tags", [])
                }
                formatted_products.append(formatted_product)
            
            return formatted_products
            
        else:
            print(f"❌ Railway AI error: {response.status_code} - {response.text}")
            return []
            
    except requests.exceptions.Timeout:
        print("⏱️ Railway AI timeout - falling back to single item processing")
        return []
    except Exception as e:
        print(f"❌ Railway AI error: {str(e)}")
        return []

def normalize_category(category: str) -> str:
    """
    Normalize category names to match our wardrobe system
    """
    category_mapping = {
        "shirt": "Shirts",
        "t-shirt": "T-shirts", 
        "tshirt": "T-shirts",
        "top": "Tops",
        "blouse": "Tops",
        "dress": "Dresses",
        "pant": "Pants",
        "pants": "Pants",
        "jean": "Jeans",
        "jeans": "Jeans",
        "trouser": "Pants",
        "skirt": "Skirts",
        "jacket": "Jackets",
        "coat": "Jackets",
        "blazer": "Jackets",
        "sweater": "Tops",
        "hoodie": "Tops",
        "shoe": "Shoes",
        "shoes": "Shoes",
        "sneaker": "Shoes",
        "sneakers": "Shoes",
        "boot": "Shoes",
        "boots": "Shoes",
        "accessory": "Accessories",
        "bag": "Accessories",
        "purse": "Accessories",
        "hat": "Accessories",
        "scarf": "Accessories"
    }
    
    normalized = category_mapping.get(category.lower(), category.title())
    return normalized

async def check_for_duplicate_items(new_items: List[Dict], existing_wardrobe: List[Dict]) -> List[Dict]:
    """
    Check for duplicate items in the wardrobe to prevent duplicate additions
    
    Args:
        new_items: List of new items to add
        existing_wardrobe: User's existing wardrobe items
        
    Returns:
        List of non-duplicate items to add
    """
    unique_items = []
    
    for new_item in new_items:
        is_duplicate = False
        
        for existing_item in existing_wardrobe:
            # Check for similarity based on category, color, and item name
            similarity_score = calculate_item_similarity(new_item, existing_item)
            
            if similarity_score > 0.8:  # 80% similarity threshold
                print(f"🔍 Duplicate detected: {new_item.get('exact_item_name')} (similarity: {similarity_score:.2f})")
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_items.append(new_item)
        else:
            print(f"⚠️ Skipping duplicate item: {new_item.get('exact_item_name')}")
    
    print(f"📊 Duplicate check: {len(new_items)} → {len(unique_items)} unique items")
    return unique_items

def calculate_item_similarity(item1: Dict, item2: Dict) -> float:
    """
    Calculate similarity between two wardrobe items
    
    Returns:
        Float between 0 and 1 indicating similarity
    """
    similarity_factors = []
    
    # Category similarity (high weight)
    if item1.get("category", "").lower() == item2.get("category", "").lower():
        similarity_factors.append(0.4)  # 40% weight for category match
    
    # Color similarity (high weight)
    color1 = item1.get("color", "").lower().replace(" ", "")
    color2 = item2.get("color", "").lower().replace(" ", "")
    if color1 and color2 and color1 in color2 or color2 in color1:
        similarity_factors.append(0.3)  # 30% weight for color match
    
    # Name similarity (medium weight)
    name1 = item1.get("exact_item_name", "").lower()
    name2 = item2.get("exact_item_name", "").lower()
    name_words1 = set(name1.split())
    name_words2 = set(name2.split())
    
    if name_words1 and name_words2:
        name_intersection = len(name_words1.intersection(name_words2))
        name_union = len(name_words1.union(name_words2))
        if name_union > 0:
            name_similarity = name_intersection / name_union
            if name_similarity > 0.3:  # At least 30% word overlap
                similarity_factors.append(0.2 * name_similarity)  # Up to 20% weight
    
    # Style and fabric similarity (low weight)
    if item1.get("style", "").lower() == item2.get("style", "").lower():
        similarity_factors.append(0.05)
        
    if item1.get("fabric_type", "").lower() == item2.get("fabric_type", "").lower():
        similarity_factors.append(0.05)
    
    return sum(similarity_factors)