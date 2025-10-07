import os
import requests
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class FashionService:
    """Fashion service for H&M trends and style data via RapidAPI."""
    
    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://hm-hennes-mauritz.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "hm-hennes-mauritz.p.rapidapi.com"
        }
        
    async def get_trending_products(
        self, 
        country: str = "us",
        lang: str = "en", 
        category: Optional[str] = None,
        limit: int = 20
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get trending products from H&M.
        
        Args:
            country: Country code (us, uk, de, etc.)
            lang: Language code (en, es, fr, etc.)
            category: Product category filter
            limit: Maximum number of products to return
            
        Returns:
            List of trending products or None if failed
        """
        if not self.api_key:
            logger.error("RapidAPI key not configured")
            return None
            
        try:
            url = f"{self.base_url}/products/list"
            
            params = {
                "country": country,
                "lang": lang,
                "currentpage": 0,
                "pagesize": limit
            }
            
            if category:
                params["categories"] = category
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse products data
            products = []
            results = data.get("results", [])
            
            for product in results:
                try:
                    parsed_product = self._parse_product(product)
                    if parsed_product:
                        products.append(parsed_product)
                except Exception as e:
                    logger.warning(f"Failed to parse product: {e}")
                    continue
            
            return products
            
        except requests.RequestException as e:
            logger.error(f"H&M API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"H&M API processing failed: {e}")
            return None
    
    async def get_categories(
        self, 
        country: str = "us",
        lang: str = "en"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get H&M product categories.
        
        Args:
            country: Country code
            lang: Language code
            
        Returns:
            List of categories or None if failed
        """
        if not self.api_key:
            logger.error("RapidAPI key not configured")
            return None
            
        try:
            url = f"{self.base_url}/categories/list"
            
            params = {
                "country": country,
                "lang": lang
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return data.get("results", [])
            
        except requests.RequestException as e:
            logger.error(f"Categories API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Categories API processing failed: {e}")
            return None
    
    def _parse_product(self, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse individual product from H&M API response."""
        try:
            # Get main product image
            images = product_data.get("images", [])
            main_image = None
            if images:
                main_image = images[0].get("url", "")
            
            # Parse price
            price_info = product_data.get("price", {})
            current_price = price_info.get("currencyIso", "") + " " + str(price_info.get("value", ""))
            
            return {
                "id": product_data.get("code", ""),
                "name": product_data.get("name", ""),
                "category": product_data.get("categoryName", ""),
                "price": current_price,
                "currency": price_info.get("currencyIso", "USD"),
                "price_value": price_info.get("value", 0),
                "image_url": main_image,
                "url": product_data.get("linkPdp", ""),
                "colors": self._extract_colors(product_data.get("rgbColors", [])),
                "is_new": product_data.get("newProduct", False),
                "brand": "H&M",
                "description": product_data.get("description", "")
            }
        except Exception as e:
            logger.error(f"Error parsing product data: {e}")
            return None
    
    def _extract_colors(self, rgb_colors: List[Dict[str, Any]]) -> List[str]:
        """Extract color names from RGB color data."""
        colors = []
        for color_data in rgb_colors:
            color_name = color_data.get("text", "")
            if color_name:
                colors.append(color_name)
        return colors
    
    def analyze_fashion_trends(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze fashion trends from H&M products.
        
        Args:
            products: List of products from get_trending_products()
            
        Returns:
            Dict with trend analysis
        """
        if not products:
            return {"trends": "No trend data available"}
        
        # Analyze colors
        color_frequency = {}
        for product in products:
            for color in product.get("colors", []):
                color_frequency[color] = color_frequency.get(color, 0) + 1
        
        # Analyze categories
        category_frequency = {}
        for product in products:
            category = product.get("category", "Unknown")
            category_frequency[category] = category_frequency.get(category, 0) + 1
        
        # Analyze price ranges
        price_ranges = {"low": 0, "medium": 0, "high": 0}
        for product in products:
            price = product.get("price_value", 0)
            if price < 30:
                price_ranges["low"] += 1
            elif price < 60:
                price_ranges["medium"] += 1
            else:
                price_ranges["high"] += 1
        
        # Get trending colors (top 5)
        trending_colors = sorted(color_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Get trending categories (top 5)
        trending_categories = sorted(category_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "trending_colors": [color for color, count in trending_colors],
            "trending_categories": [category for category, count in trending_categories],
            "price_distribution": price_ranges,
            "total_products_analyzed": len(products),
            "new_arrivals": sum(1 for p in products if p.get("is_new", False)),
            "fashion_insights": self._generate_fashion_insights(trending_colors, trending_categories)
        }
    
    def _generate_fashion_insights(
        self, 
        trending_colors: List[tuple], 
        trending_categories: List[tuple]
    ) -> List[str]:
        """Generate fashion insights based on trend analysis."""
        insights = []
        
        if trending_colors:
            top_color = trending_colors[0][0]
            insights.append(f"The most popular color trend right now is {top_color}")
        
        if trending_categories:
            top_category = trending_categories[0][0]
            insights.append(f"The hottest category in fashion is {top_category}")
        
        # Seasonal insights (basic example)
        from datetime import datetime
        current_month = datetime.now().month
        
        if current_month in [12, 1, 2]:  # Winter
            insights.append("Winter fashion emphasizes layering and warm materials")
        elif current_month in [3, 4, 5]:  # Spring
            insights.append("Spring trends focus on fresh colors and lighter fabrics")
        elif current_month in [6, 7, 8]:  # Summer
            insights.append("Summer fashion prioritizes breathable fabrics and bright colors")
        else:  # Fall
            insights.append("Fall fashion features rich colors and transitional pieces")
        
        return insights
    
    def get_style_recommendations_by_trend(
        self, 
        trend_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get personalized style recommendations based on current trends.
        
        Args:
            trend_data: Data from analyze_fashion_trends()
            user_preferences: User style preferences
            
        Returns:
            Dict with personalized recommendations
        """
        recommendations = {
            "trending_colors_to_try": trend_data.get("trending_colors", [])[:3],
            "must_have_categories": trend_data.get("trending_categories", [])[:3],
            "styling_tips": [],
            "budget_advice": self._get_budget_advice(trend_data.get("price_distribution", {})),
            "seasonal_suggestions": []
        }
        
        # Add styling tips based on trends
        trending_colors = trend_data.get("trending_colors", [])
        if trending_colors:
            recommendations["styling_tips"].append(
                f"Try incorporating {trending_colors[0]} into your outfits - it's very on-trend right now"
            )
        
        trending_categories = trend_data.get("trending_categories", [])
        if trending_categories:
            recommendations["styling_tips"].append(
                f"Consider updating your {trending_categories[0].lower()} collection with current trends"
            )
        
        # Add user preference considerations
        if user_preferences:
            self._add_personalized_recommendations(recommendations, user_preferences, trend_data)
        
        # Add seasonal suggestions
        recommendations["seasonal_suggestions"] = self._get_seasonal_suggestions()
        
        return recommendations
    
    def _get_budget_advice(self, price_distribution: Dict[str, int]) -> str:
        """Generate budget advice based on price distribution."""
        total_items = sum(price_distribution.values())
        if total_items == 0:
            return "Price information not available"
        
        low_percent = (price_distribution.get("low", 0) / total_items) * 100
        medium_percent = (price_distribution.get("medium", 0) / total_items) * 100
        high_percent = (price_distribution.get("high", 0) / total_items) * 100
        
        if low_percent > 50:
            return "Great news! Most trending items are budget-friendly (under $30)"
        elif medium_percent > 50:
            return "Current trends are in the mid-range price point ($30-60)"
        else:
            return "Trending items tend to be in the higher price range ($60+)"
    
    def _add_personalized_recommendations(
        self, 
        recommendations: Dict[str, Any], 
        user_preferences: Dict[str, Any],
        trend_data: Dict[str, Any]
    ):
        """Add personalized recommendations based on user preferences."""
        
        # Match user preferences with trends
        user_colors = user_preferences.get("favorite_colors", [])
        trending_colors = trend_data.get("trending_colors", [])
        
        matching_colors = [color for color in trending_colors if color.lower() in [c.lower() for c in user_colors]]
        
        if matching_colors:
            recommendations["styling_tips"].append(
                f"Great news! Your favorite color {matching_colors[0]} is trending right now"
            )
        
        # Budget considerations
        user_budget = user_preferences.get("budget_range", "")
        if "low" in user_budget.lower() or "budget" in user_budget.lower():
            recommendations["styling_tips"].append(
                "Look for trending pieces in the lower price range to stay fashionable on budget"
            )
    
    def _get_seasonal_suggestions(self) -> List[str]:
        """Get seasonal fashion suggestions."""
        from datetime import datetime
        current_month = datetime.now().month
        
        if current_month in [12, 1, 2]:  # Winter
            return [
                "Layer trending colors with winter basics",
                "Look for trending styles in warm fabrics",
                "Add trendy accessories to winter outfits"
            ]
        elif current_month in [3, 4, 5]:  # Spring
            return [
                "Incorporate trending colors into spring wardrobe",
                "Try trending styles in lighter fabrics",
                "Update accessories with spring trends"
            ]
        elif current_month in [6, 7, 8]:  # Summer
            return [
                "Choose trending colors in summer-appropriate fabrics",
                "Look for trending styles that work in hot weather",
                "Update summer accessories with current trends"
            ]
        else:  # Fall
            return [
                "Transition summer pieces with trending fall colors",
                "Layer trending pieces for changing weather",
                "Invest in trending boots and fall accessories"
            ]

# Global fashion service instance
fashion_service = FashionService()