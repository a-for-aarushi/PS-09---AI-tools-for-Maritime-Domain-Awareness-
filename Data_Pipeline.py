import csv
def convert_eo_sar_csv(input_file_path, output_file_path):
    """
    Converts the EO/SAR formatted CSV to a new CSV with an 'EO/SAR' column and remarks binary indicator.

    Parameters:
        input_file_path (str): Path to the original CSV file.
        output_file_path (str): Path to save the converted CSV file.
    """
    with open(input_file_path, newline='', encoding='latin-1') as infile:
        reader = csv.reader(infile)
        rows = list(reader)

    # Find EO and SAR data blocks
    data = []
    mode = None
    columns = None
    for row in rows:
        if not any(cell.strip() for cell in row):
            continue  # skip completely empty rows
        if row[0].strip() == "EO":
            mode = "EO"
            continue
        elif row[0].strip() == "SAR":
            mode = "SAR"
            continue
        elif row[0].strip().startswith("S.No.(ID)"):
            columns = row  # Save header for later
            continue
        elif mode and columns and row[0].strip().isdigit():
            # Data row
            # Pad row to columns length
            while len(row) < len(columns):
                row.append("")
            entry = {
                "EO/SAR": mode,
                columns[0]: row[0],
                columns[1]: row[1],
                columns[2]: row[2],
                columns[3]: row[3],
                columns[4]: row[4],
                "Remarks": "0" if not row[5].strip() else "1"
            }
            data.append(entry)
        else:
            continue  # skip instructions and other lines

    # Construct new columns
    new_columns = ["EO/SAR"] + columns[:5] + ["Remarks"]

    # Write output CSV
    with open(output_file_path, "w", newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=new_columns)
        writer.writeheader()
        for entry in data:
            writer.writerow(entry)

convert_eo_sar_csv("/Users/devanshkedia/Desktop/NCCIPCCC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/Imagery_details_for_vessel_detection_and_AIS_correlation.csv", "/Users/devanshkedia/Desktop/NCCIPCCC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/converted_output.csv")