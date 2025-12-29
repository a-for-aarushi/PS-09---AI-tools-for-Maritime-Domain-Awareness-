import numpy as np
import cv2
from ultralytics import YOLO
import matplotlib.pyplot as plt
import torch
from torch.nn.modules.container import Sequential
import math
import json
import os

# --------- Load your large image ----------
image_path = "/Users/devanshkedia/Desktop/NCCIPC/CODE/PS-09---AI-tools-for-Maritime-Domain-Awareness-/RGB_outputs/S2C_MSIL1C_20250315T160531_N0511_R054_T17RPH_20250315T192720_RGB.jpg"
image = cv2.imread(image_path)
H, W, _ = image.shape
print(f"Original size: {H}x{W}")

# --------- Model setup ----------
torch.serialization.add_safe_globals([Sequential])
model = YOLO("/Users/devanshkedia/Desktop/NCCIPC/yolov8s.pt")

tile_size = 640
stride = 128
conf_threshold = 0.25
iou_threshold = 0.0000005

# --------- Pad image globally ----------
pad_h = (math.ceil((H - tile_size) / stride) + 1) * stride + tile_size - H - stride
pad_w = (math.ceil((W - tile_size) / stride) + 1) * stride + tile_size - W - stride
image_padded = cv2.copyMakeBorder(image, 0, pad_h, 0, pad_w, cv2.BORDER_CONSTANT, value=0)
H_pad, W_pad, _ = image_padded.shape

# --------- Calculate number of sliding windows ----------
num_rows = math.ceil((H_pad - tile_size) / stride) + 1
num_cols = math.ceil((W_pad - tile_size) / stride) + 1
total_windows = num_rows * num_cols
print(f"Number of sliding windows along height: {num_rows}")
print(f"Number of sliding windows along width: {num_cols}")
print(f"Total number of sliding windows: {total_windows}")

detections = []  # pre-NMS detections

# --------- Sliding window loop ----------
for y in range(0, H_pad - tile_size + 1, stride):
    for x in range(0, W_pad - tile_size + 1, stride):
        tile = image_padded[y:y+tile_size, x:x+tile_size].copy()

        # Run YOLO on this tile
        results = model(tile, conf=conf_threshold, verbose=False)

        # Collect detections in global coordinates
        for b in results[0].boxes:
            x1, y1, x2, y2 = b.xyxy[0].cpu().numpy()
            conf = float(b.conf)
            cls = int(b.cls)
            detections.append({
                "global_bbox": [float(x1 + x), float(y1 + y), float(x2 + x), float(y2 + y)],
                "confidence": conf,
                "class": model.names[cls]
            })

print(f"Total detections before NMS: {len(detections)}")

# --------- Apply OpenCV NMS ----------
boxes = []
confidences = []
class_ids = []

for det in detections:
    x1, y1, x2, y2 = det["global_bbox"]
    boxes.append([int(x1), int(y1), int(x2 - x1), int(y2 - y1)])  # x, y, w, h
    confidences.append(det["confidence"])
    # map class name back to id
    class_ids.append(list(model.names.values()).index(det["class"]))

indices = cv2.dnn.NMSBoxes(boxes, confidences, score_threshold=conf_threshold, nms_threshold=iou_threshold)

final_detections = []
if len(indices) > 0:
    for i in indices.flatten():
        x, y, w, h = boxes[i]
        final_detections.append({
            "class": model.names[class_ids[i]],
            "confidence": confidences[i],
            "bbox": [x, y, x + w, y + h]
        })

print(f"Total detections after NMS: {len(final_detections)}")



# --------- Save detections as JSON ----------
output_dir = os.path.dirname(image_path)
pre_nms_path = os.path.join(output_dir, "detections_preNMS, S2C_MSIL1C_20250315T160531_N0511_R054_T17RPH_20250315T192720.json")
post_nms_path = os.path.join(output_dir, "detections_postNMS,S2C_MSIL1C_20250315T160531_N0511_R054_T17RPH_20250315T192720.json")

with open(pre_nms_path, "w") as f:
    json.dump(detections, f, indent=4)

with open(post_nms_path, "w") as f:
    json.dump(final_detections, f, indent=4)

print(f"✅ Saved detections_preNMS,S2C_MSIL1C_20250311T161121_N0511_R140_T16RGT_20250311T181252_RGB.json and detections_postNMS, S2C_MSIL1C_20250311T161121_N0511_R140_T16RGT_20250311T181252_RGB.json to:\n{output_dir}")


# --------- Visualization of final detections ----------
annotated_full = image.copy()
for det in final_detections:
    x1, y1, x2, y2 = map(int, det['bbox'])
    cv2.rectangle(annotated_full, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(annotated_full, f"{det['class']}:{det['confidence']:.2f}",
                (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

plt.figure(figsize=(12, 12))
plt.imshow(cv2.cvtColor(annotated_full, cv2.COLOR_BGR2RGB))
plt.axis('off')
plt.title("Detections across large image after NMS")
plt.show()

