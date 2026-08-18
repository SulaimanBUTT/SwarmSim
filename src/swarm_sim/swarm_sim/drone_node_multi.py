#!/usr/bin/env python3

import sys
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose, Twist
from sensor_msgs.msg import Image, Imu
from std_msgs.msg import String, Float32
import json
from .detection import DetectionModule, SwarmCoordinator
from .vision import VisionProcessor, DroneTracker
from .state_machine import StateMachine, DroneState
from .engagement import EngagementController
from .engagement import EngagementController, SafetyMonitor
from .tactics import SwarmTactics, CombatAnalytics

try:
    from cv_bridge import CvBridge
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False


class DroneNode(Node):
    """Autonomous drone agent in the swarm"""
    
    def __init__(self, drone_id: str, team: str, teammates: list):
        super().__init__(f'drone_{drone_id}')
        
        self.drone_id = drone_id
        self.team = team
        self.teammates = teammates

        
        # Core systems
        self.detection = DetectionModule(drone_id, teammates)
        self.coordinator = SwarmCoordinator(drone_id, team)
        self.state_machine = StateMachine(drone_id)

        # Engagement & Combat
        self.engagement = EngagementController(drone_id, teammates)
        self.safety = SafetyMonitor(drone_id, teammates)
        self.tactics = SwarmTactics(drone_id, team, teammates)
        self.analytics = CombatAnalytics()

        # Vision (optional)
        if VISION_AVAILABLE:
            self.vision = VisionProcessor(drone_id, team)
            self.tracker = DroneTracker()
            self.cv_bridge = CvBridge()
        else:
            self.vision = None
        
        # Subscribers
        self.pose_sub = self.create_subscription(
            Pose, f'/drone_{drone_id}/pose', self.on_pose, 10)
        self.camera_sub = self.create_subscription(
            Image, f'/drone_{drone_id}/camera/image', self.on_camera, 10)
        self.imu_sub = self.create_subscription(
            Imu, f'/drone_{drone_id}/imu', self.on_imu, 10)
        self.team_state_sub = self.create_subscription(
            String, f'/team/{team}/state', self.on_teammate_state, 10)
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(
            Twist, f'/drone_{drone_id}/cmd_vel', 10)
        self.state_pub = self.create_publisher(
            String, f'/drone_{drone_id}/state', 10)
        self.team_broadcast_pub = self.create_publisher(
            String, f'/team/{team}/state', 10)
        self.threat_pub = self.create_publisher(
            String, f'/drone_{drone_id}/threats', 10)
        self.fire_pub = self.create_publisher(
            String, f'/drone_{drone_id}/fire', 10)
        
        # State
        self.position = [0.0, 0.0, 0.0]
        self.detected_drones = {}
        self.threat_assessment = {}
        self.fire_count = 0
        
        # Main loop
        self.timer = self.create_timer(0.1, self.step)
        
        self.get_logger().info(
            f'🤖 Drone {drone_id} ({team}) initialized | Teammates: {teammates}')
    
    def on_pose(self, msg: Pose):
        """Update position from Gazebo"""
        self.position = [msg.position.x, msg.position.y, msg.position.z]
    
    def on_camera(self, msg: Image):
        """Process camera image"""
        if not self.vision:
            return
        
        try:
            cv_image = self.cv_bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            detections = self.vision.detect_drones(cv_image)
            
            if detections:
                self.get_logger().debug(
                    f'[{self.drone_id}] 👁️  Detected {len(detections)} objects')
        except Exception as e:
            pass
    
    def on_imu(self, msg: Imu):
        """Process IMU data"""
        pass
    
    def on_teammate_state(self, msg: String):
        """Receive teammate status"""
        try:
            state_data = json.loads(msg.data)
            drone_id = state_data.get('drone_id')
            self.coordinator.update_teammate_state(drone_id, msg.data)
        except json.JSONDecodeError:
            pass
    
    def step(self):
        """Main decision loop (10Hz)"""
        
        # 1. Broadcast own state
        self._broadcast_state()
        
        # 2. Detect threats
        self._detect_threats()
        
        # 3. Update state machine
        self._update_state()
        
        # 4. Execute engagement
        self._execute_engagement()
        
        # 5. Send movement commands
        self._send_commands()




    def _broadcast_state(self):
        """Publish state to team"""
        state_msg = String()
        state_msg.data = json.dumps({
            'drone_id': self.drone_id,
            'position': self.position,
            'team': self.team,
            'status': self.state_machine.state.value,
            'target': self.state_machine.target_id,
            'health': 100,  # TODO: implement health system
            'ammo': self.engagement.ammo
        })
        self.team_broadcast_pub.publish(state_msg)
    
    def _detect_threats(self):
        """Identify enemy drones"""
        friendly_positions = self.coordinator.get_all_friendly_positions()
        
        # Only count non-teammates as potential threats
        self.detected_drones = {
            drone_id: pos for drone_id, pos in friendly_positions.items()
            if drone_id != self.drone_id and drone_id not in self.teammates
        }
        
        # Assess each detected drone
        self.threat_assessment = {}
        for drone_id, position in self.detected_drones.items():
            distance = self._distance_to(position)
            classification = self.detection.classify_drone(drone_id)
            threat_level = self.detection.get_threat_level(drone_id, distance)
            
            self.threat_assessment[drone_id] = {
                'classification': classification,
                'distance': distance,
                'threat_level': threat_level
            }
            
            if classification == "ENEMY" and threat_level > 0:
                threat_msg = String()
                threat_msg.data = json.dumps({
                    'drone_id': self.drone_id,
                    'target': drone_id,
                    'distance': distance,
                    'threat_level': threat_level
                })
                self.threat_pub.publish(threat_msg)
    
    def _update_state(self):
        """Update state machine"""
        new_state = self.state_machine.update(
            self.threat_assessment,
            self.coordinator.teammate_states
        )
        
        if new_state != DroneState.IDLE:
            self.get_logger().info(
                f'[{self.drone_id}] State: {new_state.value} | '
                f'Target: {self.state_machine.target_id} | '
                f'Threat: {self.state_machine.threat_level}')
    
    def _execute_engagement(self):
        """Fire at enemies if conditions met"""
        if not self.state_machine.should_engage():
            return
        
        target = self.state_machine.target_id
        
        # Try to acquire lock
        if self.engagement.acquire_target(
            target, 
            self.state_machine.target_distance
        ):
            # Try to fire
            if self.engagement.fire(target):
                self.fire_count += 1
                
                fire_msg = String()
                fire_msg.data = json.dumps({
                    'drone_id': self.drone_id,
                    'target': target,
                    'distance': self.state_machine.target_distance,
                    'fire_count': self.fire_count
                })
                self.fire_pub.publish(fire_msg)
                
                self.get_logger().warn(
                    f'💥 [DRONE {self.drone_id}] FIRING at {target}! '
                    f'Distance: {self.state_machine.target_distance:.2f}m | '
                    f'Shots fired: {self.fire_count} | '
                    f'Ammo: {self.engagement.ammo}')
    
    def _send_commands(self):
        """Send velocity commands to motors"""
        vx, vy, vz = self.state_machine.get_movement_command()
        
        cmd = Twist()
        cmd.linear.x = vx
        cmd.linear.y = vy
        cmd.linear.z = vz
        
        # Only publish if not idle
        if self.state_machine.state != DroneState.IDLE:
            self.cmd_vel_pub.publish(cmd)
    
    def _distance_to(self, position: list) -> float:
        """Calculate distance"""
        dx = position[0] - self.position[0]
        dy = position[1] - self.position[1]
        dz = position[2] - self.position[2]
        return (dx**2 + dy**2 + dz**2) ** 0.5

    def _make_decisions(self):
        """Decide actions: detect, track, engage, coordinate"""
    
        if not self.threat_assessment:
            return  # No threats
    
    # Find closest threat
        closest_threat = min(
            self.threat_assessment.items(),
            key=lambda x: x[1]['distance']
        )

        threat_id, threat_data = closest_threat
        distance = threat_data['distance']
        classification = threat_data['classification']
    
        # STEP 1: Acquire target lock
        if self.engagement.acquire_target(threat_id, distance):
            self.get_logger().debug(f'[{self.drone_id}] Lock acquiring on {threat_id}...')
    
    # STEP 2: Check if lock is ready
        if self.engagement.is_lock_ready():
            self.get_logger().info(f'🎯 [{self.drone_id}] TARGET LOCKED: {threat_id} @ {distance:.1f}m')
        
        # STEP 3: Safety check before firing
            friendly_pos = self.coordinator.get_all_friendly_positions()
            bearing = threat_data.get('bearing', 0)
        
            if self.safety.is_safe_to_fire(threat_id, bearing, friendly_pos):
                # STEP 4: Fire!
                if self.engagement.can_fire():
                    result = self.engagement.fire(threat_id)
                    if result['success']:
                        self.get_logger().warn(
                            f'🔥 [{self.drone_id}] FIRING at {threat_id} | '
                            f'Ammo: {result["ammo"]} | '
                            f'Accuracy: {result["hit_probability"]*100:.0f}%')
                        self.analytics.record_shot(threat_id, hit=True)
            else:
            # Friendly in fire zone
                self.get_logger().warn(
                    f'⚠️  [{self.drone_id}] HOLD FIRE: Friendly in fire zone for {threat_id}')
                self.engagement.lose_target()
    
    # STEP 5: Check if should retreat
        allied_positions = self.coordinator.get_all_friendly_positions()
        if self.tactics.should_retreat(len(allied_positions), 
                                   len(self.threat_assessment), 
                                   my_health=90):
            self.get_logger().warn(f'📍 [{self.drone_id}] TACTICAL RETREAT')
            self.engagement.lose_target()


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    
    if len(args) < 3:
        print("Usage: drone_node_multi <drone_id> <team> <teammate1,teammate2,...>")
        sys.exit(1)
    
    drone_id = args[0]
    team = args[1]
    teammates = args[2].split(',') if args[2] else []
    
    rclpy.init()
    node = DroneNode(drone_id, team, teammates)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()