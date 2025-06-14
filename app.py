import pandas as pd
import folium

# --- 1. Load the data ---
csv_file = '/Users/alex/Downloads/Contact (res.partner).csv'
try:
    df = pd.read_csv(csv_file)
    print(f"Successfully loaded {csv_file}")
except FileNotFoundError:
    print(f"Error: {csv_file} not found. Please make sure the file is in the same directory.")
    exit()

# --- 2. Clean and validate coordinate data ---
# Ensure latitude and longitude columns are numeric, converting non-numeric values to NaN (Not a Number)
df['Geo Latitude'] = pd.to_numeric(df['Geo Latitude'], errors='coerce')
df['Geo Longitude'] = pd.to_numeric(df['Geo Longitude'], errors='coerce')

# Keep track of rows with invalid or missing coordinates
invalid_rows = df[df['Geo Latitude'].isnull() | df['Geo Longitude'].isnull()]
if not invalid_rows.empty:
    print("\nWarning: The following rows have invalid or missing coordinates and will be skipped:")
    print(invalid_rows[['Name', 'Geo Latitude', 'Geo Longitude']])

# Drop rows where coordinates are missing
df_located = df.dropna(subset=['Geo Latitude', 'Geo Longitude'])

# --- 3. Create the map and add markers ---
if not df_located.empty:
    # Create a map. The location and zoom will be set automatically by fit_bounds.
    my_map = folium.Map()

    print("\nAdding markers to the map...")
    # Add a marker for each location
    for idx, row in df_located.iterrows():
        # Create a combined address string for the popup
        full_address = f"{row['Street']}, {row['Zip']} {row['City']}, {row['Country']}"
        popup_text = f"<b>{row['Name']}</b><br>{full_address}"

        folium.Marker(
            location=[row['Geo Latitude'], row['Geo Longitude']],
            popup=popup_text,
            tooltip=row['Name']  # Shows the name on hover
        ).add_to(my_map)
        print(f" - Added: {row['Name']}")

    # --- 4. Automatically set the zoom level to fit all markers ---
    # Handle the case of a single point, which has no "bounds"
    if len(df_located) == 1:
        my_map.location = [df_located['Geo Latitude'].iloc[0], df_located['Geo Longitude'].iloc[0]]
        my_map.zoom_start = 13  # A good zoom level for a city view
    else:
        # If there are multiple points, fit the map to their bounds
        sw = [df_located['Geo Latitude'].min(), df_located['Geo Longitude'].min()]
        ne = [df_located['Geo Latitude'].max(), df_located['Geo Longitude'].max()]
        my_map.fit_bounds([sw, ne])

    # --- 5. Save the map to an HTML file ---
    output_filename = 'index.html'
    my_map.save(output_filename)

    print(f"\nMap has been created and saved as '{output_filename}'!")
    print("The map will automatically zoom to fit all destinations.")
else:
    print("\nNo valid locations with coordinates found in the file. The map was not created.")