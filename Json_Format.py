import os
import csv
import json

def get_sar_dimensions(measurement_folder):
    import rasterio
    tif_files = [f for f in os.listdir(measurement_folder) if f.lower().endswith('.tif') or f.lower().endswith('.tiff')]
    if tif_files:
        tif_path = os.path.join(measurement_folder, tif_files[0])
        try:
            with rasterio.open(tif_path) as src:
                return src.width, src.height
        except Exception as e:
            print(f"Could not read {tif_path}: {e}")
    else:
        print(f"No .tif or .tiff files found in {measurement_folder}")
    return None, None

def create_json_from_folders(copernicus_dir, csv_file, bbox_input, participant_name):
    # Read CSV and build lookup for image_name
    csv_lookup = {}
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_lookup[row['image_name']] = row

    # Get folder names in copernicus_data
    folders = [x for x in os.listdir(copernicus_dir) if os.path.isdir(os.path.join(copernicus_dir, x))]
    images = []
    image_name_to_id = {}
    for folder in folders:
        # Find by image_name column in CSV
        row = csv_lookup.get(folder)
        if not row:
            print(f"Warning: {folder} not found in CSV 'image_name' column, skipping.")
            continue
        image_id = int(row['S.No.(ID)'])
        eo_sar = row['EO/SAR']
        date_captured = row['time_stamp'].replace("T", " ")
        if eo_sar == "EO":
            width, height = 10980, 10980
        elif eo_sar == "SAR":
            measurement_folder = os.path.join(copernicus_dir, folder, "measurement")
            if os.path.exists(measurement_folder):
                width, height = get_sar_dimensions(measurement_folder)
            else:
                width, height = None, None
        else:
            width, height = None, None
        images.append({
            "id": image_id,
            "file_name": folder,
            "width": width,
            "height": height,
            "date_captured": date_captured
        })
        image_name_to_id[folder] = image_id

    # Build annotations
    annotations = []
    ann_id = 1
    for img_bbox in bbox_input:
        image_name = img_bbox['image_name']
        img_id = image_name_to_id.get(image_name)
        if img_id is None:
            continue
        for bbox_dict in img_bbox['bboxes']:
            annotations.append({
                "id": ann_id,
                "image_id": img_id,
                "category_id": 1,
                "bbox": bbox_dict['bbox'],
                "score": bbox_dict['score']
            })
            ann_id += 1

    # Compose output JSON
    output = {
        "info": {
            "description": "Grand challenge MDA",
            "version": "1.0",
            "year": 2025,
            "predicted_by": participant_name
        },
        "licenses": [],
        "images": images,
        "categories": [
            {"id": 1, "name": "ship"}
        ],
        "annotations": annotations
    }
    return output

# Example usage:
bbox_input = [
    {
        "image_name": "S2A_MSIL1C_20240904T151651_N0511_R025_T20TMP_20240904T221000.SAFE",
        "bboxes": [
            {"bbox": "POLYGON((46.3238122556359 12.5411993078887, 46.3255240824074 12.5411993078887, 46.3255240824074 12.5419981544837, 46.3238122556359 12.5419981544837, 46.3238122556359 12.5411993078887))", "score": 0.90},
            {"bbox": "POLYGON((46.5972081022337 11.9249537028372, 46.6011188142002 11.9249537028372, 46.6011188142002 11.9264122238383, 46.5972081022337 11.9264122238383, 46.5972081022337 11.9249537028372))", "score": 0.70},
            {"bbox": "POLYGON((46.5472708558664 12.4003420118243, 46.5482992967591 12.4003420118243, 46.5482992967591 12.4015435110778, 46.5472708558664 12.4015435110778, 46.5472708558664 12.4003420118243))", "score": 0.88},
            {"bbox": "POLYGON((46.4001002556359 12.3001993078887, 46.4015240824074 12.3001993078887, 46.4015240824074 12.3019981544837, 46.4001002556359 12.3019981544837, 46.4001002556359 12.3001993078887))", "score": 0.75},
            {"bbox": "POLYGON((46.6000001022337 12.5009537028372, 46.6041188142002 12.5009537028372, 46.6041188142002 12.5024122238383, 46.6000001022337 12.5024122238383, 46.6000001022337 12.5009537028372))", "score": 0.80}
        ]
    },
    {
        "image_name": "S2A_MSIL1C_20240910T153551_N0511_R111_T19TDF_20240910T204158.SAFE",
        "bboxes": [
            {"bbox": "POLYGON((48.3541123755276 13.0343517567962, 48.3553546620533 13.0343517567962, 48.3553546620533 13.0351278651506, 48.3541123755276 13.0351278651506, 48.3541123755276 13.0343517567962))", "score": 0.70},
            {"bbox": "POLYGON((48.4001123755276 13.1003517567962, 48.4013546620533 13.1003517567962, 48.4013546620533 13.1011278651506, 48.4001123755276 13.1011278651506, 48.4001123755276 13.1003517567962))", "score": 0.85},
            {"bbox": "POLYGON((48.5001123755276 13.2003517567962, 48.5013546620533 13.2003517567962, 48.5013546620533 13.2011278651506, 48.5001123755276 13.2011278651506, 48.5001123755276 13.2003517567962))", "score": 0.90}
        ]
    },
    {
        "image_name": "S1A_IW_GRDH_1SDV_20241109T223334_20241109T223403_056484_06EC72_FE47.SAFE",
        "bboxes": [
            {"bbox": "POLYGON((47.123 13.456, 47.124 13.456, 47.124 13.457, 47.123 13.457, 47.123 13.456))", "score": 0.85},
            {"bbox": "POLYGON((47.200 13.500, 47.201 13.500, 47.201 13.501, 47.200 13.501, 47.200 13.500))", "score": 0.80},
            {"bbox": "POLYGON((47.300 13.600, 47.301 13.600, 47.301 13.601, 47.300 13.601, 47.300 13.600))", "score": 0.78}
        ]
    },
    {
        "image_name": "S1A_IW_GRDH_1SDV_20241216T231321_20241216T231346_057024_0701EF_99B1.SAFE",
        "bboxes": [
            {"bbox": "POLYGON((48.789 14.123, 48.790 14.123, 48.790 14.124, 48.789 14.124, 48.789 14.123))", "score": 0.78},
            {"bbox": "POLYGON((48.795 14.128, 48.796 14.128, 48.796 14.129, 48.795 14.129, 48.795 14.128))", "score": 0.82},
            {"bbox": "POLYGON((48.800 14.130, 48.801 14.130, 48.801 14.131, 48.800 14.131, 48.800 14.130))", "score": 0.76}
        ]
    }
]

result = create_json_from_folders(
   "/Users/devanshkedia/Desktop/NCCIPCCC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/copernicus_data",
   "/Users/devanshkedia/Desktop/NCCIPCCC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/converted_output.csv",
   bbox_input,
   "YourName"
)
with open("output.json", "w") as f:
    json.dump(result, f, indent=2)