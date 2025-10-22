import os
import rasterio
import numpy as np
from rasterio.plot import reshape_as_image
from PIL import Image

# Path to your main dataset
BASE_DIR = "/Users/devanshkedia/Desktop/nccipc/EO data"
OUTPUT_DIR = "/Users/devanshkedia/Desktop/nccipc/EO to RGB"

# Create output folder if not exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def combine_bands_to_rgb(img_data_path, output_path):
    # Find paths for B02, B03, and B04
    band_files = {
        'B02': None,
        'B03': None,
        'B04': None
    }

    for file in os.listdir(img_data_path):
        if file.endswith('.jp2'):
            for band in band_files.keys():
                if band in file:
                    band_files[band] = os.path.join(img_data_path, file)

    # Check if all 3 bands are found
    if None in band_files.values():
        print(f"Skipping {img_data_path} — missing one or more bands.")
        return

    # Read each band
    with rasterio.open(band_files['B04']) as red:
        R = red.read(1).astype(float)
    with rasterio.open(band_files['B03']) as green:
        G = green.read(1).astype(float)
    with rasterio.open(band_files['B02']) as blue:
        B = blue.read(1).astype(float)

    # Normalize to 0–255
    def normalize(array):
        array_min, array_max = np.percentile(array, (2, 98))
        array = np.clip(array, array_min, array_max)
        return ((array - array_min) / (array_max - array_min) * 255).astype(np.uint8)

    rgb = np.dstack((normalize(R), normalize(G), normalize(B)))

    # Save as PNG
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    Image.fromarray(rgb).save(output_path)
    print(f"Saved RGB image: {output_path}")


# Walk through all folders
for root, dirs, files in os.walk(BASE_DIR):
    if "IMG_DATA" in root:
        rel_path = os.path.relpath(root, BASE_DIR)
        output_subdir = os.path.join(OUTPUT_DIR, rel_path)
        rgb_output_path = os.path.join(output_subdir, "RGB_image.png")
        combine_bands_to_rgb(root, rgb_output_path)
