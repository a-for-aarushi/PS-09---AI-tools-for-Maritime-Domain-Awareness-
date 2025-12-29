import os
import csv

def get_folder_path(folder_path, data_type):
    """
    Returns the specific IMG_DATA or measurement folder path inside the given folder_path.
    """
    for root, dirs, files in os.walk(folder_path):
        if data_type == "EO" and "IMG_DATA" in dirs:
            return os.path.join(root, "IMG_DATA")
        elif data_type == "SAR" and "measurement" in dirs:
            return os.path.join(root, "measurement")
    return None

def get_eo_sar_label_for_folders(data_folder, csv_file):
    # Read CSV and create a lookup dictionary
    lookup = {}
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lookup[row['image_name']] = row['EO/SAR']

    # List all subfolders in the data folder
    folders = [d for d in os.listdir(data_folder) if os.path.isdir(os.path.join(data_folder, d))]

    result = {}
    eo_paths = set()
    sar_paths = set()
    for folder in folders:
        eo_sar = lookup.get(folder, None)
        folder_full_path = os.path.join(data_folder, folder)
        if eo_sar == "EO":
            img_data_path = get_folder_path(folder_full_path, "EO")
            eo_paths.add(img_data_path)
            result[folder] = {'EO/SAR': eo_sar, 'folder_path': img_data_path}
        elif eo_sar == "SAR":
            measurement_path = get_folder_path(folder_full_path, "SAR")
            sar_paths.add(measurement_path)
            result[folder] = {'EO/SAR': eo_sar, 'folder_path': measurement_path}
        else:
            result[folder] = {'EO/SAR': eo_sar, 'folder_path': None}
        print(f"Folder: {folder} => EO/SAR: {eo_sar}, Path: {result[folder]['folder_path']}")

    # Print unique EO and SAR folder paths
    print("\nFinal result:")
    if eo_paths:
        print("Paths to IMG_DATA folders (EO):")
        for path in eo_paths:
            print(path)
    else:
        print("No EO (IMG_DATA) path found.")
    if sar_paths:
        print("Paths to measurement folders (SAR):")
        for path in sar_paths:
            print(path)
    else:
        print("No SAR (measurement) path found.")
    return result

# Example usage:
get_eo_sar_label_for_folders(
    "/Users/devanshkedia/Desktop/NCCIPCCC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/copernicus_data",
    "/PS-09---AI-tools-for-Maritime-Domain-Awareness-/converted_output.csv"
)