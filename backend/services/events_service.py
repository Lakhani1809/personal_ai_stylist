import os
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class EventsService:
    """Events service for getting real-time local events for outfit recommendations."""
    
    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://real-time-events-search.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "real-time-events-search.p.rapidapi.com"
        }
        
    async def search_events(
        self, 
        location: str, 
        start_date: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Search for local events in a specific location.
        
        Args:
            location: City name (e.g., "New York", "Los Angeles")
            start_date: Date in YYYY-MM-DD format (defaults to today)
            event_type: Type of event to filter by
            limit: Maximum number of events to return
            
        Returns:
            List of events or None if failed
        """
        if not self.api_key:
            logger.error("RapidAPI key not configured")
            return None
            
        try:
            url = f"{self.base_url}/search-events"
            
            if not start_date:
                start_date = date.today().strftime("%Y-%m-%d")
            
            params = {
                "query": location,
                "date": start_date,
                "limit": limit
            }
            
            if event_type:
                params["type"] = event_type
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse events data (API response format may vary)
            events = []
            events_data = data.get("data", data.get("events", []))
            
            for event in events_data:
                try:
                    parsed_event = self._parse_event(event)
                    if parsed_event:
                        events.append(parsed_event)
                except Exception as e:
                    logger.warning(f"Failed to parse event: {e}")
                    continue
            
            return events
            
        except requests.RequestException as e:
            logger.error(f"Events API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Events API processing failed: {e}")
            return None
    
    def _parse_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse individual event from API response."""
        try:
            return {
                "id": str(event_data.get("id", "")),
                "title": event_data.get("title", event_data.get("name", "Event")),
                "description": event_data.get("description", ""),
                "start_time": event_data.get("start_time", event_data.get("date")),
                "end_time": event_data.get("end_time"),
                "location": event_data.get("location", event_data.get("venue", "")),
                "event_type": event_data.get("type", event_data.get("category", "")),
                "price": event_data.get("price", ""),
                "url": event_data.get("url", event_data.get("link", "")),
                "venue": event_data.get("venue", {}),
                "organizer": event_data.get("organizer", "")
            }
        except Exception as e:
            logger.error(f"Error parsing event data: {e}")
            return None
    
    def categorize_event_for_styling(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize event and provide styling recommendations.
        
        Args:
            event: Event data from search_events()
            
        Returns:
            Dict with event category and styling suggestions
        """
        title = (event.get("title", "") + " " + event.get("description", "")).lower()
        event_type = event.get("event_type", "").lower()
        location = event.get("location", "").lower()
        
        # Determine formality level and dress code
        formality, dress_code = self._determine_formality(title, event_type, location)
        
        # Get specific styling recommendations
        style_recommendations = self._get_event_style_recommendations(
            formality, event_type, title, location
        )
        
        return {
            "event": event,
            "styling": {
                "formality_level": formality,
                "dress_code": dress_code,
                "recommendations": style_recommendations,
                "color_suggestions": self._get_event_color_suggestions(event_type, title),
                "avoid": self._get_event_avoid_list(event_type, title),
                "accessories": self._get_event_accessories(formality, event_type),
                "time_considerations": self._get_time_considerations(event.get("start_time"))
            }
        }
    
    def _determine_formality(self, title: str, event_type: str, location: str) -> tuple[str, str]:
        """Determine formality level and dress code for an event."""
        
        # High formality indicators
        formal_keywords = [
            "gala", "ball", "charity", "auction", "awards", "ceremony", 
            "wedding", "graduation", "formal", "black tie", "cocktail",
            "fundraiser", "opera", "symphony", "theater"
        ]
        
        # Business/professional indicators  
        business_keywords = [
            "conference", "seminar", "workshop", "networking", "meeting",
            "presentation", "corporate", "business", "professional", "summit"
        ]
        
        # Casual indicators
        casual_keywords = [
            "festival", "fair", "market", "picnic", "barbecue", "party",
            "concert", "music", "art", "craft", "outdoor", "sports", "game"
        ]
        
        # Check venue type
        formal_venues = ["hotel", "ballroom", "club", "resort", "theater", "opera house"]
        business_venues = ["center", "office", "conference", "convention", "corporate"]
        casual_venues = ["park", "outdoor", "beach", "bar", "pub", "cafe"]
        
        full_text = f"{title} {event_type} {location}"
        
        # Determine formality
        if any(keyword in full_text for keyword in formal_keywords):
            return "formal", "Formal attire (suit/dress)"
        elif any(keyword in full_text for keyword in business_keywords):
            return "business_casual", "Business casual"
        elif any(venue in location for venue in formal_venues):
            return "semi_formal", "Semi-formal attire"
        elif any(venue in location for venue in business_venues):
            return "business_casual", "Business casual"
        elif any(venue in location for venue in casual_venues):
            return "casual", "Casual comfortable attire"
        elif any(keyword in full_text for keyword in casual_keywords):
            return "casual", "Casual comfortable attire"
        else:
            return "smart_casual", "Smart casual attire"
    
    def _get_event_style_recommendations(
        self, 
        formality: str, 
        event_type: str, 
        title: str, 
        location: str
    ) -> List[str]:
        """Get specific style recommendations based on event characteristics."""
        
        recommendations = []
        
        if formality == "formal":
            recommendations.extend([
                "Choose elegant, well-fitted clothing",
                "Opt for classic colors like navy, black, or burgundy",
                "Ensure shoes are polished and appropriate",
                "Consider the venue's dress code requirements"
            ])
        
        elif formality == "business_casual":
            recommendations.extend([
                "Professional but not overly formal",
                "Blazer or cardigan adds polish",
                "Avoid overly casual items like sneakers or shorts",
                "Stick to neutral or conservative colors"
            ])
        
        elif formality == "casual":
            recommendations.extend([
                "Comfort is key for casual events",
                "Layer for temperature changes if outdoor",
                "Choose breathable fabrics for active events",
                "Express your personal style while remaining appropriate"
            ])
        
        # Add event-type specific advice
        if "outdoor" in location or "park" in location:
            recommendations.append("Consider weather and walking surfaces")
            
        if "networking" in title or "professional" in title:
            recommendations.append("Dress to make a good professional impression")
            
        if "dinner" in title or "evening" in title:
            recommendations.append("Evening events typically call for elevated attire")
            
        return recommendations
    
    def _get_event_color_suggestions(self, event_type: str, title: str) -> List[str]:
        """Suggest appropriate colors based on event type."""
        
        full_text = f"{event_type} {title}".lower()
        
        if "wedding" in full_text:
            return ["pastels", "soft blues", "sage green", "dusty rose"]
        elif "business" in full_text or "professional" in full_text:
            return ["navy", "charcoal", "white", "light blue", "gray"]
        elif "party" in full_text or "celebration" in full_text:
            return ["jewel tones", "bold colors", "metallics", "bright colors"]
        elif "formal" in full_text or "gala" in full_text:
            return ["black", "navy", "burgundy", "emerald", "gold accents"]
        elif "outdoor" in full_text or "festival" in full_text:
            return ["earth tones", "bright colors", "comfortable neutrals"]
        else:
            return ["versatile neutrals", "colors you love", "seasonal favorites"]
    
    def _get_event_avoid_list(self, event_type: str, title: str) -> List[str]:
        """Things to avoid wearing based on event type."""
        
        avoid_list = []
        full_text = f"{event_type} {title}".lower()
        
        if "wedding" in full_text:
            avoid_list.extend(["white", "ivory", "overly flashy"])
            
        if "business" in full_text or "professional" in full_text:
            avoid_list.extend(["too casual", "revealing", "overly trendy"])
            
        if "outdoor" in full_text:
            avoid_list.extend(["delicate fabrics", "high heels on grass", "all white"])
            
        if "formal" in full_text:
            avoid_list.extend(["casual footwear", "overly casual attire"])
            
        return avoid_list if avoid_list else ["Nothing specific to avoid"]
    
    def _get_event_accessories(self, formality: str, event_type: str) -> List[str]:
        """Suggest appropriate accessories for the event."""
        
        accessories = []
        
        if formality == "formal":
            accessories.extend(["elegant jewelry", "dress watch", "clutch or small bag"])
        elif formality == "business_casual":
            accessories.extend(["professional watch", "simple jewelry", "structured bag"])
        else:
            accessories.extend(["comfortable shoes", "practical bag", "weather-appropriate items"])
            
        if "outdoor" in event_type:
            accessories.extend(["sunglasses", "comfortable shoes", "weather protection"])
            
        return accessories
    
    def _get_time_considerations(self, start_time: Optional[str]) -> str:
        """Get time-based styling considerations."""
        
        if not start_time:
            return "Check event timing for appropriate styling"
            
        try:
            # Try to parse time if it's provided
            if ":" in str(start_time):
                hour = int(start_time.split(":")[0])
                if hour >= 18:
                    return "Evening event - consider more elegant attire"
                elif hour >= 12:
                    return "Afternoon event - smart casual to semi-formal"
                else:
                    return "Morning/daytime event - comfortable and polished"
        except:
            pass
            
        return "Consider the event timing when choosing your outfit"

# Global events service instance
events_service = EventsService()