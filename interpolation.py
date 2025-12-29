import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt
import os

# ============================================================
# STEP 1: LOAD DATA
# ============================================================

file_path = r"/Users/devanshkedia/Desktop/NCCIPCCC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/Test_data_for_interpolation.csv"
df = pd.read_csv(file_path)

# Clean column names
df.columns = df.columns.str.strip().str.lower()

# Convert timestamp to datetime
df['time_stamp'] = pd.to_datetime(df['time_stamp'], errors='coerce')

# Keep only relevant columns
df = df[['path_id', 'point_id', 'time_stamp',
         'point_latitude', 'point_longitude',
         'speed_on_ground', 'course_on_ground']]

# Drop rows without time or path_id
df = df.dropna(subset=['path_id', 'time_stamp'], how='any')

# Get all unique path IDs
unique_paths = df['path_id'].unique()
print(f"Found {len(unique_paths)} unique Path IDs: {unique_paths}")

# Folder (optional — not saving multiple files anymore)
os.makedirs("Interpolated_Paths", exist_ok=True)

# List to store all path outputs
all_path_results = []

# ============================================================
# LOOP OVER EACH PATH_ID
# ============================================================

for path_id_to_use in unique_paths:
    print("\n============================================================")
    print(f"Processing Path ID: {path_id_to_use}")
    print("============================================================")

    # ============================================================
    # STEP 2: SELECT PATH_ID
    # ============================================================

    data = df[df['path_id'] == path_id_to_use].sort_values('time_stamp').reset_index(drop=True)

    print(f"Total records: {len(data)}")

    # ============================================================
    # STEP 3: COUNT MISSING POINTS
    # ============================================================

    data['is_missing'] = data['point_latitude'].isna() | data['point_longitude'].isna()

    gap_counts = []
    count = 0
    for i in range(len(data)):
        if data.loc[i, 'is_missing']:
            count += 1
        else:
            if count > 0:
                gap_counts.append(count)
            count = 0
    if count > 0:
        gap_counts.append(count)

    print(f"\nTotal missing points: {sum(gap_counts)}")
    print(f"Gap sizes (missing between valid points): {gap_counts if gap_counts else 'No missing points'}")

    # ============================================================
    # STEP 4: DETECT TURNING OR STRAIGHT MOTION
    # ============================================================

    def curvature_angle(lat1, lon1, lat2, lon2, lat3, lon3):
        """Approximate turning angle (degrees) using 3 consecutive points."""

        def bearing(latA, lonA, latB, lonB):
            y = np.sin(np.radians(lonB - lonA)) * np.cos(np.radians(latB))
            x = (np.cos(np.radians(latA)) * np.sin(np.radians(latB)) -
                 np.sin(np.radians(latA)) * np.cos(np.radians(latB)) *
                 np.cos(np.radians(lonB - lonA)))
            return np.degrees(np.arctan2(y, x))

        b1 = bearing(lat1, lon1, lat2, lon2)
        b2 = bearing(lat2, lon2, lat3, lon3)
        angle = abs(b2 - b1)
        if angle > 180:
            angle = 360 - angle
        return angle

    valid = data.dropna(subset=["point_latitude", "point_longitude"])
    is_turning = False
    if len(valid) >= 3:
        angles = []
        for i in range(len(valid) - 2):
            a, b, c = valid.iloc[i], valid.iloc[i + 1], valid.iloc[i + 2]
            ang = curvature_angle(a.point_latitude, a.point_longitude,
                                  b.point_latitude, b.point_longitude,
                                  c.point_latitude, c.point_longitude)
            angles.append(ang)
        mean_angle = np.mean(angles)
        is_turning = mean_angle > 5
        print(f"\nMean turning angle: {mean_angle:.2f}° → {'Turning' if is_turning else 'Straight'} path detected.")

    # ============================================================
    # STEP 5: INTERPOLATE
    # ============================================================

    def adaptive_interpolation(series, timestamps, is_turning=False):
        """Adaptive: cubic if turning, else linear (time-based)."""
        valid_idx = ~series.isna()
        if valid_idx.sum() < 2:
            return series
        if is_turning:
            cs = CubicSpline(timestamps[valid_idx], series[valid_idx], extrapolate=False)
            return pd.Series(cs(timestamps), index=series.index)
        else:
            return series.interpolate(method='time')

    # Convert to datetime index
    data = data.set_index('time_stamp')

    # Convert timestamps to numeric (in seconds)
    timestamps = data.index.view(np.int64) / 1e9

    # Keep a copy of original data for plotting comparison
    original = data.copy()

    # Interpolate each numeric column
    for col in ["point_latitude", "point_longitude", "speed_on_ground", "course_on_ground"]:
        data[col] = adaptive_interpolation(data[col], timestamps, is_turning)

    # ============================================================
    # STEP 6: PLOT LAT-LONG TRAJECTORY
    # ============================================================

    orig_mask = original["point_latitude"].notna() & original["point_longitude"].notna()
    interp_mask = ~orig_mask

    plt.figure(figsize=(10, 8))
    plt.plot(data["point_latitude"], data["point_longitude"], color="gray", linestyle="--", alpha=0.5)
    plt.scatter(data.loc[orig_mask, "point_latitude"], data.loc[orig_mask, "point_longitude"], color="blue",
                label="Original Points", s=40, zorder=3)
    plt.scatter(data.loc[interp_mask, "point_latitude"], data.loc[interp_mask, "point_longitude"], color="red",
                label="Interpolated Points", s=40, zorder=3)
    plt.title(f"Trajectory (Lat vs Lon) - Path ID {path_id_to_use}")
    plt.xlabel("Latitude")
    plt.ylabel("Longitude")
    plt.legend()
    plt.grid(True)
    plt.show()

    # ============================================================
    # STEP 7: STORE RESULT IN LIST (no individual saving)
    # ============================================================

    data = data.reset_index()
    data['path_id'] = path_id_to_use  # ensure path_id retained
    all_path_results.append(data)

# ============================================================
# COMBINE & SAVE FINAL CSV
# ============================================================

final_df = pd.concat(all_path_results, ignore_index=True)

# Remove last column
final_df = final_df.iloc[:, :-1]

# Save as one CSV
output_path = "/Users/devanshkedia/Desktop/NCCIPCCC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/Interpolated_Paths/Final_Interpolated.csv"
final_df.to_csv(output_path, index=False)

print(f"\n🎯 All Path IDs processed successfully!")
print(f"✅ Final combined CSV saved to: {output_path}")
