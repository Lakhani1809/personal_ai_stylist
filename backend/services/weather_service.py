import os
import requests
import logging
from typing import Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class WeatherService:
    """Weather service for getting location-based weather data for outfit recommendations."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
    async def get_current_weather(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Get current weather for a location.
        
        Args:
            location: City name (e.g., "New York,NY,US" or "London,UK")
            
        Returns:
            Dict with weather data or None if failed
        """
        if not self.api_key:
            logger.error("OpenWeather API key not configured")
            return None
            
        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "imperial"  # Fahrenheit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "temperature": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "condition": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data.get("wind", {}).get("speed", 0),
                "location": data["name"],
                "country": data["sys"]["country"]
            }
            
        except requests.RequestException as e:
            logger.error(f"Weather API request failed: {e}")
            return None
        except KeyError as e:
            logger.error(f"Weather API response parsing failed: {e}")
            return None
            
    async def get_weather_forecast(self, location: str, days: int = 5) -> Optional[Dict[str, Any]]:
        """
        Get weather forecast for planning outfits.
        
        Args:
            location: City name
            days: Number of days forecast (max 5 for free tier)
            
        Returns:
            Dict with forecast data or None if failed
        """
        if not self.api_key:
            logger.error("OpenWeather API key not configured")
            return None
            
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "imperial"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Process forecast data (5-day forecast with 3-hour intervals)
            forecast = []
            for item in data["list"][:days * 8]:  # Limit to requested days
                forecast.append({
                    "date": item["dt_txt"],
                    "temperature": round(item["main"]["temp"]),
                    "condition": item["weather"][0]["main"],
                    "description": item["weather"][0]["description"],
                    "humidity": item["main"]["humidity"]
                })
            
            return {
                "location": data["city"]["name"],
                "country": data["city"]["country"],
                "forecast": forecast
            }
            
        except requests.RequestException as e:
            logger.error(f"Weather forecast API request failed: {e}")
            return None
        except KeyError as e:
            logger.error(f"Weather forecast API response parsing failed: {e}")
            return None
    
    def get_outfit_recommendations_by_weather(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate outfit recommendations based on weather conditions.
        
        Args:
            weather_data: Weather data from get_current_weather()
            
        Returns:
            Dict with weather-based styling advice
        """
        if not weather_data:
            return {"recommendations": "Weather data unavailable"}
            
        temp = weather_data["temperature"]
        condition = weather_data["condition"].lower()
        description = weather_data["description"].lower()
        humidity = weather_data["humidity"]
        wind_speed = weather_data.get("wind_speed", 0)
        
        recommendations = {
            "temperature_advice": self._get_temperature_advice(temp),
            "condition_advice": self._get_condition_advice(condition, description),
            "fabric_suggestions": self._get_fabric_suggestions(temp, humidity),
            "color_suggestions": self._get_color_suggestions(condition, temp),
            "layering_advice": self._get_layering_advice(temp, wind_speed),
            "accessories": self._get_weather_accessories(condition, temp, humidity)
        }
        
        return {
            "weather": weather_data,
            "recommendations": recommendations
        }
    
    def _get_temperature_advice(self, temp: int) -> str:
        """Get temperature-specific outfit advice."""
        if temp >= 80:
            return "Hot weather: Choose lightweight, breathable fabrics. Opt for light colors and minimal layers."
        elif temp >= 70:
            return "Warm weather: Light fabrics work well. Perfect for sundresses, shorts, or light pants."
        elif temp >= 60:
            return "Mild weather: Great for layering! Light sweater or cardigan with comfortable pants."
        elif temp >= 50:
            return "Cool weather: Light jacket or blazer recommended. Long pants and closed-toe shoes."
        elif temp >= 40:
            return "Cold weather: Warm coat necessary. Consider thermal layers and winter accessories."
        else:
            return "Very cold: Heavy winter coat essential. Multiple layers, warm boots, hat and gloves."
    
    def _get_condition_advice(self, condition: str, description: str) -> str:
        """Get weather condition-specific advice."""
        if "rain" in condition or "drizzle" in description:
            return "Rainy conditions: Waterproof jacket or umbrella essential. Avoid suede/leather shoes."
        elif "snow" in condition:
            return "Snowy conditions: Waterproof boots with good traction. Warm, water-resistant outerwear."
        elif "clear" in condition or "sunny" in description:
            return "Sunny conditions: Don't forget sun protection! Sunglasses and light colors to reflect heat."
        elif "cloud" in condition:
            return "Cloudy conditions: Comfortable for most outfits. Light layers in case temperature changes."
        elif "wind" in condition or "windy" in description:
            return "Windy conditions: Avoid loose scarves or hats. Fitted clothing or wind-resistant layers."
        else:
            return "Check current conditions for best outfit choice."
    
    def _get_fabric_suggestions(self, temp: int, humidity: int) -> str:
        """Suggest appropriate fabrics based on temperature and humidity."""
        if temp >= 75 and humidity > 70:
            return "High heat + humidity: Linen, cotton, bamboo, or moisture-wicking synthetics."
        elif temp >= 75:
            return "Hot + dry: Cotton, linen, silk, or lightweight synthetic blends."
        elif temp >= 60:
            return "Moderate temperature: Cotton, jersey knit, light wool, or denim."
        elif temp >= 45:
            return "Cool temperature: Wool, fleece, heavier cotton, or layered synthetics."
        else:
            return "Cold temperature: Wool, cashmere, thermal layers, or insulated synthetic materials."
    
    def _get_color_suggestions(self, condition: str, temp: int) -> str:
        """Suggest colors based on weather and temperature."""
        if temp >= 75:
            if "clear" in condition or "sunny" in condition:
                return "Bright weather: Light colors (white, pastels, light blue) to reflect heat."
            else:
                return "Warm weather: Light to medium colors work well."
        elif temp >= 50:
            return "Moderate weather: Perfect for any colors! Try seasonal favorites."
        else:
            if "snow" in condition:
                return "Snowy weather: Darker colors show less dirt, but bright colors add cheer!"
            else:
                return "Cool weather: Deeper colors (navy, burgundy, forest green) look great."
    
    def _get_layering_advice(self, temp: int, wind_speed: float) -> str:
        """Provide layering advice based on temperature and wind."""
        if temp >= 70 and wind_speed < 5:
            return "Minimal layering needed. Single layer or light cardigan for air conditioning."
        elif temp >= 60:
            return "Light layering recommended. Cardigan, light jacket, or blazer for flexibility."
        elif temp >= 45:
            return "Moderate layering: Base layer + sweater/jacket. Easy to adjust as needed."
        elif temp >= 30:
            return "Multiple layers essential: Base layer + insulating layer + outer shell."
        else:
            return "Heavy layering required: Thermal base + insulating layers + heavy winter coat."
    
    def _get_weather_accessories(self, condition: str, temp: int, humidity: int) -> str:
        """Suggest weather-appropriate accessories."""
        accessories = []
        
        if temp >= 75 or "sunny" in condition:
            accessories.append("sunglasses")
            accessories.append("sun hat")
        
        if "rain" in condition:
            accessories.append("umbrella")
            accessories.append("waterproof bag")
        
        if temp <= 45:
            accessories.append("warm hat")
            accessories.append("gloves")
            accessories.append("scarf")
        
        if humidity > 70 and temp > 70:
            accessories.append("sweat-wicking headband")
            accessories.append("cooling towel")
        
        if "wind" in condition:
            accessories.append("secure hat (no loose styles)")
        
        return ", ".join(accessories) if accessories else "No special accessories needed"

# Global weather service instance
weather_service = WeatherService()