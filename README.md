# Crime Rate Analysis & Awareness System

![Project Banner](https://raw.githubusercontent.com/vikramdatthb/Crime-Rate-Analysis-Awareness-System/refs/heads/main/images/screenshot_3_18_2025_6-58-58%20AM.png)

## Project Overview

This comprehensive data analysis project focuses on urban crime data, providing powerful insights into crime patterns, safety metrics, and risk assessment. The system leverages advanced data processing techniques, statistical analysis, and interactive visualizations to transform raw crime data into actionable safety intelligence for urban navigation and awareness.

## Key Features

- **Crime Hotspot Identification**: Utilizes geospatial analysis to identify and visualize high-risk areas across urban environments
- **Route Safety Analysis**: Analyzes crime patterns along specific routes to calculate safety scores
- **Temporal Pattern Analysis**: Examines crime distribution across different times of day, days of the week, and trends over time
- **Crime Category Analysis**: Identifies and ranks the most common types of crimes by location and severity
- **Severity Classification**: Categorizes crimes based on a custom severity scoring algorithm
- **District-level Insights**: Provides comparative analysis of crime patterns across different urban districts
- **Interactive Data Exploration**: Enables dynamic filtering and visualization of crime data

## Data Processing Pipeline

The project implements a robust data processing pipeline that handles crime data:

1. **Data Generation/Acquisition**: Creates synthetic crime data with realistic patterns (or can be replaced with real data)
2. **Data Cleaning**: Removes invalid entries and handles missing values
3. **Feature Engineering**: 
   - Extracts temporal features (time of day, day of week, month, year)
   - Categorizes crimes by type, severity, and location
   - Calculates derived metrics for analysis
4. **Statistical Analysis**: Performs aggregations and calculations to identify patterns and trends
5. **Visualization Generation**: Creates interactive visualizations for data exploration

```python
# Example of time categorization from the codebase
def categorize_time(hour):
    if 5 <= hour < 12:
        return 'Morning'
    elif 12 <= hour < 17:
        return 'Afternoon'
    elif 17 <= hour < 21:
        return 'Evening'
    else:
        return 'Night'
```

## Project Components

### 1. Data Generation Module
The `generate_data.py` script creates a realistic crime dataset:

- Generates synthetic crime data with realistic patterns across urban areas
- Creates a diverse set of crime types across different categories:
  - Violent crimes (homicide, assault, robbery, etc.)
  - Property crimes (burglary, theft, vandalism, etc.)
- Assigns realistic attributes to each crime:
  - Geographic coordinates within neighborhoods
  - Temporal patterns (date, time, day of week)
  - Severity scores based on crime type
  - Victim counts and property damage values
- Distributes crimes across districts and neighborhoods with realistic patterns

### 2. Core Analysis Engine
The core analysis functionality in `app.py` provides:

- **Data Summary Statistics**: Calculates key metrics like total crimes, violent crimes, and property crimes
- **Geospatial Analysis**: Identifies crime clusters and hotspots
- **Route Safety Algorithm**: Implements a custom algorithm that:
  - Creates a buffer zone around routes
  - Identifies crimes within proximity
  - Calculates distance-weighted safety scores
  - Classifies routes into safety categories (High, Medium, Low)
- **Trend Analysis**: Examines crime patterns over time and by location
- **Category Analysis**: Identifies correlations between crime types and other factors

```python
# route safety scoring algorithm
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
```

### 3. Data Visualization System

![Data Visualization](https://raw.githubusercontent.com/vikramdatthb/Crime-Rate-Analysis-Awareness-System/refs/heads/main/images/screenshot_3_18_2025_7-17-37%20AM.png)
![Data Visualization](https://raw.githubusercontent.com/vikramdatthb/Crime-Rate-Analysis-Awareness-System/refs/heads/main/images/Screenshot%202025-03-18%20080346.png)

The project includes a comprehensive data visualization system:

- **Interactive Crime Map**: 
  - Heat map visualization of crime density
  - Cluster visualization for areas with multiple crimes
  - Color-coded markers based on crime category and severity
  - Detailed popups with crime information
- **Time Series Analysis**: 
  - Crime trends over months and years
  - Comparative analysis of violent vs. property crimes over time
- **Categorical Visualizations**:
  - Crime type distribution
  - District-level crime comparison
  - Time of day analysis
  - Day of week patterns

### 4. Route Safety Analysis
The route safety analysis feature provides:

- **Address Geocoding**: Converts user-entered locations to geographic coordinates
- **Route Generation**: Creates a realistic route between start and end points
- **Proximity Analysis**: Identifies crimes within a specified distance of the route
- **Safety Scoring**: Calculates a comprehensive safety score based on:
  - Number of crimes near the route
  - Severity of nearby crimes
  - Presence of violent crimes
  - Recency of criminal activity
- **Risk Assessment**: Provides a safety level classification (High, Medium, Low)
- **Crime Statistics**: Summarizes crime patterns specific to the analyzed route

## Technical Implementation

### Data Analysis Technologies

- **Pandas & NumPy**: Core data processing and numerical analysis
- **Geospatial Analysis**: Custom algorithms for route safety assessment and crime clustering
- **Statistical Analysis**: Pattern recognition and trend identification
- **Data Visualization**: Interactive charts and maps for data exploration

### Data Visualization Techniques

- **Heat Maps**: Visualize crime density across geographic areas
- **Cluster Analysis**: Group nearby crimes for better visualization
- **Time Series Analysis**: Track crime trends over time
- **Categorical Charts**: Compare crime types, districts, and other factors
- **Choropleth Maps**: Display district-level statistics

### Web Development Implementation
While data analysis is the primary focus of this project, a lightweight web application was developed to make the insights accessible and interactive:

- **Flask Framework**: Powers the main application backend, handling data requests and API endpoints
- **Leaflet.js**: Renders interactive maps with crime markers, clusters, and route visualization
- **Chart.js**: Creates responsive, animated data visualizations for the dashboard
- **AJAX**: Enables asynchronous data loading for seamless user experience
- **Responsive Design**: Ensures accessibility across devices with modern CSS techniques

The web implementation follows a modular architecture:
1. **Backend API**: RESTful endpoints provide processed data to the frontend
2. **Interactive Maps**: Visualize geospatial data with custom overlays
3. **Dynamic Dashboards**: Real-time filtering and exploration of crime data
4. **Route Analysis Interface**: User-friendly input for location-based safety analysis

```javascript
//cluster implementation with Leaflet.js
clusterGroup = L.markerClusterGroup({
    maxClusterRadius: 30,
    iconCreateFunction: function(cluster) {
        const count = cluster.getChildCount();
        let size = 'small';
        if (count > 10) size = 'medium';
        if (count > 20) size = 'large';
        
        return L.divIcon({
            html: `<div class="cluster-icon cluster-${size}">${count}</div>`,
            className: 'custom-cluster-icon',
            iconSize: L.point(40, 40)
        });
    }
});
```

## Key Insights

The analysis reveals several important patterns in crime data:

- **Temporal Patterns**: Crimes show distinct patterns by time of day and day of week
- **Geographic Hotspots**: Certain neighborhoods consistently show higher crime rates
- **Crime Type Distribution**: Different areas show varying patterns of violent vs. property crimes
- **Severity Variations**: Crime severity varies significantly across different districts
- **Seasonal Trends**: Crime rates fluctuate throughout the year with identifiable patterns

## Future Enhancements

- Implement predictive modeling to forecast crime likelihood in different areas
- Incorporate demographic and socioeconomic data for more nuanced analysis
- Develop machine learning algorithms for pattern recognition and anomaly detection
- Add real-time data integration for up-to-date crime information
- Expand the analysis to include weather, events, and other external factors that may influence crime rates

## Installation and Usage

```bash
# Clone the repository
git clone https://github.com/yourusername/crime-analysis.git

# Install required packages
pip install -r requirements.txt

# Generate sample crime data (if not using real data)
python generate_data.py

# Start the application
python run.py
```

## Project Structure

```
crime-analysis/
├── app.py                      # Main Flask application
├── generate_data.py            # Data generation script
├── checkrequirements.py        # Dependency checker
├── run.py                      # Application runner
├── crime_data.csv              # Generated/processed crime data
├── static/                     # Static assets
│   ├── css/
│   │   └── style.css           # Custom styling
│   └── js/
│       └── main.js             # Client-side functionality
└── templates/                  # HTML templates
    └── index.html              # Main application template
```

## Conclusion

This Crime Rate Analysis & Awareness System demonstrates advanced data analysis techniques applied to urban safety data. By transforming crime records into actionable insights, the project showcases the power of data analysis for understanding complex urban safety patterns and potentially informing personal safety decisions and policy planning.

---

*Note: This project was developed for data analysis and visualization purposes. The safety scores and recommendations should not be used as the sole basis for navigation decisions or personal safety planning.*
