import requests
import re
from bs4 import BeautifulSoup

# --- Configuration ---
BASE_URL = "https://umassdining.com/locations-menus"
DINING_HALLS = [
    "berkshire",
    "worcester",
    "franklin",
    "hampshire"
]

# --- Helper Function ---
def clean_numeric_value(s):
    """
    Extracts the first number (float or int) from a string.
    Example: "16.4g" -> 16.4
    Example: "199" -> 199.0
    Example: "49.8mg" -> 49.8
    """
    if s is None:
        return 0.0
    
    # Find the first sequence of digits and optional decimal point
    match = re.search(r'[\d\.]+', str(s))
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return 0.0
    return 0.0

# --- Main Parsing Function ---
def scrape_menu_page(dining_hall_slug):
    """
    Scrapes all meals and items for a single dining hall.
    
    Args:
        dining_hall_slug (str): e.g., "berkshire", "worcester"

    Returns:
        list: A list of dictionaries, where each is a food item.
    """
    url = f"{BASE_URL}/{dining_hall_slug}/menu"
    print(f"Scraping {url}...")
    
    try:
        page = requests.get(url)
        page.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Could not fetch page. {e}")
        return []

    soup = BeautifulSoup(page.text, 'html.parser')
    all_food_items = []
    
    # Get the dining hall name from the page title
    title = soup.find("title").text
    dining_hall_name = title.split("|")[0].strip().replace(" Menu", "") # e.g., "Berkshire"
    
    # Find the main container for all meal panels (Lunch, Dinner, etc.)
    panel_container = soup.find("div", class_="panel-container")
    if not panel_container:
        print(f"  ERROR: Could not find 'panel-container'. Page structure may have changed.")
        return []
    
    # Each direct child div of panel-container is a meal
    meal_panels = panel_container.find_all("div", recursive=False)
    
    for panel in meal_panels:
        meal_name_tag = panel.find("h2")
        if not meal_name_tag:
            continue
        
        meal_name = meal_name_tag.text.strip() # "Lunch", "Dinner", "Late Night"
        
        # This div contains the list of stations and items
        content_section = panel.find("div", id=re.compile(r"content_text"))
        if not content_section:
            continue

        current_station = "Unknown"
        
        # Iterate over all children (h2 for stations, li for items)
        for element in content_section.children:
            if element.name == "h2" and 'menu_category_name' in element.get('class', []):
                # This is a station name, update our current station
                current_station = element.text.strip()
            
            elif element.name == "li" and 'lightbox-nutrition' in element.get('class', []):
                # This is a food item, parse it
                item_link = element.find("a")
                if not item_link:
                    continue
                
                # All data is stored in 'data-*' attributes on the <a> tag
                data = item_link.attrs
                
                try:
                    diets = data.get('data-clean-diet-str', '').split(', ')
                    
                    food_item = {
                        "name": data.get('data-dish-name'),
                        "dining_hall": dining_hall_name,
                        "meal": meal_name,
                        "station": current_station,
                        "serving_size": data.get('data-serving-size'),
                        "calories": clean_numeric_value(data.get('data-calories')),
                        "fat_g": clean_numeric_value(data.get('data-total-fat')),
                        "sat_fat_g": clean_numeric_value(data.get('data-sat-fat')),
                        "trans_fat_g": clean_numeric_value(data.get('data-trans-fat')),
                        "cholesterol_mg": clean_numeric_value(data.get('data-cholesterol')),
                        "sodium_mg": clean_numeric_value(data.get('data-sodium')),
                        "carbs_g": clean_numeric_value(data.get('data-total-carb')),
                        "fiber_g": clean_numeric_value(data.get('data-dietary-fiber')),
                        "sugars_g": clean_numeric_value(data.get('data-sugars')),
                        "protein_g": clean_numeric_value(data.get('data-protein')),
                        "allergens": data.get('data-allergens', '').strip(),
                        "ingredients": data.get('data-ingredient-list', '').strip(),
                        "diets": [d for d in diets if d] # Remove empty strings
                    }
                    all_food_items.append(food_item)
                
                except Exception as e:
                    print(f"  ERROR: Failed to parse item: {data.get('data-dish-name')}. Reason: {e}")

    print(f"  Successfully scraped {len(all_food_items)} items from {dining_hall_name}.")
    return all_food_items


def scrape_all_menus():
    """
    Runs the scraper for all specified dining halls and returns one combined list.
    """
    print("--- Starting Full UMass Menu Scrape ---")
    master_menu_list = []
    
    for hall_slug in DINING_HALLS:
        items = scrape_menu_page(hall_slug)
        master_menu_list.extend(items)
    
    print("--- Scrape Complete ---")
    print(f"Total items scraped from {len(DINING_HALLS)} dining halls: {len(master_menu_list)}")
    return master_menu_list

# This allows you to run the script directly from your terminal
# to test it:  python backend/app/core/scraper.py
if __name__ == "__main__":
    all_data = scrape_all_menus()
    
    if all_data:
        print("\nSample item (first item scraped):")
        import json
        print(json.dumps(all_data[0], indent=2))
        
        print("\nSample item (last item scraped):")
        print(json.dumps(all_data[-1], indent=2))