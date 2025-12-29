import pandas as pd
import json
import os
import pyproj  # For projecting coordinates

# --- 1. SET YOUR FILE PATHS ---
csv_path = r"/Users/devanshkedia/Desktop/NCCIPC/CODE/Imagery_details_for_vessel_detection_and_AIS_correlation.csv"
json_path = r"/Users/devanshkedia/Desktop/NCCIPC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/RGB_outputs/detections_postNMS,S2C_MSIL1C_20250315T160531_N0511_R054_T17RPH_20250315T192720.json"
output_json_path = r"/Users/devanshkedia/Desktop/S2C_MSIL1C_20250315T160531_N0511_R054_T17RPH_20250315T192720.json"  # New output file name

# --- 2. DEFINE THE STANDARD SENTINEL-2 TILE SIZE ---
STANDARD_GEO_WIDTH_METERS = 109800.0  # 109.8km
STANDARD_GEO_HEIGHT_METERS = 109800.0  # 109.8km

# --- 3. HELPER FUNCTION ---
def convert_pixel_to_geo(px, py, center_lon, center_lat, pixel_center_x, pixel_center_y, meters_per_pixel_x,
                         meters_per_pixel_y, geod):
    """
    Converts a single pixel coordinate (px, py) to geographic (lat, lon).
    """
    # 1. Find pixel distance from center
    delta_pixel_x = px - pixel_center_x
    delta_pixel_y = py - pixel_center_y

    # 2. Convert pixel distance to meter distance
    delta_meters_x = delta_pixel_x * meters_per_pixel_x  # East/West offset
    delta_meters_y = delta_pixel_y * meters_per_pixel_y  # North/South offset

    # 3. Project from the center
    #    g.fwd(lon, lat, azimuth, distance)

    # First, move East/West (azimuth 90) by delta_meters_x
    temp_lon, temp_lat, _ = geod.fwd(center_lon, center_lat, 90, delta_meters_x)

    # Then, from that new point, move North/South
    # We use a NEGATIVE delta_meters_y because pixel Y is 0 at top,
    # but North is positive *up*. Azimuth 0 is North.
    final_lon, final_lat, _ = geod.fwd(temp_lon, temp_lat, 0, -delta_meters_y)

    return [final_lat, final_lon]


# --- 4. SCRIPT LOGIC ---
try:
    # --- Part A: Get Image Center from CSV ---
    df = pd.read_csv(csv_path, header=1)
    df.columns = df.columns.str.strip()
    center_lat = df.iloc[0]['image_centre_latitude']
    center_lon = df.iloc[0]['image_centre_longitude']
    print(f"Found Image Center: Lat={center_lat}, Lon={center_lon}")

    # --- Part B: Get Manual Pixel Dimensions ---
    print("\n--- Image Dimension Input ---")
    try:
        image_width_px = int(input("Enter the TOTAL WIDTH of the image in pixels (e.g., 10980): "))
        image_height_px = int(input("Enter the TOTAL HEIGHT of the image in pixels (e.g., 10980): "))
        if image_width_px <= 0 or image_height_px <= 0:
            raise ValueError("Dimensions must be positive")
    except ValueError as e:
        print(f"Invalid input. {e}")
        exit()

    # --- Part C: Calculate Scale and Process Detections ---
    meters_per_pixel_x = STANDARD_GEO_WIDTH_METERS / image_width_px
    meters_per_pixel_y = STANDARD_GEO_HEIGHT_METERS / image_height_px
    print("\n--- Scale Calculation ---")
    print(f"  Meters per pixel (X): {meters_per_pixel_x:.6f}")
    print(f"  Meters per pixel (Y): {meters_per_pixel_y:.6f}")

    pixel_center_x = image_width_px / 2.0
    pixel_center_y = image_height_px / 2.0

    g = pyproj.Geod(ellps='WGS84')

    with open(json_path, 'r') as f:
        detections = json.load(f)

    print(f"\nProcessing {len(detections)} detections...")
    new_detections = []

    for detection in detections:
        bbox = detection['bbox']
        y_min, x_min, y_max, x_max = bbox

        # Calculate pixel centroid
        pixel_x_cen = (x_min + x_max) / 2.0
        pixel_y_cen = (y_min + y_max) / 2.0

        # --- Create a dictionary of all points to convert ---
        points_to_convert = {
            "centroid": (pixel_x_cen, pixel_y_cen),
            "top_left": (x_min, y_min),
            "top_right": (x_max, y_min),
            "bottom_left": (x_min, y_max),
            "bottom_right": (x_max, y_max)
        }

        geo_coords = {}

        # --- Convert all points ---
        for name, (px, py) in points_to_convert.items():
            geo_coords[name] = convert_pixel_to_geo(
                px, py,
                center_lon, center_lat,
                pixel_center_x, pixel_center_y,
                meters_per_pixel_x, meters_per_pixel_y,
                g
            )

        # Add the new coordinates to the detection data
        new_detection_data = detection.copy()
        new_detection_data['geo_centroid_wgs84'] = geo_coords["centroid"]
        new_detection_data['geo_corners_wgs84'] = {
            "top_left": geo_coords["top_left"],
            "top_right": geo_coords["top_right"],
            "bottom_left": geo_coords["bottom_left"],
            "bottom_right": geo_coords["bottom_right"]
        }
        new_detections.append(new_detection_data)

    # Save the new list of detections to the output JSON file
    with open(output_json_path, 'w') as f:
        json.dump(new_detections, f, indent=4)

    print("\n--- ✅ SUCCESS ---")
    print(f"Saved {len(new_detections)} detections with all coordinates to:")
    print(output_json_path)

    # Print a sample
    print("\nSample output:")
    print(json.dumps(new_detections[0], indent=4))

except FileNotFoundError as e:
    print(f"\n--- ❌ ERROR: FILE NOT FOUND ---")
    print(f"Could not find file: {e.filename}")
except ImportError:
    print("\n--- ❌ ERROR: Missing Libraries ---")
    print("Please install the required libraries first by running:")
    print("pip install pandas pyproj")
except KeyError as e:
    print(f"\n--- ❌ ERROR: 'KeyError' ---")
    print(f"Could not find the column: {e}.")
    print("Please check your CSV file's headers. Required: 'image_centre_latitude', 'image_centre_longitude'")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")