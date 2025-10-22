# AIS Correlation Test Script
# Save this as 'ais_correlation_test.py' and run with: python ais_correlation_test.py
# Requirements: pip install pandas numpy scikit-learn (if not installed)

import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from sklearn.metrics.pairwise import haversine_distances

def correlate_detections_to_ais(detections, ais, time_threshold_minutes=5, dist_threshold_km=1.0):
    """
    Correlates ship detections to AIS data.
    
    Parameters:
    - detections: list of dicts with 'timestamp' (ISO str), 'lat' (float), 'lon' (float), 'image_name' (str)
    - ais: DataFrame with columns 'timestamp' (ISO str), 'lat' (float), 'lon' (float), 'mmsi' (int/str)
    - time_threshold_minutes: max time diff in minutes
    - dist_threshold_km: max distance in km
    
    Returns:
    DataFrame in submission format: sl.no.,time_stamp,image_name,vessel_latitude,vessel_longitude,mmsi
    """
    detections_df = pd.DataFrame(detections)
    detections_df['timestamp'] = pd.to_datetime(detections_df['timestamp'])
    
    ais_df = ais.copy()
    ais_df['timestamp'] = pd.to_datetime(ais_df['timestamp'])
    
    results = []
    for idx, det in detections_df.iterrows():
        det_time = det['timestamp']
        time_window_start = det_time - timedelta(minutes=time_threshold_minutes)
        time_window_end = det_time + timedelta(minutes=time_threshold_minutes)
        
        candidates = ais_df[
            (ais_df['timestamp'] >= time_window_start) & 
            (ais_df['timestamp'] <= time_window_end)
        ].copy()
        
        if candidates.empty:
            results.append({
                'sl_no': len(results) + 1,
                'time_stamp': det_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'image_name': det['image_name'],
                'vessel_latitude': det['lat'],
                'vessel_longitude': det['lon'],
                'mmsi': 0
            })
            continue
        
        # Compute distances in km (Haversine: expects [lat, lon] in radians)
        det_pos = np.deg2rad(np.array([[det['lat'], det['lon']]]))
        cand_pos = np.deg2rad(candidates[['lat', 'lon']].values)
        distances_km = haversine_distances(det_pos, cand_pos)[0] * 6371  # Earth radius in km
        
        valid_mask = distances_km <= dist_threshold_km
        if not np.any(valid_mask):
            results.append({
                'sl_no': len(results) + 1,
                'time_stamp': det_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'image_name': det['image_name'],
                'vessel_latitude': det['lat'],
                'vessel_longitude': det['lon'],
                'mmsi': 0
            })
        else:
            # Find closest among valid
            valid_indices = np.where(valid_mask)[0]
            min_dist_idx = np.argmin(distances_km[valid_mask])
            orig_idx = valid_indices[min_dist_idx]
            closest_mmsi = candidates.iloc[orig_idx]['mmsi']
            results.append({
                'sl_no': len(results) + 1,
                'time_stamp': det_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'image_name': det['image_name'],
                'vessel_latitude': det['lat'],
                'vessel_longitude': det['lon'],
                'mmsi': closest_mmsi
            })
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    # Sample detections (3 cases: match, match with multiple candidates, no-match)
    sample_detections = [
        # Detection 1: Matches AIS #1 (close, within time/dist)
        {'timestamp': '2024-10-01T16:05:09', 'lat': 28.43023, 'lon': -78.4079665, 
         'image_name': 'S2B_MSIL1C_20241001T160509_N0511_R054_T17RQM_20241001T204223.SAFE'},
        
        # Detection 2: Matches closest of AIS #3 & #4 (both candidates, picks #3 ~0.07 km)
        {'timestamp': '2025-01-19T16:05:09', 'lat': 27.5525722, 'lon': -79.4516483, 
         'image_name': 'S2B_MSIL1C_20250119T160509_N0511_R054_T17RPL_20250119T210239.SAFE'},
        
        # Detection 3: No match (far from AIS #5, outside dist threshold ~1.62 km)
        {'timestamp': '2025-01-29T16:05:09', 'lat': 24.8446332, 'lon': -79.4893634, 
         'image_name': 'S2B_MSIL1C_20250129T160509_N0511_R054_T17RPH_20250129T193028.SAFE'}
    ]

    # Sample AIS data (5 points; timed to match, with #5 adjusted for no-match)
    sample_ais_data = {
        'timestamp': [
            '2024-10-01T16:05:00',  # Close to Det1
            '2024-10-01T16:04:00',  # Outside time window for Det1
            '2025-01-19T16:05:00',  # Close to Det2
            '2025-01-19T16:06:00',  # Farther from Det2 but within time
            '2025-01-29T16:05:00'   # Far from Det3 (>1km)
        ],
        'lat': [28.4305, 28.4300, 27.5520, 27.5530, 24.83],
        'lon': [-78.4080, -78.4070, -79.4515, -79.4520, -79.4850],
        'mmsi': [123456789, 999888777, 987654321, 555666777, 111222333]
    }
    sample_ais = pd.DataFrame(sample_ais_data)

    # Run the test
    result_df = correlate_detections_to_ais(sample_detections, sample_ais)

    # Display results
    print("Test Results:")
    print(result_df.to_string(index=False))

    # Save to CSV for submission format
    result_df.to_csv('test_AIS_correlation.csv', index=False)
    print("\nResults saved to 'test_AIS_correlation.csv'")
    