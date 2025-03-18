import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

# Set random seed for reproducibility
np.random.seed(42)

# Define crime categories and types
crime_categories = {
    'Violent Crimes': [
        'Homicide', 
        'Aggravated Assault', 
        'Simple Assault', 
        'Armed Robbery', 
        'Unarmed Robbery', 
        'Kidnapping', 
        'Domestic Violence', 
        'Gang Violence'
    ],
    'Property Crimes': [
        'Home Burglary', 
        'Commercial Burglary', 
        'Petty Theft', 
        'Grand Theft', 
        'Auto Theft', 
        'Carjacking', 
        'Arson', 
        'Vandalism', 
        'Graffiti'
    ]
}

# Flatten crime types for easier random selection
all_crime_types = []
for category, types in crime_categories.items():
    for crime_type in types:
        all_crime_types.append((category, crime_type))

# Define NYC neighborhoods with approximate coordinates
neighborhoods = {
    'Manhattan': {
        'Midtown': (40.7549, -73.9840),
        'Upper East Side': (40.7735, -73.9565),
        'Upper West Side': (40.7870, -73.9754),
        'Chelsea': (40.7465, -74.0014),
        'Greenwich Village': (40.7339, -73.9976),
        'Financial District': (40.7075, -74.0113),
        'Harlem': (40.8116, -73.9465),
        'East Village': (40.7265, -73.9815)
    },
    'Brooklyn': {
        'Williamsburg': (40.7081, -73.9571),
        'DUMBO': (40.7032, -73.9884),
        'Park Slope': (40.6710, -73.9814),
        'Brooklyn Heights': (40.6958, -73.9936),
        'Bushwick': (40.6944, -73.9213),
        'Bedford-Stuyvesant': (40.6872, -73.9418),
        'Crown Heights': (40.6694, -73.9422),
        'Flatbush': (40.6409, -73.9617)
    },
    'Queens': {
        'Astoria': (40.7644, -73.9235),
        'Long Island City': (40.7447, -73.9485),
        'Flushing': (40.7654, -73.8318),
        'Jamaica': (40.7020, -73.8085),
        'Forest Hills': (40.7185, -73.8458),
        'Jackson Heights': (40.7556, -73.8830)
    },
    'Bronx': {
        'Riverdale': (40.8900, -73.9122),
        'Fordham': (40.8614, -73.8908),
        'Mott Haven': (40.8091, -73.9229),
        'Pelham Bay': (40.8488, -73.8331)
    },
    'Staten Island': {
        'St. George': (40.6447, -74.0763),
        'Todt Hill': (40.6015, -74.1035),
        'Great Kills': (40.5544, -74.1510)
    }
}

# Function to generate random coordinates near a center point
def generate_random_location(center, max_offset=0.01):
    lat, lng = center
    lat_offset = np.random.uniform(-max_offset, max_offset)
    lng_offset = np.random.uniform(-max_offset, max_offset)
    return (lat + lat_offset, lng + lng_offset)

# Function to generate a random date within a range
def random_date(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

# Function to generate a random time
def random_time():
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}"

# Generate crime data
def generate_crime_data(num_records=650):
    data = []
    
    # Date range: 2021-01-01 to 2024-03-01
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2024, 3, 1)
    
    # Crime ID counter
    crime_id = 10000
    
    for _ in range(num_records):
        # Select random borough and neighborhood
        borough = random.choice(list(neighborhoods.keys()))
        neighborhood = random.choice(list(neighborhoods[borough].keys()))
        
        # Get base coordinates for the neighborhood
        base_coords = neighborhoods[borough][neighborhood]
        
        # Generate random location near the neighborhood center
        lat, lng = generate_random_location(base_coords)
        
        # Select random crime type
        category, crime_type = random.choice(all_crime_types)
        
        # Generate random date and time
        date = random_date(start_date, end_date)
        time = random_time()
        
        # Generate severity (1-10)
        if category == 'Violent Crimes':
            severity = random.randint(5, 10)  # Violent crimes are more severe
        else:
            severity = random.randint(1, 7)   # Property crimes vary in severity
        
        # Generate random number of victims
        victims = max(1, int(np.random.exponential(1.5))) if category == 'Violent Crimes' else 0
        
        # Generate random property damage value for property crimes
        property_damage = int(np.random.exponential(5000)) if category == 'Property Crimes' else 0
        
        # Generate random street address
        street_number = random.randint(1, 9999)
        streets = ["Main St", "Broadway", "Park Ave", "5th Ave", "Madison Ave", "Lexington Ave", 
                  "3rd Ave", "2nd Ave", "1st Ave", "Avenue A", "Avenue B", "West End Ave",
                  "Riverside Dr", "Central Park West", "Amsterdam Ave", "Columbus Ave"]
        street = random.choice(streets)
        
        # Generate random status
        statuses = ["Unsolved", "Under Investigation", "Suspect Identified", "Suspect Arrested", "Closed", "Cold Case"]
        status_weights = [0.2, 0.3, 0.15, 0.2, 0.1, 0.05]  # Probabilities for each status
        status = random.choices(statuses, weights=status_weights, k=1)[0]
        
        # Add record to data
        data.append({
            'CRIME_ID': crime_id,
            'DATE': date.strftime('%Y-%m-%d'),
            'TIME': time,
            'BOROUGH': borough,
            'NEIGHBORHOOD': neighborhood,
            'LATITUDE': lat,
            'LONGITUDE': lng,
            'CATEGORY': category,
            'CRIME_TYPE': crime_type,
            'SEVERITY': severity,
            'VICTIMS': victims,
            'PROPERTY_DAMAGE': property_damage,
            'STREET_ADDRESS': f"{street_number} {street}",
            'STATUS': status
        })
        
        crime_id += 1
    
    return pd.DataFrame(data)

# Generate and save the data
def main():
    print("Generating crime dataset...")
    df = generate_crime_data(650)
    
    # Save to CSV
    csv_path = 'crime_data.csv'
    df.to_csv(csv_path, index=False)
    print(f"Dataset generated with {len(df)} records and saved to {csv_path}")
    
    # Print sample
    print("\nSample data:")
    print(df.head())
    
    # Print statistics
    print("\nData statistics:")
    print(f"Date range: {df['DATE'].min()} to {df['DATE'].max()}")
    print(f"Crime categories: {df['CATEGORY'].value_counts().to_dict()}")
    print(f"Crime types: {df['CRIME_TYPE'].nunique()} unique types")
    print(f"Boroughs: {df['BOROUGH'].value_counts().to_dict()}")

if __name__ == "__main__":
    main()
