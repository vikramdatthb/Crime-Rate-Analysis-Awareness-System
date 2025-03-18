// Initialize the map
let map = L.map('map').setView([40.7128, -74.0060], 11); // NYC coordinates

// Add OpenStreetMap tile layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
}).addTo(map);

// Variables to store markers and layers
let fromMarker = null;
let toMarker = null;
let routeLine = null;
let crimeMarkers = [];
let clusterGroup = null;

// Initialize charts
let timeSeriesChart = null;
let crimeTypeChart = null;
let timeOfDayChart = null;
let boroughChart = null;

// Function to load data summary and initialize dashboard
function loadDataSummary() {
    showLoading();
    
    fetch('/api/data-summary')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        
        // Update summary statistics
        document.getElementById('total-crimes').textContent = data.total_crimes.toLocaleString();
        document.getElementById('violent-crimes').textContent = data.violent_crimes.toLocaleString();
        document.getElementById('property-crimes').textContent = data.property_crimes.toLocaleString();
        
        // Initialize dashboard charts
        initializeTimeSeriesChart(data.time_series_data);
        initializeCrimeTypeChart(data.crime_type_counts);
        initializeTimeOfDayChart(data.time_of_day_counts);
        initializeBoroughChart(data.borough_counts);
    })
    .catch(error => {
        hideLoading();
        console.error('Error loading data summary:', error);
        alert('Error loading data summary. Please try again.');
    });
}

// Function to geocode an address (convert address to coordinates)
function geocodeAddress(address) {
    return new Promise((resolve, reject) => {
        fetch(`/api/geocode?location=${encodeURIComponent(address)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                resolve([data.lat, data.lng]);
            } else {
                reject(new Error('Geocoding failed'));
            }
        })
        .catch(error => {
            console.error('Error geocoding address:', error);
            reject(error);
        });
    });
}

// Function to clear all markers and layers
function clearMap() {
    // Remove markers
    if (fromMarker) map.removeLayer(fromMarker);
    if (toMarker) map.removeLayer(toMarker);
    if (routeLine) map.removeLayer(routeLine);
    
    // Remove crime markers
    crimeMarkers.forEach(marker => map.removeLayer(marker));
    crimeMarkers = [];
    
    // Remove cluster group if exists
    if (clusterGroup) map.removeLayer(clusterGroup);
    clusterGroup = L.markerClusterGroup();
}

// Function to analyze the route and display results
function analyzeRoute() {
    const fromLocation = document.getElementById('from-location').value;
    const toLocation = document.getElementById('to-location').value;
    
    if (!fromLocation || !toLocation) {
        alert('Please enter both starting and destination locations');
        return;
    }
    
    // Clear previous markers and layers
    clearMap();
    
    // Show loading state
    showLoading();
    document.getElementById('analyze-btn').textContent = 'Analyzing...';
    
    // Geocode the addresses
    Promise.all([
        geocodeAddress(fromLocation),
        geocodeAddress(toLocation)
    ])
    .then(([fromCoords, toCoords]) => {
        // Add markers for from and to locations
        fromMarker = L.marker(fromCoords, { 
            title: 'From: ' + fromLocation,
            icon: L.divIcon({
                className: 'custom-div-icon',
                html: `<div style="background-color:#3a0ca3;color:white;border-radius:50%;width:30px;height:30px;display:flex;justify-content:center;align-items:center;box-shadow:0 0 10px rgba(0,0,0,0.5);"><i class="fas fa-map-marker-alt"></i></div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        })
        .addTo(map)
        .bindPopup('From: ' + fromLocation);
        
        toMarker = L.marker(toCoords, { 
            title: 'To: ' + toLocation,
            icon: L.divIcon({
                className: 'custom-div-icon',
                html: `<div style="background-color:#f72585;color:white;border-radius:50%;width:30px;height:30px;display:flex;justify-content:center;align-items:center;box-shadow:0 0 10px rgba(0,0,0,0.5);"><i class="fas fa-flag-checkered"></i></div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        })
        .addTo(map)
        .bindPopup('To: ' + toLocation);
        
        // Get a proper route path using OpenStreetMap's OSRM service
        showLoading();
        
        // Construct the OSRM API URL (using the public demo server)
        const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${fromCoords[1]},${fromCoords[0]};${toCoords[1]},${toCoords[0]}?overview=full&geometries=geojson`;
        
        // Return a promise that will be resolved with the API response
        return new Promise((resolve, reject) => {
            // Fetch the route from OSRM
            fetch(osrmUrl)
            .then(response => response.json())
            .then(data => {
                if (data.code !== 'Ok' || !data.routes || data.routes.length === 0) {
                    throw new Error('Failed to get route from OSRM');
                }
                
                // Get the route geometry (array of coordinates)
                const routeGeometry = data.routes[0].geometry.coordinates;
                
                // OSRM returns coordinates as [longitude, latitude], but Leaflet expects [latitude, longitude]
                const routeCoordinates = routeGeometry.map(coord => [coord[1], coord[0]]);
                
                // Create a polyline for the route
                routeLine = L.polyline(routeCoordinates, { 
                    color: '#4361ee', 
                    weight: 5,
                    opacity: 0.9,
                    lineCap: 'round'
                })
                .addTo(map);
                
                // Fit the map to show the entire route
                map.fitBounds(routeLine.getBounds(), { padding: [50, 50] });
                
                // Call the API to get crimes along the route, passing the full route path
                return fetch('/api/crimes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        from_lat: fromCoords[0],
                        from_lng: fromCoords[1],
                        to_lat: toCoords[0],
                        to_lng: toCoords[1],
                        route_coordinates: routeCoordinates
                    })
                });
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Resolve the promise with the data
                resolve(data);
            })
            .catch(error => {
                console.error('Error getting route:', error);
                
                // Fallback to a simple straight line if the routing service fails
                console.log('Falling back to simple straight line route');
                routeLine = L.polyline([fromCoords, toCoords], { 
                    color: '#4361ee', 
                    weight: 5,
                    opacity: 0.7,
                    dashArray: '10, 10',
                    lineCap: 'round'
                })
                .addTo(map);
                
                // Fit the map to show both markers
                map.fitBounds(routeLine.getBounds(), { padding: [50, 50] });
                
                // Call the API to get crimes along the route (without detailed path)
                fetch('/api/crimes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        from_lat: fromCoords[0],
                        from_lng: fromCoords[1],
                        to_lat: toCoords[0],
                        to_lng: toCoords[1]
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // Resolve the promise with the data
                    resolve(data);
                })
                .catch(err => {
                    // If everything fails, reject the promise
                    reject(err);
                });
            });
        });
    })
    .then(data => {
        // Reset button text
        document.getElementById('analyze-btn').textContent = 'Analyze Route';
        hideLoading();
        
        // Show results container
        document.getElementById('results-container').style.display = 'block';
        
        // Update safety score
        const safetyScoreElement = document.getElementById('safety-score-value');
        safetyScoreElement.textContent = data.safety_score;
        
        // Set color and class based on safety level
        const safetyLevelElement = document.getElementById('safety-level');
        safetyLevelElement.textContent = data.safety_level + ' Safety';
        
        // Remove all safety classes
        safetyLevelElement.classList.remove('high-safety', 'medium-safety', 'low-safety');
        
        if (data.safety_level === 'Low') {
            safetyScoreElement.style.color = '#e63946'; // Danger color
            safetyLevelElement.classList.add('low-safety');
        } else if (data.safety_level === 'Medium') {
            safetyScoreElement.style.color = '#f8961e'; // Warning color
            safetyLevelElement.classList.add('medium-safety');
        } else {
            safetyScoreElement.style.color = '#4cc9f0'; // Success color
            safetyLevelElement.classList.add('high-safety');
        }
        
        // Update crime statistics
        document.getElementById('crime-count').textContent = data.crimes.length;
        
        // Initialize cluster group for crime markers
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
        
        // Process each crime
        data.crimes.forEach(crime => {
            // Create marker for each crime
            const markerIcon = L.divIcon({
                className: 'custom-div-icon',
                html: `<div class="crime-marker ${crime.category === 'Violent Crimes' ? 'violent-marker' : 'property-marker'}" style="width:20px;height:20px;font-size:12px;">${crime.severity}</div>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });
            
            const marker = L.marker([crime.latitude, crime.longitude], { 
                icon: markerIcon,
                title: crime.crime_type
            });
            
            // Create popup content
            let severityClass = 'severity-low';
            if (crime.severity >= 7) {
                severityClass = 'severity-high';
            } else if (crime.severity >= 4) {
                severityClass = 'severity-medium';
            }
            
            let popupContent = `
                <div class="crime-popup">
                    <h3>${crime.crime_type}</h3>
                    <p><strong>Date:</strong> ${crime.date}</p>
                    <p><strong>Time:</strong> ${crime.time} (${crime.time_of_day})</p>
                    <p><strong>Location:</strong> ${crime.street_address}, ${crime.neighborhood}, ${crime.borough}</p>
                    <p><strong>Category:</strong> ${crime.category}</p>
                    <p><strong>Status:</strong> ${crime.status}</p>
                    <p><strong>Severity:</strong> <span class="severity ${severityClass}">${crime.severity}/10</span></p>
                    ${crime.victims > 0 ? `<p><strong>Victims:</strong> ${crime.victims}</p>` : ''}
                    ${crime.property_damage > 0 ? `<p><strong>Property Damage:</strong> $${crime.property_damage.toLocaleString()}</p>` : ''}
                </div>
            `;
            
            marker.bindPopup(popupContent);
            crimeMarkers.push(marker);
            clusterGroup.addLayer(marker);
        });
        
        // Add cluster group to map
        map.addLayer(clusterGroup);
        
        // Update crime statistics if available
        if (data.crime_stats && Object.keys(data.crime_stats).length > 0) {
            updateCrimeStatistics(data.crime_stats);
        }
        
        // Bring route line to front if it exists
        if (routeLine && typeof routeLine.bringToFront === 'function') {
            routeLine.bringToFront();
        }
        
        // No need to bring markers to front as they're already on top layer
        // This fixes the "fromMarker.bringToFront is not a function" error
    })
    .catch(error => {
        console.error('Error analyzing route:', error);
        document.getElementById('analyze-btn').textContent = 'Analyze Route';
        hideLoading();
        
        // Show a more detailed error message
        let errorMessage = 'Error analyzing route. ';
        
        if (error.message) {
            errorMessage += error.message;
        } else {
            errorMessage += 'Please try again.';
        }
        
        alert(errorMessage);
    });
}

// Function to update crime statistics in the UI
function updateCrimeStatistics(crimeStats) {
    // Update crime types list
    const crimeTypesList = document.getElementById('crime-types-list');
    crimeTypesList.innerHTML = '';
    
    // Sort crime types by count
    const sortedCrimeTypes = Object.entries(crimeStats.crime_types)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5); // Top 5 crime types
    
    sortedCrimeTypes.forEach(([type, count]) => {
        const li = document.createElement('li');
        li.innerHTML = `${type} <span class="crime-count">${count}</span>`;
        crimeTypesList.appendChild(li);
    });
    
    // If no crime types found
    if (sortedCrimeTypes.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'No specific crime types identified';
        crimeTypesList.appendChild(li);
    }
    
    // Update crime statistics
    document.getElementById('violent-count').textContent = 
        Object.entries(crimeStats.crime_categories)
            .find(([category, _]) => category === 'Violent Crimes')?.[1] || 0;
    
    document.getElementById('property-count').textContent = 
        Object.entries(crimeStats.crime_categories)
            .find(([category, _]) => category === 'Property Crimes')?.[1] || 0;
    
    document.getElementById('avg-severity').textContent = 
        crimeStats.avg_severity.toFixed(1);
    
    document.getElementById('total-victims').textContent = 
        crimeStats.total_victims;
    
    document.getElementById('total-damage').textContent = 
        '$' + crimeStats.total_property_damage.toLocaleString();
}

// Function to initialize time series chart
function initializeTimeSeriesChart(data) {
    const ctx = document.getElementById('time-series-chart').getContext('2d');
    
    // Sort data by date
    data.sort((a, b) => new Date(a.date) - new Date(b.date));
    
    // Extract dates and counts
    const dates = data.map(item => item.date);
    const counts = data.map(item => item.count);
    
    // Create chart
    if (timeSeriesChart) {
        timeSeriesChart.destroy();
    }
    
    timeSeriesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Number of Crimes',
                data: counts,
                backgroundColor: 'rgba(67, 97, 238, 0.2)',
                borderColor: 'rgba(67, 97, 238, 1)',
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 3,
                pointBackgroundColor: 'rgba(67, 97, 238, 1)',
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Crime Trends Over Time',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}

// Function to initialize crime type chart
function initializeCrimeTypeChart(data) {
    const ctx = document.getElementById('crime-type-chart').getContext('2d');
    
    // Sort data by count
    const sortedData = Object.entries(data)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8); // Top 8 crime types
    
    // Extract crime types and counts
    const crimeTypes = sortedData.map(item => item[0]);
    const counts = sortedData.map(item => item[1]);
    
    // Create chart
    if (crimeTypeChart) {
        crimeTypeChart.destroy();
    }
    
    crimeTypeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: crimeTypes,
            datasets: [{
                label: 'Number of Crimes',
                data: counts,
                backgroundColor: [
                    'rgba(230, 57, 70, 0.7)',
                    'rgba(241, 92, 38, 0.7)',
                    'rgba(248, 150, 30, 0.7)',
                    'rgba(249, 199, 79, 0.7)',
                    'rgba(144, 190, 109, 0.7)',
                    'rgba(67, 170, 139, 0.7)',
                    'rgba(77, 144, 142, 0.7)',
                    'rgba(87, 117, 144, 0.7)'
                ],
                borderColor: [
                    'rgba(230, 57, 70, 1)',
                    'rgba(241, 92, 38, 1)',
                    'rgba(248, 150, 30, 1)',
                    'rgba(249, 199, 79, 1)',
                    'rgba(144, 190, 109, 1)',
                    'rgba(67, 170, 139, 1)',
                    'rgba(77, 144, 142, 1)',
                    'rgba(87, 117, 144, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Most Common Crime Types',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}

// Function to initialize time of day chart
function initializeTimeOfDayChart(data) {
    const ctx = document.getElementById('time-of-day-chart').getContext('2d');
    
    // Extract time of day and counts
    const timeOfDay = Object.keys(data);
    const counts = Object.values(data);
    
    // Create chart
    if (timeOfDayChart) {
        timeOfDayChart.destroy();
    }
    
    timeOfDayChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: timeOfDay,
            datasets: [{
                data: counts,
                backgroundColor: [
                    'rgba(255, 209, 102, 0.7)', // Morning
                    'rgba(255, 159, 64, 0.7)',  // Afternoon
                    'rgba(54, 162, 235, 0.7)',  // Evening
                    'rgba(46, 49, 146, 0.7)'    // Night
                ],
                borderColor: [
                    'rgba(255, 209, 102, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(46, 49, 146, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Crimes by Time of Day',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// Function to initialize borough chart
function initializeBoroughChart(data) {
    const ctx = document.getElementById('borough-chart').getContext('2d');
    
    // Extract boroughs and counts
    const boroughs = Object.keys(data);
    const counts = Object.values(data);
    
    // Create chart
    if (boroughChart) {
        boroughChart.destroy();
    }
    
    boroughChart = new Chart(ctx, {
        type: 'polarArea',
        data: {
            labels: boroughs,
            datasets: [{
                data: counts,
                backgroundColor: [
                    'rgba(58, 12, 163, 0.7)',  // Primary color
                    'rgba(67, 97, 238, 0.7)',  // Secondary color
                    'rgba(76, 201, 240, 0.7)', // Success color
                    'rgba(247, 37, 133, 0.7)', // Accent color
                    'rgba(114, 9, 183, 0.7)'   // Another purple
                ],
                borderColor: [
                    'rgba(58, 12, 163, 1)',
                    'rgba(67, 97, 238, 1)',
                    'rgba(76, 201, 240, 1)',
                    'rgba(247, 37, 133, 1)',
                    'rgba(114, 9, 183, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Crimes by Borough',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// Function to show loading spinner
function showLoading() {
    document.getElementById('loading-spinner').style.display = 'flex';
}

// Function to hide loading spinner
function hideLoading() {
    document.getElementById('loading-spinner').style.display = 'none';
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Load data summary and initialize dashboard
    loadDataSummary();
    
    // Add event listener to the analyze button
    document.getElementById('analyze-btn').addEventListener('click', analyzeRoute);
    
    // Add event listeners for Enter key in input fields
    document.getElementById('from-location').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('to-location').focus();
        }
    });
    
    document.getElementById('to-location').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            analyzeRoute();
        }
    });
});
