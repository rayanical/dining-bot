"""
Script to initialize database and populate food items from scraper.
Run this once to set up the database.

Usage:
    python -m app.core.init_db
"""
from app.core.database import engine, Base, SessionLocal
from app.models import DiningHallMenu
from app.core.scraper import scrape_all_menus
from datetime import datetime
from collections import defaultdict

def map_scraper_data_to_schema(scraped_items):
    """
    Maps scraper data to dining_hall_menu schema format.
    Groups items by (item, dining_hall) and combines meals into availability_today array.
    """
    from collections import defaultdict

    # Group by (item, dining_hall) to combine meals
    grouped = defaultdict(lambda: {
        "item": None,
        "dining_hall": None,
        "calories": None,
        "serving_size": None,
        "fat_g": None,
        "sat_fat_g": None,
        "trans_fat_g": None,
        "cholesterol_mg": None,
        "sodium_mg": None,
        "carbs_g": None,
        "fiber_g": None,
        "sugars_g": None,
        "protein_g": None,
        "allergens": set(),
        "diet_types": set(),
        "availability_today": set(),
    })
    
    for item in scraped_items:
        key = (item["name"], item["dining_hall"])
        
        if grouped[key]["item"] is None:
            grouped[key]["item"] = item["name"]
            grouped[key]["dining_hall"] = item["dining_hall"]
            # Map nutritional values
            grouped[key]["calories"] = item.get("calories")
            grouped[key]["serving_size"] = item.get("serving_size")
            grouped[key]["fat_g"] = item.get("fat_g")
            grouped[key]["sat_fat_g"] = item.get("sat_fat_g")
            grouped[key]["trans_fat_g"] = item.get("trans_fat_g")
            grouped[key]["cholesterol_mg"] = item.get("cholesterol_mg")
            grouped[key]["sodium_mg"] = item.get("sodium_mg")
            grouped[key]["carbs_g"] = item.get("carbs_g")
            grouped[key]["fiber_g"] = item.get("fiber_g")
            grouped[key]["sugars_g"] = item.get("sugars_g")
            grouped[key]["protein_g"] = item.get("protein_g")
        
        # Add allergens
        allergens_str = item.get("allergens", "").strip()
        if allergens_str:
            allergens_list = [a.strip() for a in allergens_str.split(",") if a.strip()]
            grouped[key]["allergens"].update(allergens_list)
        
        # Add diet types
        if item.get("diets"):
            grouped[key]["diet_types"].update(item["diets"])
        
        # Add meal to availability
        meal = item.get("meal", "").strip()
        if meal:
            grouped[key]["availability_today"].add(meal.lower())
    
    # Convert to list of dicts matching schema
    result = []
    for data in grouped.values():
        result.append({
            "item": data["item"],
            "dining_hall": data["dining_hall"],
            "calories": data["calories"],
            "serving_size": data["serving_size"],
            "fat_g": data["fat_g"],
            "sat_fat_g": data["sat_fat_g"],
            "trans_fat_g": data["trans_fat_g"],
            "cholesterol_mg": data["cholesterol_mg"],
            "sodium_mg": data["sodium_mg"],
            "carbs_g": data["carbs_g"],
            "fiber_g": data["fiber_g"],
            "sugars_g": data["sugars_g"],
            "protein_g": data["protein_g"],
            "allergens": list(data["allergens"]) if data["allergens"] else None,
            "diet_types": list(data["diet_types"]) if data["diet_types"] else None,
            "availability_today": list(data["availability_today"]) if data["availability_today"] else None,
        })
    
    return result

def init_database():
    """Create tables and optionally populate with scraped data."""
    # Note: Tables are already created in Supabase, so we skip create_all
    # Base.metadata.create_all(bind=engine)  # Commented out - tables exist in Supabase
    print("✓ Using existing Supabase database tables")
    
    # Populate food items
    db = SessionLocal()
    try:
        # Check if we already have food items
        existing_count = db.query(DiningHallMenu).count()
        if existing_count > 0:
            print(f"⚠ Found {existing_count} existing food items in database.")
            response = input("Do you want to clear and re-scrape? (y/n): ")
            if response.lower() == 'y':
                db.query(DiningHallMenu).delete()
                db.commit()
                print("✓ Cleared existing food items")
            else:
                print("Skipping scrape. Keeping existing data.")
                return
        
        # Scrape and insert
        print("\nScraping menus... This may take a minute...")
        scraped_items = scrape_all_menus()
        
        if not scraped_items:
            print("⚠ No items scraped. Check your internet connection and try again.")
            return
        
        print(f"✓ Scraped {len(scraped_items)} food items")
        print(f"Mapping to schema format...")
        
        # Map to schema format
        mapped_items = map_scraper_data_to_schema(scraped_items)
        print(f"✓ Mapped to {len(mapped_items)} unique items")
        
        print(f"Inserting items into database...")
        for item_data in mapped_items:
            menu_item = DiningHallMenu(**item_data)
            db.add(menu_item)
        
        db.commit()
        print(f"✓ Successfully inserted {len(mapped_items)} items into database")
        
        # Verify
        count = db.query(DiningHallMenu).count()
        print(f"✓ Database now contains {count} items")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
