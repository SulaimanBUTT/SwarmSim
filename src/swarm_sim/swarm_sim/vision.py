import cv2
import numpy as np
from typing import List, Tuple


class VisionProcessor:
    def __init__(self, drone_id: str, team: str):
        self.drone_id = drone_id
        self.team = team
        
        if team == "friendly":
            self.target_color_lower = np.array([0, 0, 100])
            self.target_color_upper = np.array([10, 255, 255])
            self.target_name = "ENEMY"
        else:
            self.target_color_lower = np.array([100, 0, 0])
            self.target_color_upper = np.array([255, 255, 100])
            self.target_name = "FRIENDLY"
    
    def detect_drones(self, image_data: np.ndarray) -> List[Tuple]:
        if image_data is None or len(image_data.shape) != 3:
            return []
        
        hsv = cv2.cvtColor(image_data, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.target_color_lower, self.target_color_upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 50:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    detections.append((cx, cy, area))
        
        return detections
    
    def estimate_distance(self, drone_area: float, image_width: int = 640) -> float:
        if drone_area < 1:
            return 100.0
        distance = 500.0 / np.sqrt(drone_area)
        return max(0.5, min(100.0, distance))
    
    def estimate_bearing(self, drone_x: int, image_width: int = 640) -> float:
        center_x = image_width / 2
        bearing = ((drone_x - center_x) / center_x) * 90.0
        return bearing


class DroneTracker:
    def __init__(self):
        self.tracked_drones = {}
        self.frame_count = 0
    
    def update(self, detections: List[Tuple]) -> dict:
        self.frame_count += 1
        confirmed = {}
        for i, (x, y, area) in enumerate(detections):
            drone_id = f"detected_{i}"
            confirmed[drone_id] = {
                'position': (x, y),
                'area': area,
                'confidence': 0.9
            }
        return confirmed
