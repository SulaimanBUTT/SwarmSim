"""
Swarm tactics - coordinated multi-drone behavior
"""

from typing import Dict, List


class SwarmTactics:
    """Coordinated swarm strategies"""
    
    def __init__(self, drone_id: str, team: str, teammates: List[str]):
        self.drone_id = drone_id
        self.team = team
        self.teammates = teammates
    
    def recommend_formation(self, threat_count: int) -> str:
        """Recommend formation based on threat level"""
        ally_count = len(self.teammates) + 1
        
        if threat_count == 0:
            return "SPREAD"  # Spread out, search pattern
        
        elif threat_count <= 2:
            return "DIAMOND"  # Diamond formation (stable)
        
        else:
            return "AGGRESSIVE"  # Close formation, concentrated fire
    
    def coordinate_attack(self, target_id: str, 
                         teammate_statuses: Dict) -> Dict:
        """
        Coordinate multi-drone attack on single target
        
        Returns: {my_role, recommended_actions}
        """
        # Assign roles based on drone ID
        drone_ids = [self.drone_id] + self.teammates
        drone_ids.sort()
        
        my_index = drone_ids.index(self.drone_id)
        
        if my_index == 0:
            role = "PRIMARY"  # Lead attacker
            action = "ENGAGE"
        elif my_index == 1:
            role = "SUPPORT"  # Flanking fire
            action = "FLANK_LEFT"
        else:
            role = "RESERVE"  # Hold fire, ready backup
            action = "HOLD_POSITION"
        
        return {
            'target': target_id,
            'my_role': role,
            'action': action,
            'coordinate_with': [
                drone_ids[i] for i in range(len(drone_ids)) 
                if i != my_index
            ]
        }
    
    def should_retreat(self, allied_count: int, enemy_count: int, 
                      my_health: float) -> bool:
        """
        Decide if team should retreat
        
        Returns: True if should retreat
        """
        # Retreat if severely outnumbered AND damaged
        if enemy_count >= allied_count * 2 and my_health < 40:
            return True
        
        # Retreat if all allies dead
        if allied_count == 1:
            return True
        
        return False
    
    def get_defensive_target(self, threatened_ally: str) -> str:
        """
        Find best position to defend threatened ally
        
        Returns: drone_id of ally needing defense
        """
        return threatened_ally
    
    def get_retreat_vector(self, current_pos: Dict, 
                          enemy_positions: List[Dict]) -> tuple:
        """
        Calculate best retreat direction
        
        Returns: (vx, vy, vz) velocity vector
        """
        # Simple: retreat opposite of enemy center
        if not enemy_positions:
            return (0, 0, 0.5)
        
        # Calculate retreat bearing (away from enemies)
        return (-1.0, 0, 0.5)  # Backward and upward


class CombatAnalytics:
    """Analyze combat situation"""
    
    def __init__(self):
        self.engagement_history = []
        self.kills = 0
        self.hits = 0
        self.shots_fired = 0
    
    def record_shot(self, target_id: str, hit: bool):
        """Record firing event"""
        self.shots_fired += 1
        if hit:
            self.hits += 1
        
        self.engagement_history.append({
            'target': target_id,
            'hit': hit,
            'accuracy': self.get_accuracy()
        })
    
    def record_kill(self, target_id: str):
        """Record enemy destroyed"""
        self.kills += 1
    
    def get_accuracy(self) -> float:
        """Get current accuracy percentage"""
        if self.shots_fired == 0:
            return 0.0
        return (self.hits / self.shots_fired) * 100