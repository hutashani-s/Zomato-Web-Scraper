# Importing necessary libraries
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import json

# Defining headers to simulate human traffic
HEADERS = {
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, zstd", 
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
} # 'br' in accept-encoding causes text to appear as symbols

# Defining URL and the Collections to Explore
url = "https://www.zomato.com/hyderabad/"
collections = ["asian-restaurants", "og-chicken-places", "delightful-dosas", "world-cuisine", "vegetarian-restaurants", "restaurantes-pet-friendly"]

# Exploring Collections
all_data = []  # To store all restaurant data across collections

#Exploring Collections
for collection in collections:
    response = requests.get(url + collection, headers=HEADERS).text
    soup = bs(response, 'html.parser')

    # Filtering and identifying the script with data
    collection_script = soup.find_all("script", {"type": "application/ld+json"})
    data = None
    for script in collection_script:
        try:
            # Parsing json content of current script
            content = json.loads(script.string)

            # Checking if the script contains the required data
            if content.get("@type") == "ItemList":
                data = content
                break
        except (json.JSONDecodeError, AttributeError):
            continue

    # Extracting Restaurants from the Collection
    restaurant_links = []
    if data and "itemListElement" in data:  # Ensure 'itemListElement' exists
        restaurant_links = [item['url'] for item in data["itemListElement"]]

    # Extracting Restaurant Data from each URL
    for restaurant in restaurant_links:
        res_data = None  # Reset for each restaurant
        restaurant_site = requests.get(restaurant, headers=HEADERS)
        restaurant_soup = bs(restaurant_site.text, 'html.parser')

        # Filtering and identifying script with the data
        individual_scripts = restaurant_soup.find_all("script", {"type": "application/ld+json"})
        for individual_script in individual_scripts:
            try:
                # Parse json content of current script
                indiv_content = json.loads(individual_script.string)

                # Checking if the script contains the required data
                if indiv_content.get("@type") == "Restaurant":
                    res_data = indiv_content
                    break
            except (json.JSONDecodeError, AttributeError):
                continue

        # Processing and Extracting data
        if res_data:
            all_data.append({
                "Name": res_data.get("name"),
                "URL": res_data.get("url"),
                "Collection": collection,
                "Opening Hours": res_data.get("openingHours"),
                "Address": res_data.get("address", {}).get("streetAddress"),
                "Latitude": res_data.get("geo", {}).get("latitude"),
                "Longitude": res_data.get("geo", {}).get("longitude"),
                "Price Range": res_data.get("priceRange"),
                "Rating": res_data.get("aggregateRating", {}).get("ratingValue"),
                "Rating Count": res_data.get("aggregateRating", {}).get("ratingCount"),
            })
        else:
            print(f"No relevant JSON-LD script found for {restaurant}")

# Turning the consolidated data into a DataFrame
if all_data:
    all_restaurants_df = pd.DataFrame(all_data)
    print(all_restaurants_df.head())  # Display the first few rows for verification

    # Saving the data to a CSV
    all_restaurants_df.to_csv("All_Restaurants.csv", index=False)
    print("Data saved to All_Restaurants.csv")
else:
    print("No restaurant data extracted!")
