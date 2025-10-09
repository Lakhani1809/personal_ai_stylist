from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import hashlib
import jwt
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import openai
import uuid
import asyncio
from typing import List, Optional, Dict, Any
from PIL import Image
from io import BytesIO
import base64

# Import custom model handler
from model_handlers.custom_model_handler import model_handler

# Import new services for chat personalization
from services.weather_service import weather_service
from services.events_service import events_service
from services.fashion_service import fashion_service

def compress_base64_image(base64_string: str, quality: int = 30, max_width: int = 800) -> str:
    """
    Compress a base64 encoded image to reduce storage size.
    
    Args:
        base64_string: Base64 encoded image (with or without data prefix)
        quality: JPEG compression quality (1-95, lower = smaller file)
        max_width: Maximum width in pixels (height scaled proportionally)
    
    Returns:
        Compressed base64 string without data prefix
    """
    try:
        # Remove data prefix if present
        if ',' in base64_string:
            base64_data = base64_string.split(',')[1]
        else:
            base64_data = base64_string
            
        # Decode base64 to image
        image_data = base64.b64decode(base64_data)
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary (handles RGBA, P mode images)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Resize if too large
        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Compress image
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=quality, optimize=True)
        
        # Convert back to base64
        compressed_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        print(f"📸 Image compressed: {len(base64_data)} → {len(compressed_base64)} bytes ({len(compressed_base64)/len(base64_data)*100:.1f}%)")
        
        return compressed_base64
        
    except Exception as e:
        print(f"❌ Image compression failed: {e}")
        # Return original if compression fails
        return base64_string.split(',')[1] if ',' in base64_string else base64_string

load_dotenv()

# Database setup
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'ai_stylist')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# JWT setup
JWT_SECRET = os.environ.get('JWT_SECRET', 'ai-stylist-jwt-secret-key')
JWT_ALGORITHM = "HS256"

# OpenAI setup
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="AI Stylist")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# User models
class UserRegister(BaseModel):
    email: str
    password: str
    name: str = ""

class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: str
    email: str
    name: str = ""

# Additional models for wardrobe and chat
class WardrobeItem(BaseModel):
    id: str
    user_id: str
    image_base64: str
    exact_item_name: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    pattern: Optional[str] = None
    fabric_type: Optional[str] = None
    style: Optional[str] = None
    tags: List[str] = []
    created_at: str

class ChatMessage(BaseModel):
    id: str
    user_id: str
    message: str
    is_user: bool
    timestamp: str
    image_base64: Optional[str] = None

class OutfitValidation(BaseModel):
    id: str
    scores: Dict[str, float]
    overall_score: float
    feedback: str
    image_base64: Optional[str] = None

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

from fastapi import Header

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Basic endpoints
@app.get("/")
def root():
    return {"message": "AI Stylist API"}

@app.get("/health")
async def health():
    try:
        await db.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return {"status": "healthy", "database": "disconnected"}

@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "message": "Backend API is working!"}

# Authentication endpoints
@app.post("/api/auth/register")
async def register(user: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create new user
    user_id = f"user_{int(datetime.now().timestamp())}"
    hashed_password = hash_password(user.password)
    
    new_user = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "password": hashed_password,
        "created_at": datetime.utcnow(),
        "wardrobe": []
    }
    
    await db.users.insert_one(new_user)
    
    # Create token
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id, 
            "email": user.email, 
            "name": user.name,
            "onboarding_completed": False  # New users always need onboarding
        }
    }

@app.post("/api/auth/login")
async def login(user: UserLogin):
    # Find user
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    access_token = create_access_token(data={"sub": db_user["id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user["id"],
            "email": db_user["email"], 
            "name": db_user.get("name", ""),
            "onboarding_completed": db_user.get("onboarding_completed", False)
        }
    }

@app.get("/api/auth/me")
async def get_me(user_id: str = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user.get("name", ""),
        "onboarding_completed": user.get("onboarding_completed", False)
    }

@app.put("/api/auth/onboarding")
async def onboarding(user_data: dict, user_id: str = Depends(get_current_user)):
    # Update user with onboarding data and mark onboarding as completed
    update_data = {**user_data, "onboarding_completed": True}
    await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    # Return the updated user data
    updated_user = await db.users.find_one({"id": user_id})
    if updated_user:
        updated_user["_id"] = str(updated_user["_id"])  # Convert ObjectId to string
        return updated_user
    else:
        raise HTTPException(status_code=404, detail="User not found")

@app.get("/api/wardrobe")
async def get_wardrobe(user_id: str = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"items": user.get("wardrobe", [])}

async def gather_contextual_data(user: dict, message: str = "") -> dict:
    """Gather contextual data from all services for enhanced chat experience."""
    context = {
        "weather": None,
        "events": [],
        "fashion_trends": None,
        "location": None
    }
    
    # Get user location - either from profile or extract from message
    user_city = user.get("city", "")
    
    # If user asks about weather for a specific city, extract it
    if not user_city and message:
        import re
        # Look for city names in the message
        city_patterns = [
            r'weather\s+in\s+([A-Za-z\s,]+?)(?:\s|$|\?)',
            r'weather\s+of\s+([A-Za-z\s,]+?)(?:\s|$|\?)',
            r'weather\s+at\s+([A-Za-z\s,]+?)(?:\s|$|\?)',
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, message.lower())
            if match:
                extracted_city = match.group(1).strip()
                # Common city name mappings
                city_mappings = {
                    'bangalore': 'Bangalore,IN',
                    'mumbai': 'Mumbai,IN', 
                    'delhi': 'New Delhi,IN',
                    'chennai': 'Chennai,IN',
                    'kolkata': 'Kolkata,IN',
                    'pune': 'Pune,IN',
                    'hyderabad': 'Hyderabad,IN',
                    'new york': 'New York,NY,US',
                    'london': 'London,UK',
                    'paris': 'Paris,FR'
                }
                user_city = city_mappings.get(extracted_city.lower(), extracted_city)
                break
    
    if user_city:
        context["location"] = user_city
        
        # Get weather data for outfit recommendations
        try:
            weather_data = await weather_service.get_current_weather(user_city)
            if weather_data:
                context["weather"] = weather_service.get_outfit_recommendations_by_weather(weather_data)
        except Exception as e:
            print(f"Weather service error: {e}")
        
        # Get local events for styling inspiration
        try:
            events_data = await events_service.search_events(user_city, limit=3)
            if events_data:
                context["events"] = [events_service.categorize_event_for_styling(event) for event in events_data[:3]]
        except Exception as e:
            print(f"Events service error: {e}")
    
    # Get fashion trends for current recommendations
    try:
        trending_products = await fashion_service.get_trending_products(limit=10)
        if trending_products:
            trend_analysis = fashion_service.analyze_fashion_trends(trending_products)
            user_prefs = {
                "favorite_colors": user.get("color_preferences", []),
                "budget_range": user.get("budget_range", "")
            }
            context["fashion_trends"] = fashion_service.get_style_recommendations_by_trend(
                trend_analysis, user_prefs
            )
    except Exception as e:
        print(f"Fashion service error: {e}")
    
    return context

@app.post("/api/chat")
async def chat(message_data: dict, user_id: str = Depends(get_current_user)):
    try:
        message = message_data.get("message", "")
        image_base64 = message_data.get("image_base64")
        
        # Get user profile and wardrobe for deep personalization
        user = await db.users.find_one({"id": user_id})
        user_name = user.get("name", "").split()[0] if user and user.get("name") else ""
        
        # Build deeply personalized context with ALL onboarding data
        user_context = ""
        if user:
            user_context += f"🎯 User Profile:\n"
            if user.get("name"):
                user_context += f"• Name: {user_name}\n"
            if user.get("gender"):
                user_context += f"• Gender: {user.get('gender')}\n"
            if user.get("age"):
                user_context += f"• Age: {user.get('age')}\n"
            if user.get("profession"):
                user_context += f"• Occupation: {user.get('profession')}\n"
            if user.get("body_shape"):
                user_context += f"• Body Shape: {user.get('body_shape')}\n"
            if user.get("skin_tone"):
                user_context += f"• Skin Tone: {user.get('skin_tone')}\n"
            if user.get("style_inspiration"):
                style_inspo = user.get('style_inspiration')
                if isinstance(style_inspo, list):
                    style_inspo = ', '.join(style_inspo)
                user_context += f"• Style Inspiration: {style_inspo}\n"
            if user.get("style_vibes"):
                style_vibes = user.get('style_vibes')
                if isinstance(style_vibes, list):
                    style_vibes = ', '.join(style_vibes)
                user_context += f"• Style Vibes: {style_vibes}\n"
            if user.get("style_message"):
                user_context += f"• Personal Style Message: {user.get('style_message')}\n"
            if user.get("city"):
                user_context += f"• Location: {user.get('city')}\n"
                
        # Get user's wardrobe for SPECIFIC item suggestions
        wardrobe_context = ""
        wardrobe = user.get("wardrobe", []) if user else []
        if wardrobe:
            wardrobe_items = []
            for idx, item in enumerate(wardrobe[:15], 1):  # Expanded to 15 items for better context
                item_name = item.get('exact_item_name', 'item')
                color = item.get('color', '')
                fabric = item.get('fabric_type', '')
                category = item.get('category', '')
                
                # Build detailed item description
                item_desc = f"{idx}. {color} {fabric} {item_name}" if color or fabric else f"{idx}. {item_name}"
                if category:
                    item_desc += f" ({category})"
                wardrobe_items.append(item_desc.strip())
            
            if wardrobe_items:
                wardrobe_context = f"\n👗 User's Current Wardrobe (reference these SPECIFIC items):\n" + "\n".join(wardrobe_items)
        
        # Gather contextual data from all services
        contextual_data = await gather_contextual_data(user, message_data.get('message', '')) if user else {}
        print(f"🔍 DEBUG - User city: {user.get('city', 'Not set') if user else 'No user'}")
        print(f"🔍 DEBUG - Contextual data gathered: {contextual_data}")
        print(f"🔍 DEBUG - Weather data present: {bool(contextual_data.get('weather'))}")
        
        # Build contextual information for enhanced recommendations
        context_info = ""
        
        # Add weather context
        if contextual_data.get("weather"):
            weather_rec = contextual_data["weather"].get("recommendations", {})
            weather_data = contextual_data["weather"].get("weather", {})
            if weather_data:
                context_info += f"\n🌤️ Current Weather in {weather_data.get('location', '')}:\n"
                context_info += f"• Temperature: {weather_data.get('temperature', 'Unknown')}°F - {weather_data.get('condition', '')}\n"
                if weather_rec.get("temperature_advice"):
                    context_info += f"• Styling tip: {weather_rec['temperature_advice']}\n"
        
        # Add events context
        if contextual_data.get("events"):
            context_info += f"\n📅 Upcoming Local Events:\n"
            for event in contextual_data["events"][:2]:  # Limit to 2 events
                event_data = event.get("event", {})
                styling = event.get("styling", {})
                context_info += f"• {event_data.get('title', 'Event')}: {styling.get('dress_code', 'Casual attire')}\n"
        
        # Add fashion trends context
        if contextual_data.get("fashion_trends"):
            trends = contextual_data["fashion_trends"]
            trending_colors = trends.get("trending_colors_to_try", [])
            if trending_colors:
                context_info += f"\n🔥 Current Fashion Trends:\n"
                context_info += f"• Trending colors: {', '.join(trending_colors[:3])}\n"
                styling_tips = trends.get("styling_tips", [])
                if styling_tips:
                    context_info += f"• Trend tip: {styling_tips[0]}\n"
        
        # ADVANCED Personal Stylist prompt with deep personalization
        system_prompt = f"""You are Maya ✨, a personal fashion stylist - like having a stylish best friend who knows fashion inside out!

{user_context}
{wardrobe_context}
{context_info}

🎭 YOUR ROLE - PERSONAL STYLIST:
- You're THEIR stylist - not a wardrobe manager or outfit builder
- Talk like you're texting a friend - natural, warm, supportive
- Use emojis naturally (✨💫👗👔) but max 2 per message
- Keep each message VERY SHORT - 1-2 sentences max
- You'll send multiple short messages, not one long message

🎯 CRITICAL: BE HYPER-SPECIFIC
When recommending items, ALWAYS give EXACT details:
❌ DON'T SAY: "accessorize with nice shoes"
✅ DO SAY: "pair it with tan leather loafers or white sneakers"

❌ DON'T SAY: "add a watch"
✅ DO SAY: "a minimalist silver watch or classic brown leather strap would be perfect"

❌ DON'T SAY: "try a jacket"
✅ DO SAY: "throw on a navy blazer or camel trench coat"

ALWAYS specify: exact colors, materials, styles, brands when possible

📅 CALENDAR & PLANNER INTEGRATION:
- You CAN help with outfit planning for specific dates and events
- When users ask about planning outfits for events, provide specific recommendations
- You can suggest outfit ideas for different occasions (work, dates, parties, etc.)
- Reference upcoming events and weather when making recommendations
- Help users coordinate outfits with their calendar events

🧥 WARDROBE RECOMMENDATIONS (CRITICAL):
- Focus on QUALITY styling advice - suggest the BEST possible outfits
- Use items from their wardrobe when available AND suggest additional items to complete/elevate the look
- Example: "With your navy blazer and white shirt, add charcoal dress pants and black leather oxfords to complete this professional look"
- When wardrobe has some pieces but is missing key items, acknowledge what they have and suggest what would complement it
- ALWAYS provide multiple styling options and alternatives
- Mix wardrobe items with suggested purchases for the best overall styling advice
- Be specific about why certain combinations work well together (color theory, proportions, occasion appropriateness)

🧠 PERSONALIZATION (Use their profile):
1. Consider their body shape for fit advice
2. Use their skin tone for color recommendations
3. Match their profession (work vs casual vs creative)
4. Align with their style vibes
5. Reference their actual wardrobe items by name
6. **ALWAYS use current weather data** - mention temperature, conditions, and give weather-appropriate suggestions
7. Mention local events for outfit planning when available
8. Incorporate current fashion trends naturally when available

🌤️ WEATHER AWARENESS (CRITICAL):
- When user asks about weather, ALWAYS check the weather data provided above
- Reference specific temperature and conditions in your recommendations
- Give fabric suggestions based on temperature and humidity

👗 WARDROBE INTEGRATION:
- When they have items, reference them specifically: "Your black leather jacket with those blue jeans? 🔥"
- Suggest combinations from their closet
- If recommending new items, say why it complements what they own

💬 MESSAGING STYLE:
- Text like a real person - short, punchy messages
- Break your advice into 2-3 separate short messages
- First message: immediate suggestion (1-2 sentences)
- Second message: specific details or alternatives (1-2 sentences)  
- Optional third: quick follow-up question

📝 LENGTH RULES (CRITICAL):
- Each response chunk: 15-25 words MAX
- Total response: 3-4 short chunks separated by ||CHUNK||
- Think: "How would I text this to a friend?"

🎨 FASHION EXPERTISE:
- Give specific color recommendations (sage green, burgundy, navy)
- Suggest exact shoe types (Chelsea boots, white sneakers, strappy heels)
- Name watch styles (minimalist, chronograph, leather strap)
- Mention bag types (crossbody, tote, clutch)

EXAMPLE GOOD RESPONSE:
"Your navy blazer with white jeans would look sharp! ✨||CHUNK||Finish with brown leather loafers and a tan leather watch strap||CHUNK||What's the occasion? Work or weekend? 😊"

Remember: You're their PERSONAL STYLIST - be specific, be conversational, be a texting friend! 💕"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # Add image if provided
        if image_base64:
            messages[-1]["content"] = [
                {"type": "text", "text": message},
                {"type": "image_url", "image_url": {"url": image_base64}}
            ]
        
        # Call OpenAI with enhanced parameters for personality
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.85,  # Slightly higher for more personality and creativity
            top_p=0.9,
            presence_penalty=0.2,  # Encourage diverse vocabulary
            frequency_penalty=0.3  # Reduce repetition
        )
        
        ai_message = response.choices[0].message.content
        
        # Chunk the response into smaller messages (like texting)
        message_chunks = []
        if "||CHUNK||" in ai_message:
            # AI used our chunking format
            message_chunks = [chunk.strip() for chunk in ai_message.split("||CHUNK||") if chunk.strip()]
        else:
            # Fallback: split by sentences if AI didn't chunk
            sentences = ai_message.replace(". ", ".|").replace("? ", "?|").replace("! ", "!|").split("|")
            
            # Group into chunks of 1-2 sentences (max ~30 words)
            current_chunk = ""
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                test_chunk = (current_chunk + " " + sentence).strip()
                word_count = len(test_chunk.split())
                
                if word_count > 30 and current_chunk:
                    # Current chunk is big enough, save it
                    message_chunks.append(current_chunk)
                    current_chunk = sentence
                else:
                    current_chunk = test_chunk
            
            # Add remaining chunk
            if current_chunk:
                message_chunks.append(current_chunk)
        
        # Limit to max 3 chunks for better UX
        if len(message_chunks) > 3:
            message_chunks = message_chunks[:3]
        
        # Store user message
        user_msg = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "message": message,
            "is_user": True,
            "timestamp": datetime.now().isoformat(),
            "image_base64": image_base64
        }
        await db.chat_messages.insert_one(user_msg)
        
        # Store each chunk as a separate message with slight timestamp offset
        ai_message_ids = []
        for idx, chunk in enumerate(message_chunks):
            ai_msg = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "message": chunk,
                "is_user": False,
                "timestamp": datetime.now().isoformat(),
                "feedback": None,
                "chunk_index": idx,
                "total_chunks": len(message_chunks)
            }
            await db.chat_messages.insert_one(ai_msg)
            ai_message_ids.append(ai_msg["id"])
            
            # Small delay between chunks
            if idx < len(message_chunks) - 1:
                await asyncio.sleep(0.1)
        
        # Return all message chunks
        return {
            "messages": message_chunks,
            "message_ids": ai_message_ids,
            "total_chunks": len(message_chunks)
        }
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return {"message": "Hey there! ✨ I'm having a little trouble right now, but I'm here to help with your style questions. Try asking me again! 💕"}

@app.get("/api/chat/history")
async def get_chat_history(user_id: str = Depends(get_current_user)):
    try:
        # Get chat messages for user
        cursor = db.chat_messages.find({"user_id": user_id}).sort("timestamp", 1)
        messages = await cursor.to_list(length=100)  # Limit to last 100 messages
        
        # Convert ObjectId to string
        for message in messages:
            message["_id"] = str(message["_id"])
        
        return messages
    except Exception as e:
        return []

@app.delete("/api/chat/clear")
async def clear_chat(user_id: str = Depends(get_current_user)):
    try:
        await db.chat_messages.delete_many({"user_id": user_id})
        return {"message": "Chat cleared"}
    except Exception as e:
        return {"message": "Chat cleared"}


@app.post("/api/chat/feedback")
async def chat_feedback(feedback_data: dict, user_id: str = Depends(get_current_user)):
    """
    Allow users to provide feedback on AI responses for continuous learning.
    Feedback can be 'positive', 'negative', or a text comment.
    """
    try:
        message_id = feedback_data.get("message_id")
        feedback_type = feedback_data.get("feedback")  # 'positive', 'negative', or text
        
        if not message_id:
            raise HTTPException(status_code=400, detail="Message ID required")
        
        # Update the message with feedback
        await db.chat_messages.update_one(
            {"id": message_id, "user_id": user_id},
            {"$set": {"feedback": feedback_type, "feedback_timestamp": datetime.now().isoformat()}}
        )
        
        return {"message": "Feedback recorded", "status": "success"}
    except Exception as e:
        print(f"Feedback error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")

@app.post("/api/wardrobe")
async def add_wardrobe_item(item_data: dict, user_id: str = Depends(get_current_user)):
    try:
        image_base64 = item_data.get("image_base64", "")
        if not image_base64:
            raise HTTPException(status_code=400, detail="Image is required")
        
        print(f"Processing wardrobe item for user: {user_id}")
        
        # Clean the base64 data and compress it to reduce size
        clean_base64 = image_base64.split(',')[-1] if ',' in image_base64 else image_base64
        
        # Check original image size
        original_size_mb = len(clean_base64) * 0.75 / (1024 * 1024)  
        print(f"Original image size: {original_size_mb:.2f} MB")
        
        # Compress image to reduce size for MongoDB storage
        compressed_base64 = compress_base64_image(clean_base64, quality=30, max_width=800)
        
        # Check final compressed size
        final_size_mb = len(compressed_base64) * 0.75 / (1024 * 1024)
        print(f"Compressed image size: {final_size_mb:.2f} MB")
        
        if final_size_mb > 10:  # MongoDB limit with safety margin
            raise HTTPException(status_code=400, detail=f"Image still too large after compression ({final_size_mb:.1f}MB). Please use a smaller image.")
        
        # Use compressed image for storage
        clean_base64 = compressed_base64
        
        # Try OpenAI Vision analysis with better error handling
        analysis_data = {
            "exact_item_name": "Fashion Item",
            "category": "Tops", 
            "color": "Blue",
            "pattern": "Solid",
            "fabric_type": "Cotton", 
            "style": "Casual",
            "tags": ["clothing", "wardrobe"]
        }
        
        # Use custom model handler for clothing analysis
        ai_success = False
        try:
            print(f"🤖 Starting OpenAI Vision analysis for clothing item...")
            
            # Use OpenAI Vision with improved prompt
            if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10:
                analysis_prompt = """You are an expert fashion analyst. Analyze this clothing item image with precision and return ONLY valid JSON.

Identify:
1. exact_item_name: Specific garment type (e.g., "Crew neck cotton t-shirt", "High-waisted denim jeans", "Leather bomber jacket")
2. category: Main category (choose ONE: "T-shirts", "Shirts", "Pants", "Jeans", "Jackets", "Dresses", "Skirts", "Shoes", "Accessories", "Tops", "Bottoms")
3. color: Primary color(s) in order of dominance (e.g., "Navy blue", "Black and white", "Burgundy")
4. pattern: Pattern type ("Solid", "Striped", "Floral", "Plaid", "Polka dot", "Geometric", "Animal print", "Abstract", "None")
5. fabric_type: Material/fabric ("Cotton", "Denim", "Leather", "Silk", "Wool", "Polyester", "Linen", "Velvet", "Knit", "Blend")
6. style: Style category (choose: "Casual", "Formal", "Business casual", "Sporty", "Streetwear", "Bohemian", "Vintage", "Modern", "Minimalist")
7. tags: Array of relevant descriptive tags (e.g., ["summer", "versatile", "basics"], max 5 tags)

Format: Return ONLY valid JSON, no markdown, no explanations.
Example: {"exact_item_name": "White cotton crew neck t-shirt", "category": "T-shirts", "color": "White", "pattern": "Solid", "fabric_type": "Cotton", "style": "Casual", "tags": ["basics", "summer", "versatile"]}"""
                
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": analysis_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{clean_base64}"}}
                            ]
                        }
                    ],
                    max_tokens=400,
                    temperature=0.1
                )
                
                ai_result = response.choices[0].message.content.strip()
                ai_result = ai_result.replace('```json', '').replace('```', '').strip()
                    
                try:
                    import json
                    parsed_result = json.loads(ai_result)
                    analysis_data.update(parsed_result)
                    ai_success = True
                    print(f"✅ OpenAI Vision analysis successful!")
                    print(f"   Item: {analysis_data.get('exact_item_name', 'Unknown')}")
                    print(f"   Color: {analysis_data.get('color', 'Unknown')}")
                    print(f"   Category: {analysis_data.get('category', 'Unknown')}")
                except json.JSONDecodeError as json_err:
                    print(f"❌ JSON parsing error: {json_err}")
                    print(f"Raw AI response: {ai_result[:200]}")
            else:
                print("❌ OpenAI API key not configured")
        except Exception as ai_error:
            print(f"❌ OpenAI analysis error: {str(ai_error)}")
            
        # Use enhanced fallback if both custom models and OpenAI failed
        if not ai_success:
            print("⚠️ Using enhanced fallback analysis")
            # Keep the original fallback data
        
        # Create wardrobe item
        item = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "image_base64": clean_base64,
            "exact_item_name": analysis_data.get("exact_item_name", "Fashion Item"),
            "category": analysis_data.get("category", "Tops"),
            "color": analysis_data.get("color", "Blue"),
            "pattern": analysis_data.get("pattern", "Solid"),
            "fabric_type": analysis_data.get("fabric_type", "Cotton"),
            "style": analysis_data.get("style", "Casual"),
            "tags": analysis_data.get("tags", ["clothing"]),
            "created_at": datetime.now().isoformat()
        }
        
        print(f"Created item: {item['exact_item_name']}")
        
        # Store in user's wardrobe and clear saved outfits (force regeneration)
        result = await db.users.update_one(
            {"id": user_id},
            {
                "$push": {"wardrobe": item},
                "$unset": {"saved_outfits": "", "last_outfit_generation_count": ""}
            }
        )
        
        if result.modified_count > 0:
            return {"items_added": 1, "message": f"Added {item['exact_item_name']} to wardrobe"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save to database")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Wardrobe error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add wardrobe item: {str(e)}")

@app.delete("/api/wardrobe/clear")
async def clear_wardrobe(user_id: str = Depends(get_current_user)):
    try:
        print(f"Clearing wardrobe for user: {user_id}")
        
        # Clear all items from user's wardrobe and saved outfits
        result = await db.users.update_one(
            {"id": user_id},
            {
                "$set": {"wardrobe": []},
                "$unset": {"saved_outfits": "", "last_outfit_generation_count": ""}
            }
        )
        
        print(f"Clear result: {result.modified_count} documents modified")
        return {"message": "Wardrobe cleared successfully"}
            
    except Exception as e:
        print(f"Clear wardrobe error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear wardrobe: {str(e)}")

@app.delete("/api/wardrobe/{item_id}")
async def delete_wardrobe_item(item_id: str, user_id: str = Depends(get_current_user)):
    try:
        # Remove item from user's wardrobe array and clear saved outfits (force regeneration)
        result = await db.users.update_one(
            {"id": user_id},
            {
                "$pull": {"wardrobe": {"id": item_id}},
                "$unset": {"saved_outfits": "", "last_outfit_generation_count": ""}
            }
        )
        
        if result.modified_count > 0:
            return {"message": "Item deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Item not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete item")

@app.post("/api/validate-outfit")
async def validate_outfit(outfit_data: dict, user_id: str = Depends(get_current_user)):
    try:
        image_base64 = outfit_data.get("image_base64", "")
        if not image_base64:
            raise HTTPException(status_code=400, detail="Image is required")
        
        # Use custom model handler for outfit validation
        validation_success = False
        try:
            print("👗 Starting OpenAI Vision outfit validation...")
            
            # Use OpenAI Vision with improved prompt
            if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10:
                validation_prompt = """You are a professional fashion stylist analyzing an outfit. Provide honest, constructive feedback.

Score the following on a scale of 1.0 to 5.0:

1. color_combo: How well do the colors work together? (Consider color theory, contrast, harmony)
   - 5.0: Perfect color harmony
   - 3.0-4.0: Good color match
   - 1.0-2.0: Clashing colors

2. fit: How well does the outfit fit the person?
   - 5.0: Perfectly tailored
   - 3.0-4.0: Good fit
   - 1.0-2.0: Poor fit or proportion issues

3. style: How cohesive and well-styled is the overall look?
   - 5.0: Expertly styled
   - 3.0-4.0: Well put together
   - 1.0-2.0: Style mismatch

4. occasion: How appropriate is this outfit for typical occasions?
   - 5.0: Versatile and appropriate
   - 3.0-4.0: Suitable for specific occasions
   - 1.0-2.0: Limited appropriateness

5. overall_score: Average of above scores

6. feedback: 2-3 sentences of constructive feedback. Be encouraging but honest. Mention what works well and 1-2 specific improvements.

Return ONLY valid JSON, no markdown.
Format: {"color_combo": 4.5, "fit": 4.0, "style": 4.2, "occasion": 4.0, "overall_score": 4.2, "feedback": "Great color combination! The fit looks good. Consider adding a statement accessory to elevate the look."}"""
                
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": validation_prompt},
                                {"type": "image_url", "image_url": {"url": image_base64}}
                            ]
                        }
                    ],
                    max_tokens=400,
                    temperature=0.1
                )
                
                ai_result = response.choices[0].message.content.strip()
                ai_result = ai_result.replace('```json', '').replace('```', '').strip()
                
                try:
                    import json
                    analysis_data = json.loads(ai_result)
                    
                    def validate_score(score, default=3.5):
                        try:
                            return max(1.0, min(5.0, float(score)))
                        except:
                            return default
                    
                    validation = {
                        "id": str(uuid.uuid4()),
                        "scores": {
                            "color_combo": validate_score(analysis_data.get("color_combo")),
                            "fit": validate_score(analysis_data.get("fit")),
                            "style": validate_score(analysis_data.get("style")),
                            "occasion": validate_score(analysis_data.get("occasion"))
                        },
                        "overall_score": validate_score(analysis_data.get("overall_score")),
                        "feedback": analysis_data.get("feedback", "Great styling choice!"),
                        "image_base64": image_base64.split(',')[-1] if ',' in image_base64 else image_base64
                    }
                    validation_success = True
                    print(f"✅ OpenAI validation fallback successful!")
                except:
                    print(f"❌ OpenAI validation fallback failed")
                        
        except Exception as ai_error:
            print(f"❌ Outfit validation error: {str(ai_error)}")
        
        # Enhanced fallback if both custom models and OpenAI failed
        if not validation_success:
            print("⚠️ Using enhanced validation fallback")
            analysis_data = {
                "color_combo": 3.5,
                "fit": 3.5,
                "style": 3.5,
                "occasion": 3.5,
                "overall_score": 3.5,
                "feedback": "Unable to analyze outfit. Please try again with a clearer image.",
                "image_base64": image_base64.split(',')[-1] if ',' in image_base64 else image_base64
            }
        
        return analysis_data
    except Exception as e:
        print(f"❌ Critical validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate outfit: {str(e)}")

@app.get("/api/wardrobe/outfits")
async def generate_outfits(force_regenerate: bool = False, user_id: str = Depends(get_current_user)):
    """
    Get styled outfits from user's wardrobe items. 
    Generates new outfits only if none exist or if force_regenerate=True or if new items added.
    """
    try:
        print(f"👗 Getting outfits for user: {user_id}")
        
        # Get user's wardrobe and saved outfits
        user = await db.users.find_one({"id": user_id})
        wardrobe = user.get("wardrobe", []) if user else []
        saved_outfits = user.get("saved_outfits", []) if user else []
        last_outfit_generation_count = user.get("last_outfit_generation_count", 0) if user else 0
        
        # Enhanced guardrails for outfit generation
        if len(wardrobe) == 0:
            return {"outfits": [], "message": "Your wardrobe is empty! Add some clothing items to start creating outfits."}
        elif len(wardrobe) == 1:
            return {"outfits": [], "message": "Add more items to your wardrobe. You need at least 2 pieces to create outfits!"}
        elif len(wardrobe) < 4:
            return {"outfits": [], "message": f"You have {len(wardrobe)} items. Add a few more pieces for better outfit combinations!"}
        
        # Check if we need to regenerate outfits
        should_regenerate = (
            force_regenerate or 
            len(saved_outfits) == 0 or 
            len(wardrobe) != last_outfit_generation_count
        )
        
        if not should_regenerate:
            print(f"✅ Returning {len(saved_outfits)} saved outfits")
            return {"outfits": saved_outfits}
        
        print(f"🔄 Need to regenerate outfits (wardrobe changed: {len(wardrobe)} vs {last_outfit_generation_count})")
        print(f"   Found {len(wardrobe)} wardrobe items")
        
        print(f"   Found {len(wardrobe)} wardrobe items")
        
        # Prepare wardrobe summary for AI
        wardrobe_items_list = []
        for idx, item in enumerate(wardrobe):
            item_desc = f"{idx+1}. {item.get('color', '')} {item.get('fabric_type', '')} {item.get('exact_item_name', 'item')} ({item.get('category', 'Other')})"
            wardrobe_items_list.append(item_desc.strip())
        
        wardrobe_summary = "\n".join(wardrobe_items_list)
        
        # Get user context for personalization
        user_context = ""
        if user:
            if user.get("body_shape"):
                user_context += f"Body Shape: {user.get('body_shape')}\n"
            if user.get("skin_tone"):
                user_context += f"Skin Tone: {user.get('skin_tone')}\n"
            if user.get("style_vibe"):
                user_context += f"Style Preference: {user.get('style_vibe')}\n"
        
        # OpenAI prompt for outfit generation
        outfit_prompt = f"""You are an expert fashion stylist creating outfits from a user's wardrobe.

USER PROFILE:
{user_context if user_context else "No profile info available"}

AVAILABLE WARDROBE ITEMS:
{wardrobe_summary}

TASK: Create 6-8 complete outfits using ONLY the items listed above. Each outfit should be appropriate for a specific occasion.

OCCASIONS TO COVER:
- Casual/Everyday
- Work/Business Casual
- Date Night
- Party/Night Out
- Formal
- Weekend/Relaxed
- Sporty/Active (if appropriate items available)

RULES:
1. Use ONLY items from the wardrobe list above (reference by number)
2. Each outfit must have 2-4 items that work well together
3. Consider color coordination, style harmony, and occasion appropriateness
4. Provide a brief (10-15 words) explanation of why each outfit works

FORMAT: Return ONLY valid JSON array, no markdown:
[
  {{
    "occasion": "Casual",
    "items": [1, 3, 5],
    "explanation": "Relaxed yet put-together look perfect for everyday wear"
  }},
  {{
    "occasion": "Date Night",
    "items": [2, 4],
    "explanation": "Elegant combination that's both comfortable and stylish"
  }}
]

Remember: Only use item numbers that exist in the wardrobe list!"""

        # Call OpenAI
        if not OPENAI_API_KEY or len(OPENAI_API_KEY) < 10:
            return {"outfits": [], "message": "OpenAI API key not configured"}
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional fashion stylist creating outfit combinations."},
                {"role": "user", "content": outfit_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_result = response.choices[0].message.content.strip()
        ai_result = ai_result.replace('```json', '').replace('```', '').strip()
        
        import json
        outfit_combinations = json.loads(ai_result)
        
        print(f"✅ Generated {len(outfit_combinations)} outfits")
        
        # Map item numbers back to actual items
        formatted_outfits = []
        for outfit in outfit_combinations:
            outfit_items = []
            for item_num in outfit.get("items", []):
                if 0 < item_num <= len(wardrobe):
                    outfit_items.append(wardrobe[item_num - 1])
            
            if len(outfit_items) >= 2:  # Only include outfits with at least 2 items
                formatted_outfits.append({
                    "occasion": outfit.get("occasion", "Casual"),
                    "items": outfit_items,
                    "explanation": outfit.get("explanation", "A great outfit combination!")
                })
        
        # Save the generated outfits to user document
        await db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "saved_outfits": formatted_outfits,
                    "last_outfit_generation_count": len(wardrobe),
                    "last_outfit_generation": datetime.utcnow().isoformat()
                }
            }
        )
        
        print(f"💾 Saved {len(formatted_outfits)} outfits to user profile")
        
        return {"outfits": formatted_outfits}
        
    except Exception as e:
        print(f"❌ Outfit generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"outfits": [], "message": f"Error generating outfits: {str(e)}"}

# Planned outfit models
class PlannedOutfit(BaseModel):
    date: str  # Format: YYYY-MM-DD
    occasion: str
    event_name: Optional[str] = None
    items: Dict[str, Optional[str]]  # {category: item_id}

# Save planned outfit
@app.post("/api/planner/outfit")
async def save_planned_outfit(planned_outfit: PlannedOutfit, user_id: str = Depends(get_current_user)):
    try:
        
        # Create planned outfit document
        planned_outfit_doc = {
            "date": planned_outfit.date,
            "occasion": planned_outfit.occasion,
            "event_name": planned_outfit.event_name,
            "items": planned_outfit.items,
            "created_at": datetime.utcnow().isoformat(),
            "user_id": user_id
        }
        
        # Update or insert planned outfit for this date
        await db.planned_outfits.replace_one(
            {"user_id": user_id, "date": planned_outfit.date},
            planned_outfit_doc,
            upsert=True
        )
        
        print(f"💾 Saved planned outfit for {planned_outfit.date}")
        return {"message": "Planned outfit saved successfully"}
        
    except Exception as e:
        print(f"❌ Error saving planned outfit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving planned outfit: {str(e)}")

# Get planned outfits for a date range
@app.get("/api/planner/outfits")
async def get_planned_outfits(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user["user_id"]
        
        # Query planned outfits within date range
        planned_outfits_cursor = db.planned_outfits.find({
            "user_id": user_id,
            "date": {"$gte": start_date, "$lte": end_date}
        })
        
        planned_outfits = []
        async for outfit in planned_outfits_cursor:
            outfit["_id"] = str(outfit["_id"])  # Convert ObjectId to string
            planned_outfits.append(outfit)
        
        return {"planned_outfits": planned_outfits}
        
    except Exception as e:
        print(f"❌ Error fetching planned outfits: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching planned outfits: {str(e)}")

# Delete planned outfit
@app.delete("/api/planner/outfit/{date}")
async def delete_planned_outfit(date: str, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["user_id"]
        
        result = await db.planned_outfits.delete_one({"user_id": user_id, "date": date})
        
        if result.deleted_count > 0:
            return {"message": f"Planned outfit for {date} deleted successfully"}
        else:
            return {"message": f"No planned outfit found for {date}"}
            
    except Exception as e:
        print(f"❌ Error deleting planned outfit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting planned outfit: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)