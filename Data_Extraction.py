import csv
def csv_to_dict_list(input_file_path):
    """
    Reads a CSV file and returns a list of dictionaries with 'id' and 'image_name' as keys.

    Parameters:
        input_file_path (str): Path to the CSV file.

    Returns:
        List[Dict[str, str]]: List of dictionaries with 'id' and 'image_name'.
    """
    result = []
    with open(input_file_path, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        # Try to find correct column names
        id_col = None
        image_name_col = None
        for field in reader.fieldnames:
            if field.strip().lower() in ['s.no.(id)', 'id', 's.no']:
                id_col = field
            if field.strip().lower() == 'image_name':
                image_name_col = field
        if not id_col or not image_name_col:
            raise ValueError("Could not find required columns in the CSV file.")
        for row in reader:
            if row[id_col].strip():
                result.append({
                    "id": row[id_col].strip(),
                    "image_name": row[image_name_col].strip()
                })
    return result

# Example usage:
dict_list = csv_to_dict_list("/Users/devanshkedia/Desktop/NCCIPCCC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/converted_output.csv")
print(dict_list)