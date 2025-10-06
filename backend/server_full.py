from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
import bcrypt
import base64
import asyncio
import openai
import json
from image_processor import ClothingImageProcessor


load_dotenv()

# Simplified configuration

# MongoDB connection - handle both local and Atlas environments
mongo_url = os.environ.get('MONGO_URL', os.environ.get('MONGODB_URI', 'mongodb://localhost:27017'))
db_name = os.environ.get('DB_NAME', os.environ.get('MONGODB_DB_NAME', 'ai_stylist'))

# Configure MongoDB client with Atlas-compatible settings
client = AsyncIOMotorClient(
    mongo_url,
    maxPoolSize=50,
    minPoolSize=5,
    serverSelectionTimeoutMS=5000,
    socketTimeoutMS=20000,
    connectTimeoutMS=20000,
    retryWrites=True
)
db = client[db_name]

# Security
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-this')
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initialize image processor
image_processor = ClothingImageProcessor(openai_client)

# Create the main app
app = FastAPI(title="AI Stylist API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class UserRegister(BaseModel):
    email: str
    password: str
    name: str
    gender: Optional[str] = None
    city: Optional[str] = None
    language: str = "english"
    age: Optional[int] = None
    profession: Optional[str] = None
    body_shape: Optional[str] = None
    skin_tone: Optional[str] = None
    style_inspiration: List[str] = Field(default_factory=list)
    style_vibes: List[str] = Field(default_factory=list)
    style_message: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    gender: Optional[str] = None
    city: Optional[str] = None
    language: str = "english"
    age: Optional[int] = None
    profession: Optional[str] = None
    body_shape: Optional[str] = None
    skin_tone: Optional[str] = None
    style_inspiration: List[str] = Field(default_factory=list)
    style_vibes: List[str] = Field(default_factory=list)
    style_message: Optional[str] = None
    onboarding_completed: bool = False
    created_at: datetime

class OnboardingData(BaseModel):
    age: Optional[int] = None
    profession: Optional[str] = None
    body_shape: Optional[str] = None
    skin_tone: Optional[str] = None
    style_inspiration: List[str] = Field(default_factory=list)
    style_vibes: List[str] = Field(default_factory=list)
    style_message: Optional[str] = None

class WardrobeItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    image_base64: str
    category: Optional[str] = None
    exact_item_name: Optional[str] = None
    color: Optional[str] = None
    pattern: Optional[str] = None
    fabric_type: Optional[str] = None
    style: Optional[str] = None
    fit: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_worn: Optional[datetime] = None

class WardrobeItemCreate(BaseModel):
    image_base64: str
    manual_tags: List[str] = Field(default_factory=list)

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    is_user: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    image_base64: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    image_base64: Optional[str] = None

class OutfitValidation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    image_base64: str
    scores: Dict[str, int] = Field(default_factory=dict)
    overall_score: float
    feedback: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OutfitValidationCreate(BaseModel):
    image_base64: str

class StyledLook(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    items: List[str]
    occasion: Optional[str] = None
    season: Optional[str] = None
    style_vibe: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=['HS256'])
        user_id = payload.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def analyze_garment_with_ai(image_base64: str) -> Dict[str, Any]:
    """Analyze garment image using OpenAI Vision API with enhanced prompting"""
    try:
        # Clean and prepare image data
        clean_base64 = image_base64
        if image_base64.startswith('data:image'):
            clean_base64 = image_base64.split(',')[1]
        
        # Create the image URL for OpenAI Vision API
        image_url = f"data:image/jpeg;base64,{clean_base64}"
        
        # Call OpenAI Vision API directly
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert fashion stylist and clothing analyst. Analyze garments with precision and provide detailed information.

For clothing items, identify:
- Specific category (t-shirt, button-down shirt, jeans, dress pants, sweater, dress, skirt, etc.)
- Exact item name with descriptive details
- Primary color and any accent colors
- Pattern type (solid, striped, floral, plaid, etc.)
- Fabric material when visible (cotton, denim, silk, wool, etc.)
- Style classification (casual, formal, business, trendy, vintage, etc.)
- Fit type (slim, regular, loose, oversized, fitted, etc.)
- Descriptive tags

Respond ONLY in valid JSON format:
{
  "category": "specific garment type",
  "exact_item_name": "detailed item description",
  "color": "primary color",
  "pattern": "pattern type",
  "fabric_type": "fabric material",
  "style": "style category",
  "fit": "fit type",
  "tags": ["descriptive", "tags"]
}

Be specific and accurate. No explanations outside JSON."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this clothing item in detail. Identify the specific garment type, color, fabric, style, and provide comprehensive fashion analysis in JSON format."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        
        try:
            # Clean response
            clean_response = ai_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response.replace('```json', '').replace('```', '').strip()
            elif clean_response.startswith('```'):
                clean_response = clean_response.replace('```', '').strip()
            
            analysis = json.loads(clean_response)
            
            # Ensure all required fields with meaningful defaults
            final_analysis = {
                'category': analysis.get('category', 'garment'),
                'exact_item_name': analysis.get('exact_item_name', analysis.get('category', 'clothing item')),
                'color': analysis.get('color', 'multicolor'),
                'pattern': analysis.get('pattern', 'solid'),
                'fabric_type': analysis.get('fabric_type', 'fabric'),
                'style': analysis.get('style', 'casual'),
                'fit': analysis.get('fit', 'regular'),
                'tags': analysis.get('tags', ['clothing'])
            }
            
            logging.info(f"AI Analysis Success: {final_analysis}")
            return final_analysis
            
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {str(e)}, Response: {ai_response}")
            return create_fallback_analysis()
        
    except Exception as e:
        logging.error(f"Error analyzing garment with OpenAI: {str(e)}")
        return create_fallback_analysis()

def create_fallback_analysis():
    return {
        "category": "garment",
        "exact_item_name": "clothing item",
        "color": "multicolor",
        "pattern": "solid",
        "fabric_type": "fabric",
        "style": "casual",
        "fit": "regular",
        "tags": ["clothing"]
    }

async def get_styling_advice(user_id: str, message: str, image_base64: Optional[str] = None) -> str:
    """Get styling advice using OpenAI with enhanced personality"""
    try:
        # Get user profile for personalization
        user = await db.users.find_one({"id": user_id})
        if not user:
            return "Hey! I need to know more about you first. Let's complete your style profile together!"
        
        # Get user's wardrobe for context
        wardrobe_items = await db.wardrobe.find({"user_id": user_id}).to_list(50)
        wardrobe_context = []
        for item in wardrobe_items:
            exact_name = item.get('exact_item_name', item.get('category', 'item'))
            color = item.get('color', 'unknown color')
            fabric = item.get('fabric_type', '')
            style = item.get('style', '')
            wardrobe_context.append(f"• {exact_name} in {color}" + (f", {fabric}" if fabric else "") + (f" ({style})" if style else ""))
        
        wardrobe_text = "\n".join(wardrobe_context) if wardrobe_context else "No wardrobe items uploaded yet - let's start building your digital closet!"
        
        # Build user personality context
        personality_context = f"""USER PROFILE:
- Name: {user.get('name', 'Friend')}
- Age: {user.get('age', 'Not specified')}
- Location: {user.get('city', 'Not specified')} 
- Profession: {user.get('profession', 'Not specified')}
- Body Shape: {user.get('body_shape', 'Not specified')}
- Skin Tone: {user.get('skin_tone', 'Not specified')}
- Style Inspiration: {', '.join(user.get('style_inspiration', []) or ['Personal style in development'])}
- Style Vibes: {', '.join(user.get('style_vibes', []) or ['Exploring different vibes'])}
- Style Message: {user.get('style_message', 'Developing their unique voice')}

WARDROBE INVENTORY:
{wardrobe_text}"""
        
        system_message = f"""You are Maya, a friendly and knowledgeable fashion stylist with a warm, conversational personality. You're like that stylish friend who always knows what looks great and makes fashion fun and accessible.

{personality_context}

PERSONALITY GUIDELINES:
✨ Be conversational, warm, and encouraging - like chatting with a stylish friend
✨ Reference current trends and cultural moments (Met Gala looks, street style, celebrity fashion when relevant)
✨ Use the user's personal info to make advice specific to their lifestyle, location, and body type
✨ Ask follow-up questions to understand their needs better
✨ Give practical, solution-focused advice without jargon
✨ Reference their existing wardrobe items specifically when making suggestions
✨ Be subtly educational about styling principles without being preachy
✨ Include cultural context and references that feel natural and current

RESPONSE STYLE:
- Keep responses conversational and engaging (not bullet points unless specifically needed)
- Reference the user's profile details naturally in conversation
- Mention specific wardrobe items they own when relevant
- Include fashion references (trends, celebrities, street style) when appropriate
- Always end with an engaging question or suggestion to continue the conversation

Remember: You're not just giving fashion advice, you're building confidence and helping them express their personality through style!"""
        
        # Prepare messages for OpenAI
        messages = [{"role": "system", "content": system_message}]
        
        # Handle image if provided
        if image_base64:
            try:
                # Clean base64 data and detect format properly
                clean_base64 = image_base64
                image_format = "jpeg"  # default
                
                if image_base64.startswith('data:image/'):
                    # Extract format from data URL
                    format_part = image_base64.split(',')[0]
                    if 'png' in format_part.lower():
                        image_format = "png"
                    elif 'webp' in format_part.lower():
                        image_format = "webp"
                    elif 'gif' in format_part.lower():
                        image_format = "gif"
                    else:
                        image_format = "jpeg"
                    clean_base64 = image_base64.split(',')[1]
                
                # Validate base64 and convert if needed
                try:
                    # Test if base64 is valid by trying to decode it
                    import base64
                    from PIL import Image
                    import io
                    
                    image_data = base64.b64decode(clean_base64)
                    test_image = Image.open(io.BytesIO(image_data))
                    
                    # Convert to JPEG if it's not a supported format for OpenAI
                    if test_image.format not in ['PNG', 'JPEG', 'WEBP', 'GIF']:
                        # Convert to JPEG
                        if test_image.mode in ['RGBA', 'LA']:
                            # Add white background for transparent images
                            background = Image.new('RGB', test_image.size, (255, 255, 255))
                            background.paste(test_image, mask=test_image.split()[-1] if test_image.mode == 'RGBA' else None)
                            test_image = background
                        elif test_image.mode != 'RGB':
                            test_image = test_image.convert('RGB')
                        
                        # Save as JPEG
                        output_buffer = io.BytesIO()
                        test_image.save(output_buffer, format='JPEG', quality=85)
                        clean_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
                        image_format = "jpeg"
                    
                    logging.info(f"Chat image processed: format={image_format}, size={test_image.size}, base64_length={len(clean_base64)}")
                    
                except Exception as img_error:
                    logging.error(f"Error processing chat image: {img_error}")
                    # Try with original format
                    pass
                
                # Ensure proper format for OpenAI Vision API
                image_url = f"data:image/{image_format};base64,{clean_base64}"
                
            except Exception as e:
                logging.error(f"Error preparing chat image: {e}")
                image_url = f"data:image/jpeg;base64,{clean_base64}"
            
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            })
        else:
            messages.append({
                "role": "user",
                "content": message
            })
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=800
        )
        
        ai_response = response.choices[0].message.content
        logging.info(f"Chat AI Response Success: {len(ai_response)} characters")
        return ai_response
        
    except Exception as e:
        logging.error(f"Error getting styling advice with OpenAI: {str(e)}")
        return "I'm having trouble analyzing your image right now, but I'm still here to help with styling advice! Can you describe what you're wearing or what you need help with?"

# Routes
@app.post("/api/auth/register")
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password": hashed_password,
        "name": user_data.name,
        "gender": user_data.gender,
        "city": user_data.city,
        "language": user_data.language,
        "age": user_data.age,
        "profession": user_data.profession,
        "body_shape": user_data.body_shape,
        "skin_tone": user_data.skin_tone,
        "style_inspiration": user_data.style_inspiration,
        "style_vibes": user_data.style_vibes,
        "style_message": user_data.style_message,
        "onboarding_completed": False,
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id)
    return {"token": token, "user": UserProfile(**user_doc)}

@app.post("/api/auth/login")
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"])
    return {"token": token, "user": UserProfile(**user)}

@app.get("/api/auth/me", response_model=UserProfile)
async def get_profile(user_id: str = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(**user)

@app.put("/api/auth/onboarding", response_model=UserProfile)
async def complete_onboarding(onboarding_data: OnboardingData, user_id: str = Depends(get_current_user)):
    update_data = onboarding_data.dict(exclude_unset=True)
    update_data["onboarding_completed"] = True
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = await db.users.find_one({"id": user_id})
    return UserProfile(**user)

@app.post("/api/wardrobe")
async def add_wardrobe_items(item_data: WardrobeItemCreate, user_id: str = Depends(get_current_user)):
    """
    Enhanced wardrobe upload with multi-item detection and advanced image processing
    Returns multiple items if multiple clothing pieces are detected
    """
    try:
        # Extract and process all clothing items from the image
        processed_items = await image_processor.extract_and_process_items(item_data.image_base64)
        
        added_items = []
        
        for item_info in processed_items:
            # Combine AI tags with manual tags
            all_tags = list(set(item_info.get('tags', []) + item_data.manual_tags))
            
            # Create wardrobe item with processed image and enhanced fields
            wardrobe_item = WardrobeItem(
                user_id=user_id,
                image_base64=item_info['image_base64'],  # This is the processed image with background
                category=item_info.get('category'),
                exact_item_name=item_info.get('exact_item_name'),
                color=item_info.get('color'),
                pattern=item_info.get('pattern'),
                fabric_type=item_info.get('fabric_type'),
                style=item_info.get('style'),
                fit=item_info.get('fit'),
                tags=all_tags
            )
            
            await db.wardrobe.insert_one(wardrobe_item.dict())
            added_items.append(wardrobe_item)
        
        logging.info(f"Successfully added {len(added_items)} items to wardrobe")
        
        # Return summary of added items
        return {
            "success": True,
            "items_added": len(added_items),
            "items": [item.dict() for item in added_items],
            "message": f"Successfully processed and added {len(added_items)} clothing item(s) to your wardrobe"
        }
        
    except Exception as e:
        logging.error(f"Error adding wardrobe items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process and add wardrobe items: {str(e)}")

@app.get("/api/wardrobe", response_model=List[WardrobeItem])
async def get_wardrobe(user_id: str = Depends(get_current_user)):
    items = await db.wardrobe.find({"user_id": user_id}).to_list(100)
    return [WardrobeItem(**item) for item in items]

@app.get("/api/wardrobe/categories")
async def get_wardrobe_categories(user_id: str = Depends(get_current_user)):
    """Get wardrobe items organized by category"""
    items = await db.wardrobe.find({"user_id": user_id}).to_list(100)
    
    categories = {}
    for item in items:
        category = item.get('category', 'Other')
        if category not in categories:
            categories[category] = []
        categories[category].append(WardrobeItem(**item))
    
    return categories

@app.delete("/api/wardrobe/{item_id}")
async def delete_wardrobe_item(item_id: str, user_id: str = Depends(get_current_user)):
    result = await db.wardrobe.delete_one({"id": item_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}

@app.post("/api/chat", response_model=ChatMessage)
async def chat_with_stylist(chat_request: ChatRequest, user_id: str = Depends(get_current_user)):
    # Save user message
    user_message = ChatMessage(
        user_id=user_id,
        message=chat_request.message,
        is_user=True,
        image_base64=chat_request.image_base64
    )
    await db.chat_messages.insert_one(user_message.dict())
    
    # Get AI response
    ai_response = await get_styling_advice(user_id, chat_request.message, chat_request.image_base64)
    
    # Save AI message
    ai_message = ChatMessage(
        user_id=user_id,
        message=ai_response,
        is_user=False
    )
    await db.chat_messages.insert_one(ai_message.dict())
    
    return ai_message

@app.get("/api/chat/history", response_model=List[ChatMessage])
async def get_chat_history(user_id: str = Depends(get_current_user)):
    messages = await db.chat_messages.find({"user_id": user_id}).sort("timestamp", 1).to_list(100)
    return [ChatMessage(**msg) for msg in messages]

@app.delete("/api/chat/clear")
async def clear_chat_history(user_id: str = Depends(get_current_user)):
    """Clear all chat history for user"""
    result = await db.chat_messages.delete_many({"user_id": user_id})
    return {"message": f"Cleared {result.deleted_count} messages"}

# Health check endpoint for deployment
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    try:
        # Test database connection
        await db.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Outfit validation endpoint with Emergent LLM
@app.post("/api/validate-outfit", response_model=OutfitValidation)
async def validate_outfit(validation_data: OutfitValidationCreate, user_id: str = Depends(get_current_user)):
    try:
        # Get user profile for context
        user = await db.users.find_one({"id": user_id})
        
        # Clean image data
        image_base64 = validation_data.image_base64
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',')[1]
        
        # Create image URL for OpenAI Vision API
        image_url = f"data:image/jpeg;base64,{image_base64}"
        
        # Create AI validation using OpenAI Vision API
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are Maya, a professional fashion stylist with expertise in high-end fashion houses. Provide precise, authoritative outfit validation with these 4 metrics (scored 1-5):

1. Color Combination: Evaluate harmony, contrast, and color theory application
2. Fit & Silhouette: Assess garment fit, proportions, and body flattery
3. Style Consistency: Analyze cohesive aesthetic and style narrative
4. Occasion Appropriateness: Judge suitability for setting and context

USER: {user.get('name', 'Client')} - {user.get('profession', 'Professional')} in {user.get('city', 'their city')}

FEEDBACK GUIDELINES:
- Be direct and professional, not overly friendly
- Use fashion industry terminology
- Provide specific, actionable advice
- Focus on technical aspects: silhouette, proportions, color theory
- Avoid excessive praise - be honest and constructive
- Reference current trends when relevant
- Keep feedback concise but informative (2-3 sentences)

Respond in JSON format: {{"color_combo": score, "fit": score, "style": score, "occasion": score, "overall_score": average, "feedback": "professional assessment"}}"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please validate this outfit and provide scores on the 4 parameters with constructive feedback."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            max_tokens=600
        )
        
        # Parse AI response
        ai_response = response.choices[0].message.content
        
        try:
            # Clean response - remove any markdown formatting
            clean_response = ai_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response.replace('```json', '').replace('```', '').strip()
            elif clean_response.startswith('```'):
                clean_response = clean_response.replace('```', '').strip()
            
            validation_result = json.loads(clean_response)
            
            # Ensure all scores are valid (1-5)
            for key in ['color_combo', 'fit', 'style', 'occasion']:
                if key in validation_result:
                    validation_result[key] = max(1, min(5, validation_result[key]))
            
            # Calculate overall score
            scores = [validation_result.get(key, 3) for key in ['color_combo', 'fit', 'style', 'occasion']]
            validation_result['overall_score'] = round(sum(scores) / len(scores), 1)
            
        except json.JSONDecodeError as e:
            logging.error(f"Validation JSON decode error: {str(e)}, Response: {ai_response}")
            validation_result = {
                "color_combo": 3,
                "fit": 3,
                "style": 3, 
                "occasion": 3,
                "overall_score": 3.0,
                "feedback": "Looking stylish! Your outfit has great potential. Keep experimenting with different combinations to find what makes you feel most confident!"
            }
        
        # Create validation record
        validation = OutfitValidation(
            user_id=user_id,
            image_base64=image_base64,
            scores={
                "color_combo": validation_result.get("color_combo", 3),
                "fit": validation_result.get("fit", 3),
                "style": validation_result.get("style", 3),
                "occasion": validation_result.get("occasion", 3)
            },
            overall_score=validation_result.get("overall_score", 3.0),
            feedback=validation_result.get("feedback", "Great outfit!")
        )
        
        await db.outfit_validations.insert_one(validation.dict())
        return validation
        
    except Exception as e:
        logging.error(f"Error validating outfit: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate outfit")

# Styled looks endpoints
@app.get("/api/styled-looks", response_model=List[StyledLook])
async def get_styled_looks(user_id: str = Depends(get_current_user)):
    looks = await db.styled_looks.find({"user_id": user_id}).to_list(50)
    return [StyledLook(**look) for look in looks]

@app.post("/api/styled-looks/generate")
async def generate_styled_looks(user_id: str = Depends(get_current_user)):
    try:
        # Get user wardrobe
        wardrobe_items = await db.wardrobe.find({"user_id": user_id}).to_list(100)
        
        if len(wardrobe_items) < 3:
            return {"message": "Add more items to your wardrobe to generate styled looks!"}
        
        # Get user profile for context
        user = await db.users.find_one({"id": user_id})
        
        # Build wardrobe context
        wardrobe_context = []
        for item in wardrobe_items:
            item_desc = f"{item.get('id')}: {item.get('exact_item_name', item.get('category'))}, {item.get('color')}, {item.get('style')}"
            wardrobe_context.append(item_desc)
        
        # Generate looks with OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are Maya, a fashion stylist creating outfit combinations from the user's wardrobe.

USER: {user.get('name')} - {user.get('profession')} in {user.get('city')}
STYLE VIBES: {', '.join(user.get('style_vibes', []))}

WARDROBE ITEMS:
{chr(10).join(wardrobe_context)}

Create 5-8 complete outfit combinations using different wardrobe items. Mix and match for various occasions.
Respond in JSON format: {{"looks": [{{"name": "outfit name", "items": ["item_id1", "item_id2"], "occasion": "casual/work/date", "season": "spring/summer/fall/winter", "style_vibe": "style description"}}]}}"""
                },
                {
                    "role": "user",
                    "content": "Generate styled looks from my wardrobe items."
                }
            ],
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        # Parse response
        try:
            looks_data = json.loads(ai_response)
            generated_looks = looks_data.get("looks", [])
        except:
            generated_looks = []
        
        # Save generated looks
        saved_count = 0
        for look_data in generated_looks:
            styled_look = StyledLook(
                user_id=user_id,
                name=look_data.get("name", f"Look {saved_count + 1}"),
                items=look_data.get("items", []),
                occasion=look_data.get("occasion"),
                season=look_data.get("season"),
                style_vibe=look_data.get("style_vibe")
            )
            await db.styled_looks.insert_one(styled_look.dict())
            saved_count += 1
        
        return {"message": f"Generated {saved_count} styled looks!", "count": saved_count}
        
    except Exception as e:
        logging.error(f"Error generating styled looks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate styled looks")

@app.get("/api/")
async def root():
    return {"message": "AI Stylist API is running"}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Production server startup - simplified for container deployment
if __name__ == "__main__":
    import uvicorn
    
    # Minimal configuration for container deployment
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8001))
    
    logger.info(f"Starting backend server on {host}:{port}")
    
    # Start with basic uvicorn configuration
    uvicorn.run(
        app,  # Use app object directly instead of string
        host=host,
        port=port,
        log_level="info"
    )
