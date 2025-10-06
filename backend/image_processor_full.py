"""
Advanced Image Processing Module for AI Stylist
Handles clothing extraction, background removal, and complementary background generation
"""

import base64
import io
import logging
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import colorsys
import openai
import json
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClothingImageProcessor:
    def __init__(self, openai_client):
        """Initialize the clothing image processor with memory optimization"""
        self.openai_client = openai_client
        self.bg_session = None
        
        logger.info("Image processor initialized")

    def base64_to_pil(self, base64_str: str) -> Image.Image:
        """Convert base64 string to PIL Image with proper orientation"""
        if base64_str.startswith('data:image'):
            base64_str = base64_str.split(',')[1]
        
        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data))
        
        # Fix image orientation using EXIF data
        try:
            from PIL import ExifTags
            
            # Check if image has EXIF data
            if hasattr(image, '_getexif') and image._getexif() is not None:
                exif = image._getexif()
                
                # Find orientation tag
                orientation_key = None
                for key, value in ExifTags.TAGS.items():
                    if value == 'Orientation':
                        orientation_key = key
                        break
                
                if orientation_key and orientation_key in exif:
                    orientation = exif[orientation_key]
                    
                    # Apply rotation based on orientation
                    if orientation == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation == 6:
                        image = image.rotate(270, expand=True)
                    elif orientation == 8:
                        image = image.rotate(90, expand=True)
                    
                    logger.info(f"Fixed image orientation: {orientation}")
        
        except Exception as e:
            logger.warning(f"Could not fix image orientation: {e}")
        
        return image.convert('RGBA')

    def pil_to_base64(self, image: Image.Image, format='PNG') -> str:
        """Convert PIL Image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        img_data = buffer.getvalue()
        return base64.b64encode(img_data).decode('utf-8')

    async def detect_clothing_items(self, image_base64: str) -> List[Dict[str, Any]]:
        """
        Use OpenAI Vision API to detect ONLY FULLY VISIBLE clothing items
        Only return items that are complete and not cut-off or partially hidden
        """
        try:
            clean_base64 = image_base64
            if image_base64.startswith('data:image'):
                clean_base64 = image_base64.split(',')[1]
            
            image_url = f"data:image/jpeg;base64,{clean_base64}"
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert fashion analyst. ONLY analyze clothing items that are FULLY VISIBLE and COMPLETE in the image.

CRITICAL REQUIREMENTS:
- ONLY include items where you can see the COMPLETE garment (not cut-off or partially hidden)
- EXCLUDE any clothing that is partially outside the image frame
- EXCLUDE items where only a portion is visible (like half of a shirt or cut-off pants)
- EXCLUDE items that are mostly obscured by other objects or people

For EACH FULLY VISIBLE clothing item, provide detailed analysis:

SPECIFICATIONS:
- exact_color: precise color (e.g., "deep navy blue", "bright red", "charcoal gray")  
- exact_style: specific style (crew neck, v-neck, straight-leg jeans, etc.)
- fit_details: how it appears to fit (fitted, loose, regular, oversized)
- fabric_appearance: visible texture/material (cotton, denim, wool, etc.)
- specific_features: visible details (buttons, pockets, logos, patterns, etc.)
- completeness_check: confirm the entire garment is visible

Respond in JSON format:
{
  "items": [
    {
      "item_type": "upperwear",
      "category": "t-shirt", 
      "exact_item_name": "navy blue cotton crew neck t-shirt",
      "exact_color": "navy blue",
      "detailed_description": "Complete navy blue t-shirt with crew neckline, short sleeves, appears to be cotton material",
      "exact_style": "crew neck short sleeve",
      "fit_details": "regular fit",
      "fabric_appearance": "cotton jersey",
      "specific_features": "solid color, no visible graphics",
      "completeness_check": "entire garment visible",
      "pattern": "solid",
      "fabric_type": "cotton", 
      "style": "casual",
      "fit": "regular",
      "confidence": 8,
      "tags": ["casual", "cotton", "basic"]
    }
  ]
}

ONLY return items that are COMPLETE and FULLY VISIBLE in the image. If no complete items are visible, return empty items array."""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": "ANALYZE these clothing items with EXTREME DETAIL. I need to recreate the EXACT SAME products - not generic versions. Study every detail: exact colors, specific style features, fabric texture, fit, construction details, etc. Be as specific as possible about what you actually see."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content
            logger.info(f"OpenAI clothing detection response: {response_text[:200]}...")
            
            # Clean and parse JSON response
            clean_response = response_text.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response.replace('```json', '').replace('```', '').strip()
            elif clean_response.startswith('```'):
                clean_response = clean_response.replace('```', '').strip()
            
            result = json.loads(clean_response)
            items = result.get('items', [])
            
            logger.info(f"Detected {len(items)} clothing items")
            return items
            
        except Exception as e:
            logger.error(f"Error detecting clothing items: {e}")
            # Return fallback single item
            return [{
                "item_type": "upperwear",
                "category": "garment",
                "exact_item_name": "clothing item",
                "color": "multicolor",
                "pattern": "solid",
                "fabric_type": "fabric",
                "style": "casual",
                "fit": "regular",
                "confidence": 5,
                "tags": ["clothing"]
            }]

    def remove_background(self, image: Image.Image) -> Image.Image:
        """Remove background from clothing image using rembg"""
        try:
            # Import rembg here to avoid startup issues
            try:
                from rembg import remove, new_session
            except ImportError as e:
                logger.error(f"rembg import failed: {e}. Using fallback background removal.")
                return image.convert('RGBA')
            
            # Initialize session if needed
            if not hasattr(self, 'bg_session') or self.bg_session is None:
                try:
                    self.bg_session = new_session('u2net')
                    logger.info("Background removal session initialized")
                except Exception as session_error:
                    logger.error(f"Failed to initialize bg session: {session_error}")
                    return image.convert('RGBA')
            
            # Convert PIL to bytes
            img_byte_arr = io.BytesIO()
            image.convert('RGB').save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Remove background
            output = remove(img_byte_arr.getvalue(), session=self.bg_session)
            
            # Convert back to PIL
            result_image = Image.open(io.BytesIO(output)).convert('RGBA')
            logger.info("Background removed successfully")
            return result_image
            
        except Exception as e:
            logger.error(f"Error removing background: {e}")
            # Return original image with transparent background as fallback
            return image.convert('RGBA')

    def get_complementary_color(self, dominant_color: str) -> Tuple[int, int, int]:
        """Generate a complementary background color based on clothing color"""
        try:
            # Color mapping for fashion-appropriate backgrounds - preferring lighter tones
            color_backgrounds = {
                'white': (248, 250, 252),    # Very light gray (subtle contrast)
                'black': (255, 255, 255),    # Pure white
                'red': (254, 249, 195),      # Light cream
                'blue': (255, 251, 235),     # Light cream
                'green': (254, 252, 232),    # Light ivory
                'yellow': (255, 255, 255),   # Pure white
                'pink': (255, 253, 240),     # Light cream
                'purple': (254, 250, 224),   # Light vanilla
                'orange': (255, 255, 255),   # Pure white
                'brown': (254, 252, 232),    # Light ivory
                'gray': (255, 255, 255),     # Pure white
                'grey': (255, 255, 255),     # Pure white
                'navy': (254, 249, 195),     # Light cream
                'beige': (255, 255, 255),    # Pure white
                'cream': (248, 250, 252),    # Very light gray
                'gold': (255, 251, 235),     # Light cream
                'silver': (255, 255, 255),   # Pure white
                'denim': (255, 253, 240),    # Light cream
                'khaki': (254, 252, 232),    # Light ivory
                'maroon': (254, 249, 195),   # Light cream
                'turquoise': (255, 251, 235), # Light cream
                'dark': (255, 255, 255),     # Pure white for any dark items
                'light': (248, 250, 252),    # Very light gray for light items
            }
            
            # Normalize color name
            color_key = dominant_color.lower().strip()
            
            # Check for exact matches first
            if color_key in color_backgrounds:
                return color_backgrounds[color_key]
            
            # Check for partial matches
            for key in color_backgrounds:
                if key in color_key or color_key in key:
                    return color_backgrounds[key]
            
            # Default complementary calculation for unknown colors
            if 'light' in color_key or 'pale' in color_key:
                return (31, 41, 55)  # Dark background for light colors
            elif 'dark' in color_key or 'deep' in color_key:
                return (249, 250, 251)  # Light background for dark colors
            
            # Default sophisticated background
            return (248, 250, 252)  # Very light gray
            
        except Exception as e:
            logger.error(f"Error generating complementary color: {e}")
            return (248, 250, 252)  # Default light gray

    def create_gradient_background(self, width: int, height: int, color: Tuple[int, int, int]) -> Image.Image:
        """Create an elegant gradient background"""
        try:
            # Create gradient from main color to slightly lighter/darker variation
            r, g, b = color
            
            # Create subtle gradient by adjusting brightness
            top_color = tuple(min(255, int(c * 1.1)) for c in color)
            bottom_color = tuple(max(0, int(c * 0.9)) for c in color)
            
            # Create gradient
            background = Image.new('RGB', (width, height), top_color)
            draw = ImageDraw.Draw(background)
            
            # Draw gradient
            for y in range(height):
                ratio = y / height
                interpolated_color = tuple(
                    int(top_color[i] * (1 - ratio) + bottom_color[i] * ratio)
                    for i in range(3)
                )
                draw.line([(0, y), (width, y)], fill=interpolated_color)
            
            # Add subtle texture with soft circles
            overlay = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Add subtle decorative elements
            circle_positions = [
                (width * 0.15, height * 0.2, width * 0.08),
                (width * 0.85, height * 0.7, width * 0.06),
                (width * 0.3, height * 0.8, width * 0.04),
            ]
            
            for x, y, radius in circle_positions:
                overlay_draw.ellipse(
                    [x - radius, y - radius, x + radius, y + radius],
                    fill=(255, 255, 255, 8)  # Very subtle white circles
                )
            
            # Composite gradient with overlay
            background = background.convert('RGBA')
            background = Image.alpha_composite(background, overlay)
            
            return background.convert('RGB')
            
        except Exception as e:
            logger.error(f"Error creating gradient background: {e}")
            return Image.new('RGB', (width, height), color)

    async def extract_product_only(self, image_base64: str, item_info: Dict[str, Any]) -> str:
        """
        Extract clothing item and create clean product catalog image (like reference examples)
        """
        try:
            # Process image to create clean product photo
            return await self.create_catalog_product_image(image_base64, item_info)
            
        except Exception as e:
            logger.error(f"Error in product extraction: {e}")
            return await self.create_catalog_product_image(image_base64, item_info)

    async def extract_specific_item(self, image_base64: str, item_info: Dict[str, Any]) -> str:
        """
        Extract the EXACT product from the uploaded image - no AI generation
        Simple background removal and clean presentation of the actual uploaded product
        """
        try:
            # Get item-specific information
            item_type = item_info.get('item_type', 'upperwear')
            category = item_info.get('category', 'garment')
            color = item_info.get('color', 'white')
            exact_name = item_info.get('exact_item_name', category)
            
            logger.info(f"EXTRACTING ACTUAL PRODUCT: {exact_name} ({item_type}) from uploaded image")
            
            # Extract the actual product from the uploaded image (no AI generation)
            extracted_image = await self.extract_actual_product_simple(image_base64, item_info)
            
            return extracted_image
            
        except Exception as e:
            logger.error(f"Error extracting actual product for {item_info.get('category', 'item')}: {e}")
            # Fallback to basic processing of the actual image
            return await self.create_catalog_product_image(image_base64, item_info)

    async def create_item_specific_catalog_image(self, image_base64: str, item_info: Dict[str, Any]) -> str:
        """
        Create item-specific catalog image with targeted processing for each clothing type
        This ensures each item gets unique processing based on its characteristics
        """
        try:
            # Convert to PIL Image
            original_image = self.base64_to_pil(image_base64)
            
            # Get item-specific processing parameters
            item_type = item_info.get('item_type', 'upperwear')
            category = item_info.get('category', 'garment')
            color = item_info.get('color', 'white')
            
            # Step 1: Item-specific background removal with targeted model selection
            product_extracted = await self.item_specific_background_removal(original_image, item_type, category)
            
            # Step 2: Item-specific cropping based on clothing type
            cropped_product = self.item_specific_crop(product_extracted, item_type)
            
            # Step 3: Create item-specific catalog background
            catalog_background = self.create_item_specific_background(item_type, color)
            
            # Step 4: Item-specific positioning and scaling
            final_product = self.position_item_specifically(catalog_background, cropped_product, item_type)
            
            # Step 5: Apply item-specific enhancements
            final_product = self.apply_item_specific_enhancements(final_product, item_type)
            
            # Convert back to base64
            processed_base64 = self.pil_to_base64(final_product.convert('RGB'), 'JPEG')
            
            logger.info(f"Created item-specific catalog image for {category} ({item_type})")
            return processed_base64
            
        except Exception as e:
            logger.error(f"Error creating item-specific catalog image: {e}")
            # Fallback to general catalog processing
            return await self.create_catalog_product_image(image_base64, item_info)

    async def item_specific_background_removal(self, image: Image.Image, item_type: str, category: str) -> Image.Image:
        """Item-specific background removal with targeted model selection"""
        try:
            try:
                from rembg import remove, new_session
            except ImportError as e:
                logger.error(f"rembg import failed: {e}. Using fallback background removal.")
                return image.convert('RGBA')
            
            # Select model based on item type for better results
            model_priority = {
                'upperwear': ['u2net_cloth_seg', 'u2net', 'silueta'],
                'lowerwear': ['u2net_cloth_seg', 'u2net', 'silueta'], 
                'footwear': ['u2net', 'silueta'],
                'dress': ['u2net_cloth_seg', 'u2net'],
                'layer': ['u2net_cloth_seg', 'u2net']
            }
            
            models_to_try = model_priority.get(item_type, ['u2net', 'silueta'])
            
            for model_name in models_to_try:
                try:
                    session = new_session(model_name)
                    logger.info(f"Using {model_name} for {item_type} background removal")
                    
                    # Convert PIL to bytes
                    img_byte_arr = io.BytesIO()
                    image.convert('RGB').save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    
                    # Remove background
                    output = remove(img_byte_arr.getvalue(), session=session)
                    result_image = Image.open(io.BytesIO(output)).convert('RGBA')
                    
                    # Check if we got a good result
                    bbox = result_image.getbbox()
                    if bbox:
                        logger.info(f"Successfully removed background for {category} using {model_name}")
                        return result_image
                        
                except Exception as model_error:
                    logger.warning(f"Model {model_name} failed for {item_type}: {model_error}")
                    continue
            
            # Fallback to basic removal
            logger.warning(f"All specialized models failed for {item_type}, using basic removal")
            return self.remove_background_advanced(image)
            
        except Exception as e:
            logger.error(f"Item-specific background removal failed: {e}")
            return image.convert('RGBA')

    def item_specific_crop(self, image: Image.Image, item_type: str) -> Image.Image:
        """Item-specific cropping based on clothing type"""
        try:
            bbox = image.getbbox()
            if not bbox:
                return image
                
            left, top, right, bottom = bbox
            width = right - left
            height = bottom - top
            
            # Different cropping strategies for different item types
            if item_type == 'upperwear':
                # Focus on upper portion, allow more vertical space
                crop_margin_x = width * 0.08
                crop_margin_y = height * 0.06
            elif item_type == 'lowerwear':
                # Focus on lower portion, tighter horizontal crop
                crop_margin_x = width * 0.06
                crop_margin_y = height * 0.08
            elif item_type == 'footwear':
                # Tight crop for shoes
                crop_margin_x = width * 0.05
                crop_margin_y = height * 0.05
            elif item_type == 'dress':
                # Full garment, balanced crop
                crop_margin_x = width * 0.07
                crop_margin_y = height * 0.07
            else:
                # Default crop
                crop_margin_x = width * 0.06
                crop_margin_y = height * 0.06
            
            # Apply item-specific cropping
            final_left = max(0, left - crop_margin_x)
            final_top = max(0, top - crop_margin_y)
            final_right = min(image.width, right + crop_margin_x)
            final_bottom = min(image.height, bottom + crop_margin_y)
            
            cropped = image.crop((final_left, final_top, final_right, final_bottom))
            logger.info(f"Applied {item_type}-specific crop from {image.size} to {cropped.size}")
            return cropped
            
        except Exception as e:
            logger.error(f"Error in item-specific crop for {item_type}: {e}")
            return image

    def create_item_specific_background(self, item_type: str, color: str) -> Image.Image:
        """Create item-specific background based on type and color"""
        try:
            # Different sizes for different item types - standard catalog sizes
            size_mapping = {
                'upperwear': (800, 900),    # Taller for shirts
                'lowerwear': (900, 800),    # Wider for pants  
                'footwear': (800, 600),     # Smaller for shoes
                'dress': (700, 1000),       # Tall for dresses
                'layer': (800, 900),        # Same as upperwear
            }
            
            size = size_mapping.get(item_type, (800, 800))  # Default square
            
            # Clean backgrounds based on item color (same logic as before)
            if color.lower() in ['black', 'dark', 'navy', 'charcoal']:
                bg_color = (248, 249, 250)  # Very light gray for dark items
            elif color.lower() in ['white', 'cream', 'light', 'beige']:
                bg_color = (245, 245, 245)  # Light gray for light items
            else:
                bg_color = (255, 255, 255)  # Pure white for colorful items
            
            # Create solid background
            background = Image.new('RGB', size, bg_color)
            
            logger.info(f"Created {item_type}-specific background {size} in color {bg_color}")
            return background
            
        except Exception as e:
            logger.error(f"Error creating item-specific background: {e}")
            return Image.new('RGB', (800, 800), (255, 255, 255))

    def position_item_specifically(self, background: Image.Image, product: Image.Image, item_type: str) -> Image.Image:
        """Position product based on item type"""
        try:
            bg_width, bg_height = background.size
            prod_width, prod_height = product.size
            
            # Item-type specific scaling and positioning
            if item_type == 'upperwear':
                max_scale = 0.75  # Shirts can be larger
                y_offset = -0.05  # Slightly higher
            elif item_type == 'lowerwear':
                max_scale = 0.70  # Pants medium size
                y_offset = 0.05   # Slightly lower
            elif item_type == 'footwear':
                max_scale = 0.65  # Shoes smaller
                y_offset = 0.10   # Lower position
            elif item_type == 'dress':
                max_scale = 0.80  # Dresses can be large
                y_offset = 0.0    # Centered
            else:
                max_scale = 0.75  # Default
                y_offset = 0.0
            
            # Calculate scaling
            scale_factor = min(
                (bg_width * max_scale) / prod_width,
                (bg_height * max_scale) / prod_height,
                2.0  # Don't upscale too much
            )
            
            # Resize if needed
            if scale_factor != 1.0:
                new_width = int(prod_width * scale_factor)
                new_height = int(prod_height * scale_factor)
                product = product.resize((new_width, new_height), Image.Resampling.LANCZOS)
                prod_width, prod_height = new_width, new_height
            
            # Position with item-specific offset
            x = (bg_width - prod_width) // 2
            y = int((bg_height - prod_height) // 2 + (bg_height * y_offset))
            
            # Ensure item stays within bounds
            y = max(0, min(y, bg_height - prod_height))
            
            # Composite
            background = background.convert('RGBA')
            background.paste(product, (x, y), product if product.mode == 'RGBA' else None)
            
            logger.info(f"Positioned {item_type} at ({x}, {y}) with scale {scale_factor:.2f}")
            return background
            
        except Exception as e:
            logger.error(f"Error positioning {item_type}: {e}")
            return background

    def apply_item_specific_enhancements(self, image: Image.Image, item_type: str) -> Image.Image:
        """Apply enhancements based on item type"""
        try:
            # Different enhancement levels for different item types
            if item_type == 'footwear':
                # Shoes need more contrast and sharpening
                contrast_factor = 1.2
                sharpness_factor = 1.25
                color_factor = 1.15
            elif item_type in ['upperwear', 'dress']:
                # Clothing needs balanced enhancement
                contrast_factor = 1.15
                sharpness_factor = 1.15
                color_factor = 1.1
            elif item_type == 'lowerwear':
                # Pants/jeans need moderate enhancement
                contrast_factor = 1.1
                sharpness_factor = 1.1
                color_factor = 1.08
            else:
                # Default enhancement
                contrast_factor = 1.1
                sharpness_factor = 1.1
                color_factor = 1.05
            
            # Apply enhancements
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(contrast_factor)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(sharpness_factor)
            
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(color_factor)
            
            # Slight brightness for catalog look
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.05)
            
            logger.info(f"Applied {item_type}-specific enhancements")
            return image
            
        except Exception as e:
            logger.error(f"Error applying enhancements for {item_type}: {e}")
            return image

    async def extract_actual_product_simple(self, image_base64: str, item_info: Dict[str, Any]) -> str:
        """
        Extract the EXACT product from uploaded image - no AI generation
        Simple background removal and clean presentation on plain background
        """
        try:
            # Convert to PIL Image
            original_image = self.base64_to_pil(image_base64)
            
            # Step 1: Remove background to isolate the clothing item
            product_extracted = self.remove_background_advanced(original_image)
            
            # Step 2: Check if we got a valid product (not empty or too small)
            bbox = product_extracted.getbbox()
            if not bbox:
                logger.warning("No product found after background removal")
                return await self.create_simple_fallback(item_info)
            
            # Check if product is reasonably sized (not too small/partial)
            left, top, right, bottom = bbox
            width = right - left
            height = bottom - top
            original_area = original_image.width * original_image.height
            product_area = width * height
            
            # If product takes less than 5% of image, it might be partial/cut-off
            if product_area < (original_area * 0.05):
                logger.warning(f"Product appears too small/partial: {product_area}/{original_area}")
                return await self.create_simple_fallback(item_info)
            
            # Step 3: Crop tightly around the product
            cropped_product = self.aggressive_product_crop(product_extracted)
            
            # Step 4: Create clean background (800x800 standard size)
            item_color = item_info.get('color', 'white')
            if item_color.lower() in ['black', 'dark', 'navy']:
                bg_color = (248, 249, 250)  # Light gray for dark items
            elif item_color.lower() in ['white', 'light', 'cream']:
                bg_color = (245, 245, 245)  # Slightly darker for light items
            else:
                bg_color = (255, 255, 255)  # Pure white for colored items
            
            clean_background = Image.new('RGB', (800, 800), bg_color)
            
            # Step 5: Position the actual extracted product on clean background
            final_image = self.position_for_catalog(clean_background, cropped_product)
            
            # Step 6: Light enhancement for catalog look
            final_image = self.apply_simple_enhancements(final_image)
            
            # Convert back to base64
            processed_base64 = self.pil_to_base64(final_image.convert('RGB'), 'JPEG')
            
            logger.info(f"Successfully extracted actual product: {item_info.get('category', 'item')}")
            return processed_base64
            
        except Exception as e:
            logger.error(f"Error extracting actual product: {e}")
            return await self.create_simple_fallback(item_info)
    
    async def create_simple_fallback(self, item_info: Dict[str, Any]) -> str:
        """Create a simple colored rectangle as fallback when product extraction fails"""
        try:
            category = item_info.get('category', 'garment')
            color = item_info.get('color', 'gray')
            
            # Create simple colored rectangle
            fallback = Image.new('RGB', (800, 800), (255, 255, 255))
            draw = ImageDraw.Draw(fallback)
            
            # Color mapping
            color_map = {
                'red': (220, 53, 69), 'blue': (13, 110, 253), 'green': (25, 135, 84),
                'yellow': (255, 193, 7), 'purple': (111, 66, 193), 'orange': (253, 126, 20),
                'pink': (214, 51, 132), 'brown': (121, 85, 72), 'black': (33, 37, 41),
                'white': (248, 249, 250), 'navy': (13, 27, 62), 'gray': (108, 117, 125),
            }
            
            item_color = color_map.get(color.lower(), (128, 128, 128))
            
            # Draw simple product shape
            center_x, center_y = 400, 400
            if 'shirt' in category.lower() or 'top' in category.lower():
                # Simple shirt rectangle
                draw.rectangle([center_x-100, center_y-120, center_x+100, center_y+80], 
                              fill=item_color, outline=(0,0,0), width=2)
            elif 'pants' in category.lower() or 'jean' in category.lower():
                # Simple pants rectangle
                draw.rectangle([center_x-80, center_y-100, center_x+80, center_y+120],
                              fill=item_color, outline=(0,0,0), width=2)
            else:
                # Generic rectangle
                draw.rectangle([center_x-90, center_y-90, center_x+90, center_y+90],
                              fill=item_color, outline=(0,0,0), width=2)
            
            return self.pil_to_base64(fallback, 'JPEG')
            
        except Exception as e:
            logger.error(f"Error creating simple fallback: {e}")
            simple_img = Image.new('RGB', (400, 400), (240, 240, 240))
            return self.pil_to_base64(simple_img, 'JPEG')

    def apply_simple_enhancements(self, image: Image.Image) -> Image.Image:
        """Apply simple, light enhancements for clean look"""
        try:
            # Very light enhancements - just clean up the image
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.05)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.05)
            
            logger.info("Applied simple enhancements")
            return image
        except Exception as e:
            logger.error(f"Error applying simple enhancements: {e}")
            return image

    async def generate_product_image(self, item_info: Dict[str, Any]) -> str:
        """
        Generate EXACT REPLICA of the detected product using detailed analysis
        This creates a precise match to what was seen in the original image
        """
        try:
            # Get detailed analysis from enhanced detection
            category = item_info.get('category', 'garment')
            exact_name = item_info.get('exact_item_name', category)
            exact_color = item_info.get('exact_color', item_info.get('color', 'colored'))
            detailed_description = item_info.get('detailed_description', '')
            exact_style = item_info.get('exact_style', item_info.get('style', 'casual'))
            fit_details = item_info.get('fit_details', 'regular fit')
            fabric_appearance = item_info.get('fabric_appearance', 'fabric')
            specific_features = item_info.get('specific_features', '')
            neckline = item_info.get('neckline', '')
            sleeve_details = item_info.get('sleeve_details', '')
            
            # Create ULTRA-detailed prompt to recreate the exact same product
            prompt_parts = [
                f"Professional product photography of {exact_name}",
                f"in {exact_color} color",
                f"with {exact_style}" if exact_style else "",
                f"{fit_details}" if fit_details else "",
                f"made of {fabric_appearance}" if fabric_appearance else "",
                f"featuring {specific_features}" if specific_features else "",
                f"with {neckline}" if neckline else "",
                f"and {sleeve_details}" if sleeve_details else "",
                "clean white background, centered, studio lighting",
                "high quality fashion product photography",
                "no person, no model, just the clothing item alone",
                "professional catalog style photo"
            ]
            
            # Clean and join the prompt
            prompt = ", ".join([part for part in prompt_parts if part.strip()])
            
            # If we have detailed description, add it
            if detailed_description:
                prompt += f". Product details: {detailed_description}"
            
            logger.info(f"Generating EXACT REPLICA for: {exact_name}")
            logger.info(f"Detailed prompt: {prompt}")
            
            # Generate image using OpenAI DALL-E with detailed prompt
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            
            # Download the generated image
            import httpx
            async with httpx.AsyncClient() as client:
                img_response = await client.get(image_url)
                img_response.raise_for_status()
                
                # Convert to base64
                generated_image_base64 = base64.b64encode(img_response.content).decode('utf-8')
                
                logger.info(f"Successfully generated EXACT REPLICA for {category}")
                return generated_image_base64
            
        except Exception as e:
            logger.error(f"Error generating exact replica for {item_info.get('category', 'item')}: {e}")
            
            # Fallback: Create a simple product placeholder
            return await self.create_product_placeholder(item_info)

    async def create_product_placeholder(self, item_info: Dict[str, Any]) -> str:
        """
        Create a simple product placeholder when image generation fails
        """
        try:
            category = item_info.get('category', 'garment')
            color = item_info.get('color', 'white')
            
            # Create a simple solid color placeholder
            placeholder_size = (800, 800)
            
            # Get color RGB values
            color_mapping = {
                'red': (220, 53, 69),
                'blue': (13, 110, 253),
                'green': (25, 135, 84),
                'yellow': (255, 193, 7),
                'purple': (111, 66, 193),
                'orange': (253, 126, 20),
                'pink': (214, 51, 132),
                'brown': (121, 85, 72),
                'black': (33, 37, 41),
                'white': (248, 249, 250),
                'navy': (13, 27, 62),
                'gray': (108, 117, 125),
                'grey': (108, 117, 125),
            }
            
            item_color = color_mapping.get(color.lower(), (128, 128, 128))
            
            # Create placeholder image
            placeholder = Image.new('RGB', placeholder_size, (255, 255, 255))
            draw = ImageDraw.Draw(placeholder)
            
            # Draw simple product shape based on category
            center_x, center_y = placeholder_size[0] // 2, placeholder_size[1] // 2
            
            if 'shirt' in category.lower() or 'top' in category.lower():
                # Draw shirt shape
                draw.rectangle([center_x-120, center_y-150, center_x+120, center_y+100], 
                              fill=item_color, outline='black', width=3)
                draw.ellipse([center_x-30, center_y-130, center_x+30, center_y-100],
                            fill='white', outline='black', width=2)
            elif 'pants' in category.lower() or 'jean' in category.lower():
                # Draw pants shape
                draw.rectangle([center_x-80, center_y-100, center_x+80, center_y+150],
                              fill=item_color, outline='black', width=3)
            elif 'shoe' in category.lower() or 'sneaker' in category.lower():
                # Draw shoe shape
                draw.ellipse([center_x-100, center_y-30, center_x+100, center_y+50],
                            fill=item_color, outline='black', width=3)
            else:
                # Generic rectangle
                draw.rectangle([center_x-100, center_y-100, center_x+100, center_y+100],
                              fill=item_color, outline='black', width=3)
            
            # Convert to base64
            placeholder_base64 = self.pil_to_base64(placeholder, 'JPEG')
            
            logger.info(f"Created placeholder for {category} in {color}")
            return placeholder_base64
            
        except Exception as e:
            logger.error(f"Error creating placeholder: {e}")
            # Return minimal fallback
            simple_img = Image.new('RGB', (400, 400), (240, 240, 240))
            return self.pil_to_base64(simple_img, 'JPEG')

    async def advanced_product_extraction(self, image_base64: str, item_info: Dict[str, Any]) -> str:
        """
        Advanced product extraction using multiple background removal techniques
        """
        try:
            # Convert to PIL Image
            image = self.base64_to_pil(image_base64)
            
            # Step 1: Advanced background removal using multiple models
            extracted_product = self.remove_background_advanced(image)
            
            # Step 2: Crop and center the product
            cropped_product = self.crop_and_center_product(extracted_product)
            
            # Step 3: Create professional background
            item_color = item_info.get('color', 'white')
            bg_color = self.get_complementary_color(item_color)
            
            # Create a clean product background (400x500 standard product size)
            product_size = (400, 500)
            background = self.create_clean_product_background(product_size[0], product_size[1], bg_color)
            
            # Step 4: Resize and center the product on the new background
            final_image = self.composite_product_professionally(background, cropped_product)
            
            # Step 5: Enhance for product photography
            final_image = self.enhance_for_product_photo(final_image)
            
            # Convert back to base64
            processed_base64 = self.pil_to_base64(final_image.convert('RGB'), 'JPEG')
            
            logger.info(f"Successfully extracted {item_info.get('category', 'product')} as standalone item")
            return processed_base64
            
        except Exception as e:
            logger.error(f"Error in advanced product extraction: {e}")
            # Fallback to basic processing
            return self.process_clothing_item_basic(image_base64, item_info)

    def remove_background_advanced(self, image: Image.Image) -> Image.Image:
        """Advanced background removal focusing on clothing extraction - REMOVE HUMANS COMPLETELY"""
        try:
            try:
                from rembg import remove, new_session
            except ImportError as e:
                logger.error(f"rembg import failed: {e}. Using fallback background removal.")
                return image.convert('RGBA')
            
            # Use the most aggressive background removal model
            try:
                # Try multiple models for best human removal
                models_to_try = ['u2net_human_seg', 'u2net', 'silueta']
                
                for model_name in models_to_try:
                    try:
                        session = new_session(model_name)
                        logger.info(f"Using {model_name} for aggressive background removal")
                        
                        # Convert PIL to bytes
                        img_byte_arr = io.BytesIO()
                        image.convert('RGB').save(img_byte_arr, format='PNG')
                        img_byte_arr.seek(0)
                        
                        # Remove background aggressively
                        output = remove(img_byte_arr.getvalue(), session=session)
                        
                        # Convert back to PIL
                        result_image = Image.open(io.BytesIO(output)).convert('RGBA')
                        
                        # Check if we got a good result (non-empty)
                        bbox = result_image.getbbox()
                        if bbox:
                            logger.info(f"Successfully removed background using {model_name}")
                            return result_image
                            
                    except Exception as model_error:
                        logger.warning(f"Model {model_name} failed: {model_error}")
                        continue
                
                # If all models fail, return transparent version
                logger.error("All background removal models failed")
                return image.convert('RGBA')
                
            except Exception as e:
                logger.error(f"Background removal setup failed: {e}")
                return image.convert('RGBA')
            
        except Exception as e:
            logger.error(f"Advanced background removal completely failed: {e}")
            return image.convert('RGBA')

    def crop_and_center_product(self, image: Image.Image) -> Image.Image:
        """Crop to focus on the product and remove excess transparent space"""
        try:
            # Get the bounding box of non-transparent pixels
            bbox = image.getbbox()
            
            if bbox:
                # Crop to content with some padding
                padding = 20
                left, top, right, bottom = bbox
                
                # Add padding but ensure we don't go outside image bounds
                left = max(0, left - padding)
                top = max(0, top - padding)
                right = min(image.width, right + padding)
                bottom = min(image.height, bottom + padding)
                
                cropped = image.crop((left, top, right, bottom))
                logger.info(f"Cropped product to focus area: {bbox}")
                return cropped
            else:
                logger.warning("No content found for cropping")
                return image
                
        except Exception as e:
            logger.error(f"Error cropping product: {e}")
            return image

    def create_clean_product_background(self, width: int, height: int, color: Tuple[int, int, int]) -> Image.Image:
        """Create a clean, professional product background"""
        try:
            # Create subtle gradient for depth
            background = Image.new('RGB', (width, height), color)
            draw = ImageDraw.Draw(background)
            
            # Add very subtle radial gradient for professional look
            center_x, center_y = width // 2, height // 2
            
            for y in range(height):
                for x in range(width):
                    distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    max_distance = (width ** 2 + height ** 2) ** 0.5 / 2
                    
                    # Very subtle darkening towards edges
                    factor = 1 - (distance / max_distance) * 0.1
                    
                    new_color = tuple(int(c * factor) for c in color)
                    draw.point((x, y), fill=new_color)
            
            return background
            
        except Exception as e:
            logger.error(f"Error creating clean background: {e}")
            return Image.new('RGB', (width, height), color)

    def composite_product_professionally(self, background: Image.Image, product: Image.Image) -> Image.Image:
        """Composite product onto background with professional positioning"""
        try:
            bg_width, bg_height = background.size
            prod_width, prod_height = product.size
            
            # Calculate scaling to fit nicely (leave 15% margin)
            scale_factor = min(
                (bg_width * 0.85) / prod_width,
                (bg_height * 0.85) / prod_height
            )
            
            # Resize product if needed
            if scale_factor < 1:
                new_size = (int(prod_width * scale_factor), int(prod_height * scale_factor))
                product = product.resize(new_size, Image.Resampling.LANCZOS)
                prod_width, prod_height = new_size
            
            # Center the product
            x = (bg_width - prod_width) // 2
            y = (bg_height - prod_height) // 2
            
            # Composite
            background = background.convert('RGBA')
            background.paste(product, (x, y), product)
            
            logger.info(f"Product composited at position ({x}, {y}) with scale {scale_factor:.2f}")
            return background
            
        except Exception as e:
            logger.error(f"Error compositing product: {e}")
            return background

    def enhance_for_product_photo(self, image: Image.Image) -> Image.Image:
        """Apply professional product photography enhancements"""
        try:
            # Slight contrast boost for product clarity
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)
            
            # Slight sharpening
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            # Slight color saturation boost
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.05)
            
            logger.info("Applied product photography enhancements")
            return image
            
        except Exception as e:
            logger.error(f"Error enhancing product photo: {e}")
            return image

    async def create_catalog_product_image(self, image_base64: str, item_info: Dict[str, Any]) -> str:
        """
        Create clean catalog-style product image like the reference examples
        Goal: Clean product on plain background, no humans, professional presentation
        """
        try:
            # Convert to PIL Image
            original_image = self.base64_to_pil(image_base64)
            
            # Step 1: Use advanced background removal with cloth-specific model
            product_extracted = self.remove_background_advanced(original_image)
            
            # Step 2: Aggressive crop to focus only on the clothing item
            cropped_product = self.aggressive_product_crop(product_extracted)
            
            # Step 3: Create professional catalog background (clean and minimal)
            item_color = item_info.get('color', 'white')
            catalog_background = self.create_catalog_background(item_color)
            
            # Step 4: Professional product positioning (centered, proper scaling)
            final_product = self.position_for_catalog(catalog_background, cropped_product)
            
            # Step 5: Apply catalog-style enhancements
            final_product = self.apply_catalog_enhancements(final_product)
            
            # Convert back to base64
            processed_base64 = self.pil_to_base64(final_product.convert('RGB'), 'JPEG')
            
            logger.info(f"Created catalog product image for {item_info.get('category', 'item')}")
            return processed_base64
            
        except Exception as e:
            logger.error(f"Error creating catalog product image: {e}")
            # Fallback to basic processing
            return await self.advanced_product_extraction(image_base64, item_info)

    def aggressive_product_crop(self, image: Image.Image) -> Image.Image:
        """Aggressively crop to focus only on the product, removing as much background as possible"""
        try:
            # Get bounding box of non-transparent content
            bbox = image.getbbox()
            
            if bbox:
                left, top, right, bottom = bbox
                
                # Calculate dimensions
                width = right - left
                height = bottom - top
                
                # Apply aggressive cropping - remove more empty space
                crop_margin = min(width, height) * 0.05  # Only 5% margin
                
                # Crop tightly around the product
                final_left = max(0, left - crop_margin)
                final_top = max(0, top - crop_margin)
                final_right = min(image.width, right + crop_margin)
                final_bottom = min(image.height, bottom + crop_margin)
                
                cropped = image.crop((final_left, final_top, final_right, final_bottom))
                
                logger.info(f"Aggressively cropped product from {image.size} to {cropped.size}")
                return cropped
            else:
                logger.warning("No product content found for aggressive cropping")
                return image
                
        except Exception as e:
            logger.error(f"Error in aggressive product crop: {e}")
            return image

    def create_catalog_background(self, item_color: str) -> Image.Image:
        """Create clean catalog background (900x900 like reference examples)"""
        try:
            # Standard catalog size (square format like examples)
            size = (900, 900)
            
            # Create clean backgrounds based on item color
            if item_color.lower() in ['black', 'dark', 'navy', 'charcoal']:
                # Light background for dark items
                bg_color = (248, 249, 250)  # Very light gray
            elif item_color.lower() in ['white', 'cream', 'light', 'beige']:
                # Slightly off-white for light items
                bg_color = (245, 245, 245)  # Light gray
            else:
                # Clean white for colorful items
                bg_color = (255, 255, 255)  # Pure white
            
            # Create solid background (no gradients - clean and simple)
            background = Image.new('RGB', size, bg_color)
            
            logger.info(f"Created catalog background {size} in color {bg_color} for {item_color} item")
            return background
            
        except Exception as e:
            logger.error(f"Error creating catalog background: {e}")
            return Image.new('RGB', (900, 900), (255, 255, 255))

    def position_for_catalog(self, background: Image.Image, product: Image.Image) -> Image.Image:
        """Position product in catalog style - centered and properly scaled"""
        try:
            bg_width, bg_height = background.size
            prod_width, prod_height = product.size
            
            # Calculate scaling to fit nicely within catalog bounds (leave 20% margin)
            max_product_width = bg_width * 0.8
            max_product_height = bg_height * 0.8
            
            scale_factor = min(
                max_product_width / prod_width,
                max_product_height / prod_height
            )
            
            # Don't upscale too much - keep it natural
            scale_factor = min(scale_factor, 2.0)
            
            # Resize product if needed
            if scale_factor != 1.0:
                new_width = int(prod_width * scale_factor)
                new_height = int(prod_height * scale_factor)
                product = product.resize((new_width, new_height), Image.Resampling.LANCZOS)
                prod_width, prod_height = new_width, new_height
            
            # Center the product perfectly
            x = (bg_width - prod_width) // 2
            y = (bg_height - prod_height) // 2
            
            # Composite product onto background
            background = background.convert('RGBA')
            background.paste(product, (x, y), product if product.mode == 'RGBA' else None)
            
            logger.info(f"Positioned product at ({x}, {y}) with scale {scale_factor:.2f}")
            return background
            
        except Exception as e:
            logger.error(f"Error positioning product for catalog: {e}")
            return background

    def apply_catalog_enhancements(self, image: Image.Image) -> Image.Image:
        """Apply professional catalog-style enhancements"""
        try:
            # Clean, crisp enhancement for catalog style
            
            # Slight contrast for clarity
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.15)
            
            # Sharpening for product details
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)
            
            # Natural color enhancement (not too saturated)
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.1)
            
            # Brightness adjustment for catalog lighting
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.05)
            
            logger.info("Applied catalog-style enhancements")
            return image
            
        except Exception as e:
            logger.error(f"Error applying catalog enhancements: {e}")
            return image

    def process_clothing_item_basic(self, image_base64: str, item_info: Dict[str, Any]) -> str:
        """
        Basic fallback processing method
        """
        try:
            # Convert to PIL Image
            image = self.base64_to_pil(image_base64)
            
            # Basic background removal
            no_bg_image = self.remove_background(image)
            
            # Get complementary background color
            item_color = item_info.get('color', 'white')
            bg_color = self.get_complementary_color(item_color)
            
            # Create simple background
            background = self.create_gradient_background(400, 500, bg_color)
            
            # Basic composite
            background = background.convert('RGBA')
            final_image = Image.alpha_composite(background, no_bg_image.resize((400, 500)))
            
            # Convert back to base64
            processed_base64 = self.pil_to_base64(final_image.convert('RGB'), 'JPEG')
            
            logger.info(f"Basic processing completed for {item_info.get('category', 'item')}")
            return processed_base64
            
        except Exception as e:
            logger.error(f"Error in basic processing: {e}")
            # Return original image if all processing fails
            return image_base64.replace('data:image/jpeg;base64,', '').replace('data:image/png;base64,', '')

    async def extract_and_process_items(self, image_base64: str) -> List[Dict[str, Any]]:
        """
        Main function: Detect multiple clothing items and process each one
        Returns list of processed wardrobe items ready for database
        """
        try:
            # Step 1: Detect all clothing items in the image
            detected_items = await self.detect_clothing_items(image_base64)
            
            # Step 2: Process each item (for now, we'll use the same processed image for all items)
            # In a more advanced implementation, we could segment each item individually
            processed_items = []
            
            for item_info in detected_items:
                # Extract each item separately with item-specific processing
                processed_image_base64 = await self.extract_specific_item(image_base64, item_info)
                
                # Create wardrobe item data structure
                wardrobe_item = {
                    'image_base64': processed_image_base64,
                    'category': item_info.get('category', 'garment'),
                    'exact_item_name': item_info.get('exact_item_name', 'clothing item'),
                    'color': item_info.get('exact_color', item_info.get('color', 'multicolor')),  # Fix: use exact_color first
                    'pattern': item_info.get('pattern', 'solid'),
                    'fabric_type': item_info.get('fabric_type', 'fabric'),
                    'style': item_info.get('style', 'casual'),
                    'fit': item_info.get('fit', 'regular'),
                    'tags': item_info.get('tags', ['clothing']),
                    'item_type': item_info.get('item_type', 'upperwear'),
                    'confidence': item_info.get('confidence', 5)
                }
                
                processed_items.append(wardrobe_item)
            
            logger.info(f"Successfully extracted and processed {len(processed_items)} items")
            return processed_items
            
        except Exception as e:
            logger.error(f"Error in extract_and_process_items: {e}")
            # Return fallback single item
            processed_image = self.process_clothing_item(image_base64, {'color': 'white', 'category': 'garment'})
            return [{
                'image_base64': processed_image,
                'category': 'garment',
                'exact_item_name': 'clothing item',
                'color': 'multicolor',
                'pattern': 'solid',
                'fabric_type': 'fabric',
                'style': 'casual',
                'fit': 'regular',
                'tags': ['clothing'],
                'item_type': 'upperwear',
                'confidence': 5
            }]

# Helper function for quick background color preview
def get_color_preview_data():
    """Return color mapping data for frontend preview"""
    return {
        'white': {'bg': '#2D3748', 'name': 'Dark Slate'},
        'black': {'bg': '#F7FAFC', 'name': 'Light Gray'},
        'red': {'bg': '#DCFCE7', 'name': 'Light Mint'},
        'blue': {'bg': '#FFF7ED', 'name': 'Light Peach'},
        'green': {'bg': '#FEF2F2', 'name': 'Light Rose'},
        'yellow': {'bg': '#4338CA', 'name': 'Deep Indigo'},
        'pink': {'bg': '#22C55E', 'name': 'Fresh Green'},
        'purple': {'bg': '#FCD34D', 'name': 'Warm Yellow'},
        'orange': {'bg': '#2563EB', 'name': 'Rich Blue'},
        'brown': {'bg': '#DBEAFE', 'name': 'Light Blue'}
    }