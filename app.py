from flask import Flask, request, jsonify, render_template
import pandas as pd
import numpy as np
from flask_cors import CORS
import os
import json
from geopy.distance import geodesic
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS for all routes

# Load and preprocess the crime data
def load_data():
    try:
        print("Loading crime data...")
        df = pd.read_csv('crime_data.csv')
        print(f"Successfully loaded CSV with {len(df)} records")
        
        # Convert date to datetime
        df['DATE'] = pd.to_datetime(df['DATE'])
        
        # Create year and month columns for time-based analysis
        df['YEAR'] = df['DATE'].dt.year
        df['MONTH'] = df['DATE'].dt.month
        df['DAY_OF_WEEK'] = df['DATE'].dt.day_name()
        
        # Extract hour from time for time-of-day analysis
        df['HOUR'] = df['TIME'].apply(lambda x: int(x.split(':')[0]))
        
        # Create time of day category
        time_of_day = []
        for hour in df['HOUR']:
            if 5 <= hour < 12:
                time_of_day.append('Morning')
            elif 12 <= hour < 17:
                time_of_day.append('Afternoon')
            elif 17 <= hour < 21:
                time_of_day.append('Evening')
            else:
                time_of_day.append('Night')
        
        df['TIME_OF_DAY'] = time_of_day
        
        return df
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Global variable to store the data
crime_data = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/crimes', methods=['POST'])
def get_crimes():
    global crime_data
    
    try:
        # Load data if not already loaded
        if crime_data is None:
            crime_data = load_data()
            if crime_data.empty:
                return jsonify({'error': 'Failed to load crime data'}), 500
        
        # Get from and to coordinates from request
        data = request.json
        print(f"Received request data: {data}")
        
        from_lat = data.get('from_lat')
        from_lng = data.get('from_lng')
        to_lat = data.get('to_lat')
        to_lng = data.get('to_lng')
        
        # Check if detailed route coordinates are provided
        route_coordinates = data.get('route_coordinates', [])
        
        # Validate coordinates
        if not all([from_lat, from_lng, to_lat, to_lng]):
            print("Invalid coordinates received")
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        # Convert to float
        from_lat, from_lng = float(from_lat), float(from_lng)
        to_lat, to_lng = float(to_lat), float(to_lng)
        
        print(f"Processing route from ({from_lat}, {from_lng}) to ({to_lat}, {to_lng})")
        
        # Create bounding box for the route (with some buffer)
        if route_coordinates and len(route_coordinates) > 0:
            # If we have detailed route coordinates, create a bounding box that encompasses all points
            lats = [coord[0] for coord in route_coordinates]
            lngs = [coord[1] for coord in route_coordinates]
            min_lat = min(lats) - 0.005  # Smaller buffer since we have precise route
            max_lat = max(lats) + 0.005
            min_lng = min(lngs) - 0.005
            max_lng = max(lngs) + 0.005
        else:
            # Fallback to simple bounding box between start and end points
            min_lat = min(from_lat, to_lat) - 0.02
            max_lat = max(from_lat, to_lat) + 0.02
            min_lng = min(from_lng, to_lng) - 0.02
            max_lng = max(from_lng, to_lng) + 0.02
        
        # Filter crimes within the bounding box
        filtered_data = crime_data[
            (crime_data['LATITUDE'] >= min_lat) & 
            (crime_data['LATITUDE'] <= max_lat) &
            (crime_data['LONGITUDE'] >= min_lng) & 
            (crime_data['LONGITUDE'] <= max_lng)
        ]
        
        print(f"Found {len(filtered_data)} crimes within the bounding box")
        
        # Function to calculate minimum distance from point to a polyline (route)
        def point_to_route_distance(point, route_points):
            min_distance = float('inf')
            
            # If no route points or only one point, return a large distance
            if not route_points or len(route_points) < 2:
                return min_distance
            
            # Check distance to each segment of the route
            for i in range(len(route_points) - 1):
                segment_start = route_points[i]
                segment_end = route_points[i + 1]
                
                # Calculate distance from point to this segment
                try:
                    # Convert to numpy arrays for vector operations
                    point_np = np.array([float(point[0]), float(point[1])])
                    segment_start_np = np.array([float(segment_start[0]), float(segment_start[1])])
                    segment_end_np = np.array([float(segment_end[0]), float(segment_end[1])])
                    
                    # Vector from segment_start to segment_end
                    segment_vec = segment_end_np - segment_start_np
                    segment_length = np.linalg.norm(segment_vec)
                    segment_unit_vec = segment_vec / segment_length if segment_length > 0 else segment_vec
                    
                    # Vector from segment_start to point
                    point_vec = point_np - segment_start_np
                    
                    # Project point_vec onto segment_unit_vec
                    projection_length = np.dot(point_vec, segment_unit_vec)
                    
                    # If projection is outside the segment, use distance to nearest endpoint
                    if projection_length < 0:
                        segment_distance = np.linalg.norm(point_vec)
                    elif projection_length > segment_length:
                        segment_distance = np.linalg.norm(point_np - segment_end_np)
                    else:
                        # Distance from point to segment
                        projection = segment_start_np + projection_length * segment_unit_vec
                        segment_distance = np.linalg.norm(point_np - projection)
                    
                    # Update minimum distance if this segment is closer
                    min_distance = min(min_distance, segment_distance)
                    
                except Exception as e:
                    print(f"Error calculating segment distance: {str(e)}")
                    continue
            
            return min_distance
        
        # Function to calculate distance from point to line segment (for fallback)
        def point_to_line_distance(point, line_start, line_end):
            try:
                # Convert to numpy arrays for vector operations
                point = np.array([float(point[0]), float(point[1])])
                line_start = np.array([float(line_start[0]), float(line_start[1])])
                line_end = np.array([float(line_end[0]), float(line_end[1])])
                
                # Vector from line_start to line_end
                line_vec = line_end - line_start
                line_length = np.linalg.norm(line_vec)
                line_unit_vec = line_vec / line_length if line_length > 0 else line_vec
                
                # Vector from line_start to point
                point_vec = point - line_start
                
                # Project point_vec onto line_unit_vec
                projection_length = np.dot(point_vec, line_unit_vec)
                
                # If projection is outside the line segment, use distance to nearest endpoint
                if projection_length < 0:
                    return np.linalg.norm(point_vec)
                elif projection_length > line_length:
                    return np.linalg.norm(point - line_end)
                else:
                    # Distance from point to line
                    projection = line_start + projection_length * line_unit_vec
                    return np.linalg.norm(point - projection)
            except Exception as e:
                print(f"Error in point_to_line_distance: {str(e)}")
                # Return a large distance if there's an error
                return 999
        
        # Filter crimes that are close to the route
        MAX_DISTANCE_KM = 0.5  # Reduced distance threshold for more precise filtering
        nearby_crimes = []
        
        for _, crime in filtered_data.iterrows():
            lat, lng = crime['LATITUDE'], crime['LONGITUDE']
            
            # Calculate distance in km
            try:
                crime_point = (float(lat), float(lng))
                
                if route_coordinates and len(route_coordinates) > 1:
                    # Use the detailed route path for distance calculation
                    distance = point_to_route_distance(crime_point, route_coordinates)
                    distance_km = distance * 111  # Rough conversion to km
                else:
                    # Fallback to simple line if no detailed route
                    route_start = (float(from_lat), float(from_lng))
                    route_end = (float(to_lat), float(to_lng))
                    distance_km = point_to_line_distance(crime_point, route_start, route_end) * 111
                
            except Exception as e:
                print(f"Error calculating distance: {str(e)}")
                continue  # Skip this crime if there's an error
            
            if distance_km <= MAX_DISTANCE_KM:
                # Create crime data dictionary with proper handling of NaN values
                crime_info = {
                    'id': int(crime['CRIME_ID']),
                    'latitude': float(lat),
                    'longitude': float(lng),
                    'date': str(crime['DATE'].date()),
                    'time': str(crime['TIME']),
                    'borough': str(crime['BOROUGH']),
                    'neighborhood': str(crime['NEIGHBORHOOD']),
                    'category': str(crime['CATEGORY']),
                    'crime_type': str(crime['CRIME_TYPE']),
                    'severity': int(crime['SEVERITY']),
                    'victims': int(crime['VICTIMS']),
                    'property_damage': int(crime['PROPERTY_DAMAGE']),
                    'street_address': str(crime['STREET_ADDRESS']),
                    'status': str(crime['STATUS']),
                    'year': int(crime['YEAR']),
                    'month': int(crime['MONTH']),
                    'day_of_week': str(crime['DAY_OF_WEEK']),
                    'hour': int(crime['HOUR']),
                    'time_of_day': str(crime['TIME_OF_DAY']),
                    'distance_to_route': float(distance_km)  # Add distance to route for reference
                }
                
                # Replace any NaN values with appropriate defaults
                for key, value in crime_info.items():
                    if pd.isna(value):
                        if isinstance(value, (int, float)):
                            crime_info[key] = 0
                        else:
                            crime_info[key] = ''
                
                nearby_crimes.append(crime_info)
        
        # Calculate route safety score based on crime density and severity
        safety_score = 100
        if nearby_crimes:
            # Reduce score based on number and severity of crimes
            crime_count = len(nearby_crimes)
            total_severity = sum(crime['severity'] for crime in nearby_crimes)
            violent_crimes = sum(1 for crime in nearby_crimes if crime['category'] == 'Violent Crimes')
            
            # Adjust score (simple algorithm - can be refined)
            safety_score -= min(60, crime_count * 3)  # Reduce up to 60 points based on count
            safety_score -= min(20, total_severity / 2)  # Reduce up to 20 points based on severity
            safety_score -= min(20, violent_crimes * 5)  # Reduce up to 20 points based on violent crimes
        
        # Determine safety level
        safety_level = 'High'
        if safety_score < 60:
            safety_level = 'Low'
        elif safety_score < 80:
            safety_level = 'Medium'
        
        # Generate crime statistics
        crime_stats = {}
        if nearby_crimes:
            df_nearby = pd.DataFrame(nearby_crimes)
            
            # Crime types breakdown
            crime_types = df_nearby['crime_type'].value_counts().to_dict()
            
            # Crime categories breakdown
            crime_categories = df_nearby['category'].value_counts().to_dict()
            
            # Time of day breakdown
            time_of_day = df_nearby['time_of_day'].value_counts().to_dict()
            
            # Day of week breakdown
            day_of_week = df_nearby['day_of_week'].value_counts().to_dict()
            
            # Year breakdown
            year_counts = df_nearby['year'].value_counts().to_dict()
            
            # Neighborhood breakdown
            neighborhood_counts = df_nearby['neighborhood'].value_counts().to_dict()
            
            # Status breakdown
            status_counts = df_nearby['status'].value_counts().to_dict()
            
            # Average severity
            avg_severity = float(df_nearby['severity'].mean())
            
            # Total victims
            total_victims = int(df_nearby['victims'].sum())
            
            # Total property damage
            total_property_damage = int(df_nearby['property_damage'].sum())
            
            crime_stats = {
                'crime_types': crime_types,
                'crime_categories': crime_categories,
                'time_of_day': time_of_day,
                'day_of_week': day_of_week,
                'year_counts': year_counts,
                'neighborhood_counts': neighborhood_counts,
                'status_counts': status_counts,
                'avg_severity': avg_severity,
                'total_victims': total_victims,
                'total_property_damage': total_property_damage
            }
        
        print(f"Found {len(nearby_crimes)} crimes close to the route")
        print(f"Safety score: {safety_score}, Safety level: {safety_level}")
        
        return jsonify({
            'crimes': nearby_crimes,
            'safety_score': safety_score,
            'safety_level': safety_level,
            'crime_stats': crime_stats
        })
        
    except Exception as e:
        print(f"Error in get_crimes: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-summary', methods=['GET'])
def get_data_summary():
    global crime_data
    
    # Load data if not already loaded
    if crime_data is None:
        crime_data = load_data()
        if crime_data.empty:
            return jsonify({'error': 'Failed to load crime data'}), 500
    
    # Get summary statistics
    total_crimes = len(crime_data)
    violent_crimes = len(crime_data[crime_data['CATEGORY'] == 'Violent Crimes'])
    property_crimes = len(crime_data[crime_data['CATEGORY'] == 'Property Crimes'])
    
    # Get crime counts by borough
    borough_counts = crime_data['BOROUGH'].value_counts().to_dict()
    
    # Get crime counts by year
    year_counts = crime_data['YEAR'].value_counts().sort_index().to_dict()
    
    # Get top crime types
    crime_type_counts = crime_data['CRIME_TYPE'].value_counts().head(10).to_dict()
    
    # Get crime counts by time of day
    time_of_day_counts = crime_data['TIME_OF_DAY'].value_counts().to_dict()
    
    # Get crime counts by day of week
    day_of_week_counts = crime_data['DAY_OF_WEEK'].value_counts().to_dict()
    
    # Get average severity
    avg_severity = float(crime_data['SEVERITY'].mean())
    
    # Get total victims
    total_victims = int(crime_data['VICTIMS'].sum())
    
    # Get total property damage
    total_property_damage = int(crime_data['PROPERTY_DAMAGE'].sum())
    
    # Generate time series data for crimes by month
    time_series = crime_data.groupby(['YEAR', 'MONTH']).size().reset_index(name='count')
    time_series['date'] = time_series.apply(lambda x: f"{int(x['YEAR'])}-{int(x['MONTH']):02d}", axis=1)
    time_series_data = time_series[['date', 'count']].to_dict('records')
    
    # Generate choropleth data for crimes by neighborhood
    neighborhood_data = crime_data.groupby(['BOROUGH', 'NEIGHBORHOOD']).size().reset_index(name='count')
    neighborhood_data = neighborhood_data.to_dict('records')
    
    return jsonify({
        'total_crimes': total_crimes,
        'violent_crimes': violent_crimes,
        'property_crimes': property_crimes,
        'borough_counts': borough_counts,
        'year_counts': year_counts,
        'crime_type_counts': crime_type_counts,
        'time_of_day_counts': time_of_day_counts,
        'day_of_week_counts': day_of_week_counts,
        'avg_severity': avg_severity,
        'total_victims': total_victims,
        'total_property_damage': total_property_damage,
        'time_series_data': time_series_data,
        'neighborhood_data': neighborhood_data
    })

@app.route('/api/crime-trends', methods=['GET'])
def get_crime_trends():
    global crime_data
    
    # Load data if not already loaded
    if crime_data is None:
        crime_data = load_data()
        if crime_data.empty:
            return jsonify({'error': 'Failed to load crime data'}), 500
    
    # Generate time series for violent crimes
    violent_ts = crime_data[crime_data['CATEGORY'] == 'Violent Crimes'].groupby(['YEAR', 'MONTH']).size().reset_index(name='count')
    violent_ts['date'] = violent_ts.apply(lambda x: f"{int(x['YEAR'])}-{int(x['MONTH']):02d}", axis=1)
    violent_ts_data = violent_ts[['date', 'count']].to_dict('records')
    
    # Generate time series for property crimes
    property_ts = crime_data[crime_data['CATEGORY'] == 'Property Crimes'].groupby(['YEAR', 'MONTH']).size().reset_index(name='count')
    property_ts['date'] = property_ts.apply(lambda x: f"{int(x['YEAR'])}-{int(x['MONTH']):02d}", axis=1)
    property_ts_data = property_ts[['date', 'count']].to_dict('records')
    
    # Get crime type trends over years
    crime_type_years = crime_data.groupby(['YEAR', 'CRIME_TYPE']).size().reset_index(name='count')
    crime_type_years_data = crime_type_years.to_dict('records')
    
    # Get borough trends over years
    borough_years = crime_data.groupby(['YEAR', 'BOROUGH']).size().reset_index(name='count')
    borough_years_data = borough_years.to_dict('records')
    
    # Get time of day trends
    time_of_day_years = crime_data.groupby(['YEAR', 'TIME_OF_DAY']).size().reset_index(name='count')
    time_of_day_years_data = time_of_day_years.to_dict('records')
    
    # Get day of week trends
    day_of_week_years = crime_data.groupby(['YEAR', 'DAY_OF_WEEK']).size().reset_index(name='count')
    day_of_week_years_data = day_of_week_years.to_dict('records')
    
    return jsonify({
        'violent_crimes_trend': violent_ts_data,
        'property_crimes_trend': property_ts_data,
        'crime_type_years': crime_type_years_data,
        'borough_years': borough_years_data,
        'time_of_day_years': time_of_day_years_data,
        'day_of_week_years': day_of_week_years_data
    })

@app.route('/api/crime-heatmap', methods=['GET'])
def get_crime_heatmap():
    global crime_data
    
    # Load data if not already loaded
    if crime_data is None:
        crime_data = load_data()
        if crime_data.empty:
            return jsonify({'error': 'Failed to load crime data'}), 500
    
    # Get all crime locations with severity
    crime_locations = crime_data[['LATITUDE', 'LONGITUDE', 'SEVERITY', 'CATEGORY', 'CRIME_TYPE']].to_dict('records')
    
    # Convert to the format needed for the heatmap
    heatmap_data = []
    for crime in crime_locations:
        heatmap_data.append({
            'lat': float(crime['LATITUDE']),
            'lng': float(crime['LONGITUDE']),
            'intensity': int(crime['SEVERITY']),
            'category': str(crime['CATEGORY']),
            'crime_type': str(crime['CRIME_TYPE'])
        })
    
    return jsonify({
        'heatmap_data': heatmap_data
    })

@app.route('/api/geocode', methods=['GET'])
def geocode_location():
    location = request.args.get('location', '')
    
    # For simplicity, we'll use hardcoded coordinates for some NYC locations
    locations = {
        'manhattan': (40.7831, -73.9712),
        'midtown': (40.7549, -73.9840),
        'upper east side': (40.7735, -73.9565),
        'upper west side': (40.7870, -73.9754),
        'chelsea': (40.7465, -74.0014),
        'greenwich village': (40.7339, -73.9976),
        'financial district': (40.7075, -74.0113),
        'harlem': (40.8116, -73.9465),
        'east village': (40.7265, -73.9815),
        'brooklyn': (40.6782, -73.9442),
        'williamsburg': (40.7081, -73.9571),
        'dumbo': (40.7032, -73.9884),
        'park slope': (40.6710, -73.9814),
        'brooklyn heights': (40.6958, -73.9936),
        'bushwick': (40.6944, -73.9213),
        'bedford-stuyvesant': (40.6872, -73.9418),
        'crown heights': (40.6694, -73.9422),
        'flatbush': (40.6409, -73.9617),
        'queens': (40.7282, -73.7949),
        'astoria': (40.7644, -73.9235),
        'long island city': (40.7447, -73.9485),
        'flushing': (40.7654, -73.8318),
        'jamaica': (40.7020, -73.8085),
        'forest hills': (40.7185, -73.8458),
        'jackson heights': (40.7556, -73.8830),
        'bronx': (40.8448, -73.8648),
        'riverdale': (40.8900, -73.9122),
        'fordham': (40.8614, -73.8908),
        'mott haven': (40.8091, -73.9229),
        'pelham bay': (40.8488, -73.8331),
        'staten island': (40.5795, -74.1502),
        'st. george': (40.6447, -74.0763),
        'todt hill': (40.6015, -74.1035),
        'great kills': (40.5544, -74.1510),
        'times square': (40.7580, -73.9855),
        'central park': (40.7812, -73.9665),
        'prospect park': (40.6602, -73.9690),
        'jfk airport': (40.6413, -73.7781),
        'laguardia airport': (40.7769, -73.8740)
    }
    
    # Check if the location matches any of our hardcoded locations
    location_lower = location.lower()
    for key, (lat, lng) in locations.items():
        if key in location_lower:
            return jsonify({
                'success': True,
                'lat': lat,
                'lng': lng,
                'display_name': location.title()
            })
    
    # If no match, return a default location (Manhattan)
    return jsonify({
        'success': True,
        'lat': 40.7831,
        'lng': -73.9712,
        'display_name': 'Manhattan, New York'
    })

if __name__ == '__main__':
    app.run(debug=True)
