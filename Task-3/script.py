# importing libraries
import spacy
import json
import folium
from folium.plugins import HeatMap
from collections import Counter
from geopy.geocoders import Nominatim
import time
from geopy.exc import GeocoderTimedOut
from datetime import datetime
import pandas as pd
import sys

def read_dataset(file_name):
    """
    Reads a JSON dataset from a file and loads it into a Python dictionary.

    This function opens a JSON file, reads its contents, and parses it 
    into a dictionary or list, depending on the file structure.

    Args:
        file_name (str): The name of the JSON file to read.

    Returns:
        dictionary: The loaded dataset from the JSON file.
    """
    
    with open(file_name, 'r') as f:
        dataset = json.load(f)
    return dataset

def save_posts_to_json(posts, filename="filtered_reddit_posts.json", pretty=True):
    """Saves filtered Reddit posts to a JSON file.

    Args:
        posts (list): A list of dictionaries containing Reddit post data.
        filename (str, optional): The name of the JSON file to save. Defaults to "filtered_reddit_posts.json".
        pretty (bool, optional): Whether to format the JSON for readability (default: True). 
                                 If False, it reduces file size by not adding extra whitespace.
    
    Returns:
        None
    """
    with open(filename, 'w') as json_file:
        json.dump(posts, json_file, indent=4 if pretty else None)

def extract_locations(text,nlp,abbreviation_mapping):
    doc = nlp(text)

    # Normalize abbreviation mapping keys to lowercase for case-insensitive lookup
    lower_abbreviation_mapping = {key.lower(): val for key, val in abbreviation_mapping.items()}

    # Extract named entities (GPE) and normalize to lowercase for comparison
    locations = {ent.text for ent in doc.ents if ent.label_ == "GPE"}

    # Check for abbreviations (case-insensitive) and map them
    words = text.split()
    for word in words:
        lower_word = word.lower()
        if lower_word in lower_abbreviation_mapping:
            locations.add(lower_abbreviation_mapping[lower_word])

    return list(locations) if locations else ["no location found"]

def process_posts(posts):
    nlp = spacy.load("en_core_web_sm")  # Load English NLP model
    # Custom mapping of common abbreviations to full names
    abbreviation_mapping = {
        "NYC": "New York City",
        "LA": "Los Angeles",
        "SF": "San Francisco",
        "UK": "United Kingdom",
        "USA": "United States",
        "US":"United States",
        "UAE": "United Arab Emirates",
        "TX": "Texas",
        "CA": "California",
        "DC": "Washington, D.C.",
    }
    all_locations = []
    for post in posts:
        text = post["content"]
        locations = extract_locations(text=text,nlp=nlp,abbreviation_mapping=abbreviation_mapping)
        all_locations.append(locations)
        post["location"] = locations
    return posts,all_locations

def get_coordinates(geolocator,location,location_cache):
    """Retrieve coordinates for a given location, with caching and retries."""
    if location in location_cache:
        return location_cache[location]
    
    for _ in range(3):  # Retry up to 3 times
        try:
            geo = geolocator.geocode(location)
            if geo:
                coords = (geo.latitude, geo.longitude)
                location_cache[location] = coords  # Store in cache
                return coords
        except GeocoderTimedOut:
            print(f"Timeout for {location}, retrying...")
            time.sleep(2)  # Wait before retrying
        except Exception as e:
            print(f"Error geocoding {location}: {e}")
            return None

    return None  # Return None if all retries fail

def make_map(location_coordinates):
    # Create a Folium Map
    m = folium.Map(location=[20, 0], zoom_start=2, control_scale=True)

    # Add Heatmap with a name for the toggle control
    heat_data = [(lat, lon, count) for lat, lon, count in location_coordinates]
    heat_layer = HeatMap(heat_data, name="Crisis Heatmap")
    heat_layer.add_to(m)

    # Add Tile Layers (Users can toggle layers)
    folium.TileLayer(
        "CartoDB Positron",
        attr="© OpenStreetMap contributors & CARTO"
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)  # Keeps the layer toggle expanded
    # Add Scale Bar
    m.get_root().html.add_child(folium.Element("""
        <style>
            .leaflet-control-scale { background: rgba(255, 255, 255, 0.8); padding: 5px; }
        </style>
    """))

    # Add a Title (Centered at the Top)
    title_html = '''
        <div style="position: fixed; 
                    top: 10px; left: 50%; transform: translateX(-50%);
                    background-color: rgba(255, 255, 255, 0.8); 
                    padding: 10px; z-index: 1000; font-size:16px; font-weight: bold; 
                    text-align: center; border-radius: 5px;">
            Crisis Heatmap: Mental Health Distress & Substance Use - {}
        </div>
    '''.format(datetime.now().strftime("%Y-%m-%d"))
    m.get_root().html.add_child(folium.Element(title_html))


    # Add a Legend (Color Scale)
    legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 10px; width: 160px; height: auto; 
                    background-color: rgba(255, 255, 255, 0.8);
                    padding: 10px; z-index: 1000; font-size:12px;">
            <b>Post Intensity</b><br>
            <div style="width: 20px; height: 20px; background: red; display: inline-block;"></div> High<br>
            <div style="width: 20px; height: 20px; background: orange; display: inline-block;"></div> Medium<br>
            <div style="width: 20px; height: 20px; background: yellow; display: inline-block;"></div> Low<br>
        </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    # Save and display the map
    map_path = 'crisis_heatmap.html'
    m.save(map_path)
    print(f"Map saved to {map_path}")

def get_location_coordinates(user_agent,location_counts):
    # Initialize geocoder
    geolocator = Nominatim(user_agent=user_agent, timeout=10)
    # Caching to avoid redundant API calls
    location_cache = {}
    # Convert location names to coordinates
    location_coordinates = []
    for location, count in location_counts.items():
        coords = get_coordinates(geolocator=geolocator,location=location,location_cache=location_cache)
        if coords:
            location_coordinates.append((*coords, count))
        time.sleep(2)  # Increase sleep time to prevent rate limiting
    return location_coordinates
def read_and_process_data(file_name):
    """
    Reads the dataset and processes posts to extract locations.
    
    Args:
        file_name (str): Path to the dataset JSON file.
    
    Returns:
        tuple: Processed posts and a list of all extracted locations.
    """
    posts = read_dataset(file_name=file_name)
    posts, all_locations = process_posts(posts=posts)
    return posts, all_locations

def save_processed_data(posts, filename):
    """
    Saves the processed posts with extracted locations to a JSON file.

    Args:
        posts (list): List of processed posts.
        filename (str): File name to save the updated dataset.
    """
    save_posts_to_json(posts=posts, filename=filename)
    print(f"Processed dataset saved as {filename}")

def filter_locations(all_locations):
    """
    Flattens and filters the extracted locations, removing unwanted words.

    Args:
        all_locations (list): List of extracted locations.

    Returns:
        Counter: A Counter object with the count of each filtered location.
    """
    flat_locations = [loc for sublist in all_locations for loc in sublist]
    
    unwanted_words = {"no location found", "meth", "kinda", "example", "country",
                      "place", "world", "earth", "everywhere", "phobia", "mcas"}
    
    filtered_locations = [loc for loc in flat_locations if loc.lower() not in unwanted_words]
    
    return Counter(filtered_locations)

def save_top_locations(location_counts, file_path="top_5_locations.csv"):
    """
    Saves the top 5 locations with the most discussions to a CSV file.

    Args:
        location_counts (Counter): A Counter object with location counts.
        file_path (str): The file path to save the CSV.
    """
    top_5_locations = location_counts.most_common(5)
    df_top5 = pd.DataFrame(top_5_locations, columns=["Location", "Count"])
    df_top5.to_csv(file_path, index=False)
    print(f"Top 5 Locations saved to {file_path}")

def create_and_display_map(location_coordinates):
    """
    Generates a heatmap and stores it using Folium.

    Args:
        location_coordinates (list): A list of tuples with location data.
    """
    make_map(location_coordinates=location_coordinates)

def main():
    """
    Main function to process the dataset, extract locations, generate a heatmap, 
    and save top location statistics. Requires a user agent as a command-line argument.
    """
    # Check if the script received the correct number of arguments
    if len(sys.argv) < 2:
        print("Error: No user agent provided.")
        print("Usage: python script.py 'your_user_agent_string'")
        sys.exit(1)  # Exit the script
    # Get the user agent from command-line arguments
    user_agent = sys.argv[1]
    print(f"User agent : {user_agent}")
    file_name = '../Task-2/updated_dataset.json'
    
    # Step 1: Read and Process Data
    posts, all_locations = read_and_process_data(file_name)

    # Step 2: Save Processed Data
    save_processed_data(posts, "updated_dataset_with_locations.json")

    # Step 3: Filter and Count Locations
    location_counts = filter_locations(all_locations)

    # Step 4: Save Top Locations to CSV
    save_top_locations(location_counts)

    # Step 5: Get Location Coordinates
    print("Getting location coordinates... (this may take some time)")
    location_coordinates = get_location_coordinates(user_agent=user_agent,location_counts=location_counts)

    # Step 6: Generate Map
    create_and_display_map(location_coordinates)

    print("Script finished!")

if __name__ == "__main__":
    main()