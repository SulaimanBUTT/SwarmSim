"""
Engagement logic for drone combat - COMPLETE SYSTEM
"""

import time
from typing import Dict, Optional


class EngagementController:
    """Manages weapon fire and target lock"""
    
    def __init__(self, drone_id: str, teammates: list):
        self.drone_id = drone_id
        self.teammates = teammates
        self.target_locked = False
        self.lock_time = 0
        self.last_fire_time = 0
        self.ammo = 100
        self.fire_rate = 0.5  # 2 shots per second
        self.lock_time_required = 0.5  # seconds to acquire lock
    
    def acquire_target(self, target_id: str, distance: float) -> bool:
        """Try to lock onto target"""
        # Check if target is teammate (NEVER lock friendlies)
        if target_id in self.teammates:
            return False
        
        # Check range
        if distance > 50.0:
            return False
        
        if not self.target_locked:
            self.lock_time = time.time()
            self.target_locked = True
        
        return self.target_locked
    
    def lose_target(self):
        """Lose lock on current target"""
        self.target_locked = False
        self.lock_time = 0
    
    def is_lock_ready(self) -> bool:
        """Check if lock time requirement met"""
        if not self.target_locked:
            return False
        
        elapsed = time.time() - self.lock_time
        return elapsed >= self.lock_time_required
    
    def can_fire(self) -> bool:
        """Check if weapon ready to fire"""
        if self.ammo <= 0:
            return False
        
        if not self.is_lock_ready():
            return False
        
        current_time = time.time()
        if current_time - self.last_fire_time < self.fire_rate:
            return False
        
        return True
    
    def fire(self, target_id: str) -> Dict:
        """
        Fire weapon at target
        
        Returns: {success, ammo_remaining, hit_probability}
        """
        if not self.can_fire():
            return {'success': False, 'ammo': self.ammo}
        
        # Fire!
        self.ammo -= 1
        self.last_fire_time = time.time()
        
        # Hit probability: closer = more accurate
        hit_probability = 0.85  # 85% accuracy
        
        return {
            'success': True,
            'ammo': self.ammo,
            'hit_probability': hit_probability,
            'target': target_id
        }
    
    def get_status(self) -> Dict:
        """Return engagement status"""
        return {
            'target_locked': self.target_locked,
            'lock_ready': self.is_lock_ready(),
            'can_fire': self.can_fire(),
            'ammo': self.ammo,
            'fire_rate': self.fire_rate
        }


class SafetyMonitor:
    """Prevents friendly fire"""
    
    def __init__(self, drone_id: str, teammates: list):
        self.drone_id = drone_id
        self.teammates = teammates
        self.fire_cone_width = 15.0  # degrees
    
    def is_safe_to_fire(self, target_id: str, 
                       target_bearing: float,
                       friendly_positions: Dict[str, Dict]) -> bool:
        """
        Check if firing is safe - no friendlies in fire zone
        
        Args:
            target_id: drone we want to fire at
            target_bearing: angle to target (-90 to +90 degrees)
            friendly_positions: dict of friendly drone positions
        
        Returns: True if safe to fire
        """
        # Never fire at teammates
        if target_id in self.teammates:
            return False
        
        # Check each friendly
        for friend_id, friend_data in friendly_positions.items():
            if friend_id == self.drone_id:
                continue
            
            friend_bearing = friend_data.get('bearing', 0)
            
            # Is friendly within fire cone?
            bearing_diff = abs(friend_bearing - target_bearing)
            if bearing_diff < self.fire_cone_width:
                # FRIENDLY IN FIRE ZONE - ABORT
                return False
        
        return True
    
    def log_safety_check(self, safe: bool, reason: str = ""):
        """Log safety check result"""
        status = "✅ SAFE" if safe else "❌ UNSAFE"
        return f"{status}: {reason}"