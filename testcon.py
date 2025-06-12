import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
import os

def test_map_generation(location_coords=(13.7563, 100.5018), zoom=8, output_filename="test_map.png"):
    """
    Generates a static map image for testing purposes.
    """
    print(f"Attempting to generate map at coords: {location_coords}, zoom: {zoom}")
    print(f"Output will be saved to: {output_filename}")

    # Create a dummy GeoDataFrame for the extent, or use your actual spatial data
    gdf = gpd.GeoDataFrame({
        'geometry': [gpd.points_from_xy([location_coords[1]], [location_coords[0]])[0]],
        'name': ['Center']
    }, crs="EPSG:4326") # WGS84

    # Convert to a projected CRS that contextily works well with
    gdf_proj = gdf.to_crs(epsg=3857) # Web Mercator

    fig, ax = plt.subplots(figsize=(8, 6), dpi=300) # Standard size for testing
    
    try:
        ctx.add_basemap(ax, crs=gdf_proj.crs.to_string(), source=ctx.providers.Esri.WorldStreetMap, zoom=zoom)
        print("Basemap added successfully.")
    except Exception as e:
        print(f"ERROR: Failed to add basemap. Please check your internet connection and try a different zoom level or provider.")
        print(f"Error details: {e}")
        ax.set_title("Map loading failed. Check internet connection or zoom.")
        ax.set_facecolor('lightgray')

    ax.set_axis_off()
    plt.tight_layout(pad=0)

    try:
        plt.savefig(output_filename, format='png', bbox_inches='tight', pad_inches=0)
        print(f"Map saved to {output_filename}")
    except Exception as e:
        print(f"ERROR: Failed to save map image to file: {e}")
    
    plt.close(fig) # Close the plot to free memory

if __name__ == "__main__":
    # Test 1: Using Bangkok coordinates and a moderate zoom
    print("\n--- Test 1: Bangkok, zoom 12 ---")
    test_map_generation(location_coords=(13.7563, 100.5018), zoom=12, output_filename="test_map_bangkok_z12.png")

    # Test 2: Using the same coordinates but a lower zoom (should show broader area)
    print("\n--- Test 2: Bangkok, zoom 8 ---")
    test_map_generation(location_coords=(13.7563, 100.5018), zoom=8, output_filename="test_map_bangkok_z8.png")

    # Test 3: Using the same coordinates but a higher zoom (may or may not show more detail depending on data availability)
    print("\n--- Test 3: Bangkok, zoom 16 ---")
    test_map_generation(location_coords=(13.7563, 100.5018), zoom=16, output_filename="test_map_bangkok_z16.png")

    # Test 4: Try a different map provider (sometimes default might have issues)
    # Check ctx.providers for more options. Common ones are Stamen.Toner, ESRI.WorldStreetMap
    print("\n--- Test 4: Bangkok, zoom 12, different provider (Stamen Toner) ---")
    
    # You'll need to modify the test_map_generation function temporarily for this,
    # or create a new test function as ctx.add_basemap source is hardcoded.
    # For now, manually try modifying source in the main function
    # In test_map_generation, change:
    # source=ctx.providers.OpenStreetMap.Mapnik
    # TO:
    # source=ctx.providers.Stamen.Toner
    
    # Rerun the script after changing provider source in the function
    # test_map_generation(location_coords=(13.7563, 100.5018), zoom=12, output_filename="test_map_bangkok_stamen.png")
    # Please revert the source back to OpenStreetMap.Mapnik after testing if you want to use the default
    
    print("\n-- Please check the generated 'test_map_*.png' files to see if maps are appearing. --")
    print("-- Also, check the console output for any 'ERROR' messages. --")