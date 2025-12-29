import json
import csv

# File paths
output_json_path = "/Users/devanshkedia/Desktop/NCCIPCCC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/output.json"
converted_csv_path = "/Users/devanshkedia/Desktop/NCCIPCCC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/converted_output.csv"
correlation_json_path = "/Users/devanshkedia/Desktop/NCCIPCCC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/output_correlation.json"

# Step 1: Read output.json
with open(output_json_path, "r") as f:
    data = json.load(f)

# Step 2: Build lookup from converted_output.csv
remarks_lookup = {}
with open(converted_csv_path, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        remarks_lookup[row["image_name"]] = row["Remarks"]

# Step 3: Filter images list
filtered_images = [
    img for img in data["images"]
    if remarks_lookup.get(img["file_name"], "0") == "1"
]

# Step 4: Build set of kept image IDs
kept_image_ids = set(img["id"] for img in filtered_images)

# Step 5: Filter annotations for those image IDs only
filtered_annotations = [
    ann for ann in data.get("annotations", [])
    if ann["image_id"] in kept_image_ids
]

# Step 6: Compose output_correlation.json
filtered_data = {
    "info": data["info"],
    "licenses": data["licenses"],
    "images": filtered_images,
    "categories": data["categories"],
    "annotations": filtered_annotations
}

with open(correlation_json_path, "w") as f:
    json.dump(filtered_data, f, indent=2)

print(f"output_correlation.json created with {len(filtered_images)} images and {len(filtered_annotations)} annotations.")