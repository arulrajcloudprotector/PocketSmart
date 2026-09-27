import os
import json
import re
import urllib.parse
from google import genai
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
client = genai.Client()
MODEL_NAME = "gemini-3.8-flash"


def _extract_json(text):
    """Clean markdown fences and parse JSON."""
    text = re.sub(r"```json|```", "", text).strip()
    return json.loads(text)


def _add_home_links(result):
    for cat in result.get("budget_breakdown", []):
        for item in cat.get("items", []):
            st_terms = item.get("search_terms", "")
            if st_terms:
                q = urllib.parse.quote_plus(st_terms)
                item["shopping_links"] = {
                    "amazon": f"https://www.amazon.in/s?k={q}",
                    "flipkart": f"https://www.flipkart.com/search?q={q}",
                    "ikea": f"https://www.ikea.com/in/en/search/?q={q}",
                    "myntra": f"https://www.myntra.com/search?q={q}"
                }
    return result


def _add_party_links(result):
    for cat in result.get("budget_breakdown", []):
        cat_name = cat.get("category", "").lower()
        for item in cat.get("items", []):
            st_terms = item.get("search_terms", "")
            if not st_terms:
                continue
            q = urllib.parse.quote_plus(st_terms)
            links = {}
            if cat_name in ("venue", "accommodation"):
                links["google"] = f"https://www.google.com/search?q={q}"
                links["makemytrip"] = f"https://www.makemytrip.com/hotels/hotel-listing/?searchText={q}"
                links["oyorooms"] = f"https://www.oyorooms.com/search?location={q}"
            elif cat_name in ("catering", "food", "drinks"):
                links["swiggy"] = f"https://www.swiggy.com/search?query={q}"
                links["zomato"] = f"https://www.zomato.com/search?q={q}"
            elif cat_name == "entertainment":
                links["bookmyshow"] = f"https://in.bookmyshow.com/search?q={q}"
                links["amazon"] = f"https://www.amazon.in/s?k={q}"
            else:
                links["amazon"] = f"https://www.amazon.in/s?k={q}"
                links["flipkart"] = f"https://www.flipkart.com/search?q={q}"
                links["myntra"] = f"https://www.myntra.com/search?q={q}"
            item["shopping_links"] = links
    return result


def _add_jewelry_links(result):
    for item in result.get("jewelry_recommendations", []):
        st_terms = item.get("search_terms", "")
        if st_terms:
            q = urllib.parse.quote_plus(st_terms)
            item["shopping_links"] = {
                "amazon": f"https://www.amazon.in/s?k={q}",
                "flipkart": f"https://www.flipkart.com/search?q={q}",
                "myntra": f"https://www.myntra.com/search?q={q}",
                "tanishq": f"https://www.tanishq.co.in/search?q={q}",
                "caratlane": f"https://www.caratlane.com/search?q={q}"
            }
    return result


def get_home_recommendations(total_budget, num_lights, num_fans, num_furniture, num_dining, additional):
    prompt = f"""You are a home interior expert for India.
Budget: Rs.{total_budget}
Lights: {num_lights}, Fans: {num_fans}, Furniture: {num_furniture}, Dining Tables: {num_dining}
Additional needs: {additional or "None"}

Return ONLY valid JSON (no markdown) with this structure:
{{
  "total_budget": {total_budget},
  "budget_breakdown": [
    {{
      "category": "Lighting",
      "allocation": 0,
      "items": [
        {{"name":"", "description":"", "estimated_price":0, "quantity":0, "search_terms":""}}
      ]
    }}
  ],
  "remaining_budget": 0,
  "additional_suggestions": []
}}
Use Indian brands, INR prices, and India-friendly search terms. Keep total under budget."""

    try:
        interaction = client.interactions.create(model=MODEL_NAME, input=prompt)
        result = _extract_json(interaction.output_text)
        return _add_home_links(result)
    except Exception as e:
        return {"error": str(e)}


def get_party_recommendations(total_budget, party_type, num_guests, venue, catering, decoration, entertainment, additional):
    prompt = f"""You are a party planning expert for India.
Budget: Rs.{total_budget}
Event: {party_type}, Guests: {num_guests}
Venue: {venue or "Not specified"}
Catering: {catering}, Decoration: {decoration}, Entertainment: {entertainment}
Additional: {additional or "None"}

Return ONLY valid JSON (no markdown):
{{
  "total_budget": {total_budget},
  "budget_breakdown": [
    {{
      "category": "Catering",
      "allocation": 0,
      "items": [
        {{"name":"", "description":"", "estimated_price":0, "quantity":0, "search_terms":""}}
      ]
    }}
  ],
  "venue_suggestions": [],
  "remaining_budget": 0,
  "additional_suggestions": []
}}
Use Indian vendors and INR prices."""

    try:
        interaction = client.interactions.create(model=MODEL_NAME, input=prompt)
        result = _extract_json(interaction.output_text)
        return _add_party_links(result)
    except Exception as e:
        return {"error": str(e)}


def get_jewelry_recommendations(total_budget, occasion, preferences, image_path=None):
    base_prompt = f"""You are a jewelry styling expert for India.
Budget: Rs.{total_budget}
Occasion: {occasion}
Preferences: {preferences or "None"}
Return ONLY valid JSON (no markdown):
{{
  "outfit_analysis": {{"colors":[], "style":"", "formality":""}},
  "total_budget": {total_budget},
  "jewelry_recommendations": [
    {{"item_type":"", "description":"", "style":"", "estimated_price":0, "search_terms":""}}
  ],
  "remaining_budget": 0,
  "styling_tips": []
}}
Use INR prices and Indian brands."""

    try:
        if image_path:
            img = Image.open(image_path)
            prompt = base_prompt + "\nAn outfit image is uploaded. Suggest jewelry that complements it."
            interaction = client.interactions.create(
                model=MODEL_NAME,
                input=[prompt, img]
            )
        else:
            interaction = client.interactions.create(model=MODEL_NAME, input=base_prompt)
        result = _extract_json(interaction.output_text)
        return _add_jewelry_links(result)
    except Exception as e:
        return {"error": str(e)}