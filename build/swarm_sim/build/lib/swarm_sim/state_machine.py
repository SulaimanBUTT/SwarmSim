"""
Drone state machine for behavioral logic
"""

from enum import Enum


class DroneState(Enum):
    """Drone operational states"""
    IDLE = "idle"                    # Waiting for orders
    SEARCH = "search"                # Looking for enemies
    TRACKING = "tracking"            # Following an enemy
    ENGAGING = "engaging"            # Attacking an enemy
    DEFENSIVE = "defensive"          # Protecting teammate
    EVADING = "evading"              # Running from threat
    DAMAGED = "damaged"              # Low health


class StateMachine:
    """Manages drone behavior state transitions"""
    
    def __init__(self, drone_id: str):
        self.drone_id = drone_id
        self.state = DroneState.IDLE
        self.target_id = None
        self.target_distance = float('inf')
        self.threat_level = 0
    
    def update(self, threat_assessment: dict, teammate_status: dict) -> DroneState:
        """
        Update state based on current threats and teammate status
        
        Returns: new state
        """
        
        # Check if any enemies detected
        enemy_threats = {
            drone_id: threat for drone_id, threat in threat_assessment.items()
            if threat['classification'] == 'ENEMY'
        }
        
        # Find closest enemy
        if enemy_threats:
            closest = min(enemy_threats.items(), 
                         key=lambda x: x[1]['distance'])
            self.target_id = closest[0]
            self.target_distance = closest[1]['distance']
            self.threat_level = closest[1]['threat_level']
        else:
            self.target_id = None
            self.target_distance = float('inf')
            self.threat_level = 0
        
        # State transitions
        if self.threat_level > 50:
            # High threat nearby
            if self.state in [DroneState.IDLE, DroneState.SEARCH]:
                self.state = DroneState.TRACKING
            elif self.state == DroneState.TRACKING:
                if self.target_distance < 2.0:
                    self.state = DroneState.ENGAGING
        
        elif self.threat_level > 20:
            # Medium threat
            if self.state == DroneState.IDLE:
                self.state = DroneState.SEARCH
            elif self.state == DroneState.ENGAGING:
                self.state = DroneState.TRACKING
        
        else:
            # No immediate threat
            if self.state in [DroneState.TRACKING, DroneState.ENGAGING]:
                self.state = DroneState.SEARCH
            elif self.state == DroneState.SEARCH:
                self.state = DroneState.IDLE
        
        return self.state
    
    def should_engage(self) -> bool:
        """Decide whether to fire weapons"""
        return (
            self.state == DroneState.ENGAGING and
            self.target_distance < 3.0 and
            self.threat_level > 30
        )
    
    def get_movement_command(self) -> tuple:
        """
        Return movement command based on state
        
        Returns: (vx, vy, vz) velocity in m/s
        """
        if self.state == DroneState.IDLE:
            return (0, 0, 0)
        
        elif self.state == DroneState.SEARCH:
            # Hover and rotate
            return (0.1, 0, 0)
        
        elif self.state == DroneState.TRACKING:
            # Move toward target
            return (0.5, 0, 0)
        
        elif self.state == DroneState.ENGAGING:
            # Aggressive approach
            return (1.0, 0, 0)
        
        elif self.state == DroneState.EVADING:
            # Retreat
            return (-1.0, 0, 0.5)
        
        return (0, 0, 0)