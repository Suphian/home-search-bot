import os
import requests
import pandas as pd
from dotenv import load_dotenv
import googlemaps
from statistics import median

# Load API keys
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
REALTOR_API_KEY = os.getenv("REALTOR_API_KEY")
GREATSCHOOLS_API_KEY = os.getenv("GREATSCHOOLS_API_KEY")

# Constants (customize as needed)
REGION = "Dallas-Fort Worth, TX"
BEDS_MIN = 3
BEDS_MAX = 4
BATHS_MIN = 2.5
SQFT_MIN = 2000
AGE_MAX = 20
PRICE_MIN = 350_000
PRICE_MAX = 550_000
UNDERVALUED_PCT = 0.85 # 15% below comps
MAX_MERCEDES_COMMUTE = 90 # minutes
MAX_MOSQUE_COMMUTE = 20 # minutes
MAX_COSTCO_COMMUTE = 15 # minutes
MAX_TARGET_COMMUTE = 10 # minutes
MAX_GYM_COMMUTE = 15 # minutes

MERCEDES_HQ = "13650 Heritage Pkwy, Fort Worth, TX 76177"
JOB_ADDRESS = ""  # Set to "" if not needed

MOSQUES = [
    ("Valley Ranch Islamic Center", "351 Ranchview Dr, Irving, TX 75063"),
    ("Epic Masjid", "4701 14th St, Plano, TX 75074")
]

PREMIUM_GYMS = ["Life Time", "Equinox"]

# Set up Google Maps client
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

def get_properties():
    # This example uses the Realtor API on RapidAPI
    url = "https://realtor.p.rapidapi.com/properties/v2/list-for-sale"
    headers = {
        "X-RapidAPI-Key": REALTOR_API_KEY,
        "X-RapidAPI-Host": "realtor.p.rapidapi.com"
    }
    params = {
        "city": "Dallas",
        "limit": 200,
        "beds_min": BEDS_MIN,
        "beds_max": BEDS_MAX,
        "baths_min": BATHS_MIN,
        "price_min": PRICE_MIN,
        "price_max": PRICE_MAX,
        "sqft_min": SQFT_MIN,
        "sort": "newest"
    }
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        print("Failed to fetch properties:", resp.text)
        return []
    return resp.json().get("properties", [])

def get_comparables(property):
    # This is a stub. Ideally, you'd use the same API to pull 10+ recent sales in the same zip/area.
    # For demo, let's just use other properties in the same zip code.
    all_props = get_properties()
    return [p for p in all_props if
            p['address']['postal_code'] == property['address']['postal_code'] and
            abs(float(p['baths']) - float(property['baths'])) <= 1 and
            abs(int(p['beds']) - int(property['beds'])) <= 1 and
            abs(int(p['building_size']['size']) - int(property['building_size']['size'])) <= 500]

def is_undervalued(property):
    comps = get_comparables(property)
    if not comps:
        return False
    comp_prices = [c['price'] for c in comps if 'price' in c and c['price'] is not None]
    if not comp_prices:
        return False
    avg_price = median(comp_prices)
    return property['price'] <= avg_price * UNDERVALUED_PCT

def driving_time_okay(origin, dest, max_minutes):
    try:
        directions = gmaps.directions(origin, dest, mode="driving")
        minutes = directions[0]['legs'][0]['duration']['value'] / 60
        return minutes <= max_minutes
    except Exception as e:
        print(f"Error calculating driving time from {origin} to {dest}: {e}")
        return False

def check_amenity(home_addr, keyword, max_time):
    places = gmaps.places_nearby(
        location=gmaps.geocode(home_addr)[0]['geometry']['location'],
        radius=16093,  # 10 miles (~16km), increase if needed
        keyword=keyword
    )
    for place in places.get('results', []):
        dest = place['vicinity']
        if driving_time_okay(home_addr, dest, max_time):
            return True
    return False

def near_mosque(home_addr):
    for name, mosque_addr in MOSQUES:
        if driving_time_okay(home_addr, mosque_addr, MAX_MOSQUE_COMMUTE):
            return True
    return False

def near_costco(home_addr):
    return check_amenity(home_addr, "Costco", MAX_COSTCO_COMMUTE)

def near_target(home_addr):
    return check_amenity(home_addr, "Target", MAX_TARGET_COMMUTE)

def near_gym(home_addr):
    for gym in PREMIUM_GYMS:
        if check_amenity(home_addr, gym, MAX_GYM_COMMUTE):
            return True
    return False

def not_in_hoa(property):
    # Many APIs provide HOA as a field (sometimes 'hoa_fee' or 'hoa' or 'association_fee')
    hoa_fee = property.get('association_fee') or property.get('hoa_fee')
    if hoa_fee and hoa_fee > 0:
        return False
    return True

def school_rating_is_high(home_addr):
    # Use GreatSchools API to check school rating near home_addr
    # This is a stub. Actual API call needed.
    # Return True if rating >= 7/10 (customize as needed)
    return True

def is_good_candidate(property):
    # Basic checks
    if not (property['beds'] >= BEDS_MIN and property['beds'] <= BEDS_MAX):
        return False
    if float(property['baths']) < BATHS_MIN:
        return False
    if int(property['building_size']['size']) < SQFT_MIN:
        return False
    age = 2025 - int(property['year_built']) if 'year_built' in property and property['year_built'] else 100
    if age > AGE_MAX and property['price'] > 400_000:
        return False
    if not (PRICE_MIN <= property['price'] <= PRICE_MAX):
        return False
    # Undervalued?
    if not is_undervalued(property):
        return False
    # School quality
    if not school_rating_is_high(property['address']['line']):
        return False
    # Amenities
    addr = property['address']['line']
    if not near_costco(addr): return False
    if not near_target(addr): return False
    if not near_mosque(addr): return False
    if not near_gym(addr): return False
    # HOA
    if not not_in_hoa(property): return False
    # Commute (Mercedes HQ)
    if not driving_time_okay(addr, MERCEDES_HQ, MAX_MERCEDES_COMMUTE): return False
    # Optionally, your own work commute:
    if JOB_ADDRESS and not driving_time_okay(addr, JOB_ADDRESS, 30): return False
    return True

def main():
    homes = get_properties()
    good_homes = []
    for home in homes:
        try:
            if is_good_candidate(home):
                good_homes.append(home)
        except Exception as e:
            print("Error evaluating home:", home.get('address', {}).get('line'), e)
    if good_homes:
        df = pd.DataFrame(good_homes)
        df.to_csv("filtered_dallas_homes.csv", index=False)
        print(f"Found {len(good_homes)} matching homes! See filtered_dallas_homes.csv.")
    else:
        print("No homes found matching all criteria.")

if __name__ == "__main__":
    main()
