import sys
import os
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import engine, SessionLocal
from app.data.models import Base, FoodItem
from app.core.scraper import scrape_all_menus

def seed_database():
    print("Initializing database and creating tables...")
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    try:
        print("Starting menu scrape...")
        food_items_data = scrape_all_menus()
        
        if not food_items_data:
            print("No items were scraped. Exiting seed script.")
            return

        print(f"Scraped {len(food_items_data)} items. Seeding database...")
        
        # Track items to avoid duplicates in this run
        added_items = 0
        existing_items = 0
        
        for item_data in food_items_data:
            # Check if an item with the same name, dining hall, and meal already exists
            exists = session.query(FoodItem).filter(
                FoodItem.name == item_data["name"],
                FoodItem.dining_hall == item_data["dining_hall"],
                FoodItem.meal == item_data["meal"]
            ).first()
            
            if not exists:
                food_item = FoodItem(
                    name=item_data["name"],
                    dining_hall=item_data["dining_hall"],
                    meal=item_data["meal"],
                    station=item_data["station"],
                    serving_size=item_data["serving_size"],
                    calories=item_data["calories"],
                    fat_g=item_data["fat_g"],
                    sat_fat_g=item_data["sat_fat_g"],
                    trans_fat_g=item_data["trans_fat_g"],
                    cholesterol_mg=item_data["cholesterol_mg"],
                    sodium_mg=item_data["sodium_mg"],
                    carbs_g=item_data["carbs_g"],
                    fiber_g=item_data["fiber_g"],
                    sugars_g=item_data["sugars_g"],
                    protein_g=item_data["protein_g"],
                    allergens=item_data["allergens"],
                    ingredients=item_data["ingredients"],
                    diets=item_data["diets"]
                )
                session.add(food_item)
                added_items += 1
            else:
                existing_items += 1
        
        print(f"Committing {added_items} new items to the database...")
        print(f"Skipped {existing_items} items that already exist.")
        session.commit()
        print("Database seeding complete!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    # This allows you to run the script directly:
    # python backend/app/data/seed_db.py
    seed_database()