import json
import csv
import re

# Input/output files
input_json = "/Users/devanshkedia/Desktop/NCCIPCCC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/output_correlation.json"
output_csv = "/Users/devanshkedia/Desktop/NCCIPCCC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/output_correlation_csv.csv"

# Load the JSON
with open(input_json, 'r') as f:
    data = json.load(f)

# Build a lookup from image_id to (image_name, timestamp)
image_lookup = {img['id']: (img['file_name'], img['date_captured']) for img in data['images']}

# Prepare CSV
with open(output_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['timestamp', 'lat', 'lon', 'image_name'])

    for ann in data.get('annotations', []):
        image_id = ann['image_id']
        image_name, timestamp = image_lookup.get(image_id, ("", ""))
        bbox = ann['bbox']
        # Extract last coordinate from POLYGON string
        coords = re.findall(r"([-+]?\d*\.\d+|\d+)\s+([-+]?\d*\.\d+|\d+)", bbox)
        if coords:
            lat, lon = coords[-1]
            writer.writerow([timestamp, lat, lon, image_name])
        else:
            # If cannot parse, write empty line (optional)
            writer.writerow([timestamp, '', '', image_name])

print(f"CSV saved to {output_csv}")