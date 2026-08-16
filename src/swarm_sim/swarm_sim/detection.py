"""Drone detection module"""

class DetectionModule:
    def __init__(self, drone_id, teammates):
        self.drone_id = drone_id
        self.teammates = teammates
        self.detected_drones = {}
    
    def classify_drone(self, drone_id):
        if drone_id in self.teammates:
            return "FRIENDLY"
        return "ENEMY"
    
    def get_threat_level(self, drone_id, distance):
        if drone_id in self.teammates:
            return 0
        if distance < 1.0:
            return 100
        elif distance < 3.0:
            return 50
        return 10
    
    def should_engage(self, drone_id, threat_level):
        if self.classify_drone(drone_id) == "FRIENDLY":
            return False
        return threat_level > 30


class SwarmCoordinator:
    def __init__(self, drone_id, team):
        self.drone_id = drone_id
        self.team = team
        self.teammate_states = {}
    
    def update_teammate_state(self, drone_id, state_msg):
        import json
        try:
            state_data = json.loads(state_msg)
            self.teammate_states[drone_id] = state_data
        except:
            pass
    
    def get_all_friendly_positions(self):
        positions = {}
        for drone_id, state in self.teammate_states.items():
            if 'position' in state:
                positions[drone_id] = state['position']
        return positions
    
    def is_safe_to_fire(self, target_position, fire_direction):
        return True
