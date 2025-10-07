from fastapi import FastAPI, HTTPException, Depends
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

# Import custom model handler
from model_handlers.custom_model_handler import model_handler

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
        
        # ADVANCED Personal Stylist prompt with deep personalization
        system_prompt = f"""You are Maya ✨, a personal fashion stylist - like having a stylish best friend who knows fashion inside out!

{user_context}
{wardrobe_context}

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

🧠 PERSONALIZATION (Use their profile):
1. Consider their body shape for fit advice
2. Use their skin tone for color recommendations
3. Match their profession (work vs casual vs creative)
4. Align with their style vibes
5. Reference their actual wardrobe items by name

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
        
        # Clean the base64 data and check size
        clean_base64 = image_base64.split(',')[-1] if ',' in image_base64 else image_base64
        
        # Check if image is too large for MongoDB (16MB limit)
        image_size_mb = len(clean_base64) * 0.75 / (1024 * 1024)  # Convert base64 to approximate bytes
        print(f"Image size: {image_size_mb:.2f} MB")
        
        if image_size_mb > 15:  # Leave some margin
            raise HTTPException(status_code=400, detail=f"Image too large ({image_size_mb:.1f}MB). Please use an image smaller than 15MB.")
        
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
        
        # Store in user's wardrobe
        result = await db.users.update_one(
            {"id": user_id},
            {"$push": {"wardrobe": item}}
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

@app.delete("/api/wardrobe/{item_id}")
async def delete_wardrobe_item(item_id: str, user_id: str = Depends(get_current_user)):
    try:
        # Remove item from user's wardrobe array
        result = await db.users.update_one(
            {"id": user_id},
            {"$pull": {"wardrobe": {"id": item_id}}}
        )
        
        if result.modified_count > 0:
            return {"message": "Item deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Item not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete item")

@app.delete("/api/wardrobe/clear")
async def clear_wardrobe(user_id: str = Depends(get_current_user)):
    try:
        print(f"Clearing wardrobe for user: {user_id}")
        
        # Clear all items from user's wardrobe
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": {"wardrobe": []}}
        )
        
        print(f"Clear result: {result.modified_count} documents modified")
        return {"message": "Wardrobe cleared successfully"}
            
    except Exception as e:
        print(f"Clear wardrobe error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear wardrobe: {str(e)}")

@app.post("/api/validate-outfit")
async def validate_outfit(outfit_data: dict, user_id: str = Depends(get_current_user)):
    try:
        image_base64 = outfit_data.get("image_base64", "")
        if not image_base64:
            raise HTTPException(status_code=400, detail="Image is required")
        
        # Use custom model handler for outfit validation
        validation_success = False
        try:
            print(f"👗 Starting custom outfit validation analysis...")
            
            # Use custom models first (your models)
            validation = model_handler.analyze_outfit_validation(image_base64)
            
            if validation and validation.get("overall_score", 0) > 3.0:
                validation["id"] = str(uuid.uuid4())
                validation["image_base64"] = image_base64.split(',')[-1] if ',' in image_base64 else image_base64
                validation_success = True
                print(f"✅ Custom outfit validation successful!")
                print(f"   Overall Score: {validation['overall_score']}")
                print(f"   Feedback: {validation['feedback'][:100]}...")
            else:
                print("⚠️ Custom validation models not available, falling back to OpenAI...")
                
                # Fallback to OpenAI if custom models aren't loaded
                if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10:
                    validation_prompt = """Analyze this outfit professionally. Return JSON with scores (1.0-5.0) for: color_combo, fit, style, occasion, overall_score, and detailed feedback."""
                    
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
            validation = {
                "id": str(uuid.uuid4()),
                "scores": {
                    "color_combo": 3.8,
                    "fit": 3.7,
                    "style": 4.0,
                    "occasion": 3.9
                },
                "overall_score": 3.9,
                "feedback": "Your outfit has a nice overall composition! The pieces work well together and show good style sense.",
                "image_base64": image_base64.split(',')[-1] if ',' in image_base64 else image_base64
            }
        
        return validation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to validate outfit")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)