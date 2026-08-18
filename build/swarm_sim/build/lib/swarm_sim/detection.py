"""
Drone detection module using simulated sensor data
"""

from typing import List, Dict
import json


class DetectionModule:
    """Detects and classifies other drones"""
    
    def __init__(self, drone_id: str, teammates: List[str]):
        self.drone_id = drone_id
        self.teammates = teammates
        self.detected_drones = {}  # {drone_id: {position, distance, type}}
    
    def process_sensor_data(self, sensor_data: Dict) -> List[str]:
        """
        Process sensor data and return list of detected drone IDs
        
        In real implementation, this would:
        - Process camera images with OpenCV
        - Detect drone markers/colors
        - Estimate positions via stereo vision
        
        For now: Mock detection from simulated sensor topics
        """
        detected = []
        
        # TODO: Parse camera image and detect drones
        # For now, we'll implement via topic subscription
        
        return detected
    
    def classify_drone(self, drone_id: str) -> str:
        """Classify detected drone as friendly or enemy"""
        if drone_id in self.teammates:
            return "FRIENDLY"
        else:
            return "ENEMY"
    
    def get_threat_level(self, drone_id: str, distance: float) -> int:
        """
        Calculate threat level (0-100)
        Closer = more threatening
        """
        if drone_id in self.teammates:
            return 0  # Teammates are never threats
        
        # Simple inverse distance model
        if distance < 1.0:
            return 100  # Very close, critical threat
        elif distance < 3.0:
            return 50   # Medium threat
        else:
            return 10   # Low threat
    
    def should_engage(self, drone_id: str, threat_level: int) -> bool:
        """Decide whether to engage target"""
        if self.classify_drone(drone_id) == "FRIENDLY":
            return False  # NEVER shoot friendlies
        
        if threat_level > 30:
            return True  # Engage high threats
        
        return False

    def process_visual_detections(self, detections: Dict) -> List[str]:
        """
        Process visual detections and return list of threat drone IDs
    
        Args:
        detections: dict from VisionProcessor (drone position, size, etc)
    
        Returns:
        list of detected drone IDs classified as threats
    """
        threats = []
        for drone_id, detection_data in detections.items():
            # In real implementation: match visual detection to known drone IDs
            # For now: treat any detection as potential threat
            if detection_data['confidence'] > 0.7:
                threats.append(drone_id)
    
        return threats


class SwarmCoordinator:
    """Coordinates actions across the swarm"""
    
    def __init__(self, drone_id: str, team: str):
        self.drone_id = drone_id
        self.team = team
        self.teammate_states = {}  # {drone_id: {position, status}}
    
    def update_teammate_state(self, drone_id: str, state_msg: str):
        """Update known state of a teammate"""
        try:
            state_data = json.loads(state_msg)
            self.teammate_states[drone_id] = state_data
        except json.JSONDecodeError:
            pass
    
    def get_all_friendly_positions(self) -> Dict[str, list]:
        """Return positions of all known friendly drones"""
        positions = {}
        for drone_id, state in self.teammate_states.items():
            if 'position' in state:
                positions[drone_id] = state['position']
        return positions
    
    def is_safe_to_fire(self, target_position: list, 
                        fire_direction: list) -> bool:
        """
        Check if firing at target is safe (won't hit friendlies)
        
        In full implementation: Ray-cast from drone through target
        Check if any friendly drone is in the fire cone
        """
        # TODO: Implement geometric safety check
        return True  # Placeholder