#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose, Twist
from sensor_msgs.msg import Image, Imu
from std_msgs.msg import String
import json
from .detection import DetectionModule, SwarmCoordinator


class DroneNode(Node):
    """Single drone agent in the swarm"""
    
    def __init__(self, drone_id: str, team: str, teammates: list):
        super().__init__(f'drone_{drone_id}')
        
        self.drone_id = drone_id
        self.team = team
        self.teammates = teammates
        
        # Detection and coordination
        self.detection = DetectionModule(drone_id, teammates)
        self.coordinator = SwarmCoordinator(drone_id, team)
        
        # Subscribers (receive from Gazebo)
        self.pose_sub = self.create_subscription(
            Pose, f'/drone_{drone_id}/pose', self.on_pose, 10)
        self.camera_sub = self.create_subscription(
            Image, f'/drone_{drone_id}/camera/image', self.on_camera, 10)
        self.imu_sub = self.create_subscription(
            Imu, f'/drone_{drone_id}/imu', self.on_imu, 10)
        
        # Subscribe to teammate broadcasts
        self.team_state_sub = self.create_subscription(
            String, f'/team/{team}/state', self.on_teammate_state, 10)
        
        # Publishers (send commands to Gazebo)
        self.cmd_vel_pub = self.create_publisher(
            Twist, f'/drone_{drone_id}/cmd_vel', 10)
        self.state_pub = self.create_publisher(
            String, f'/drone_{drone_id}/state', 10)
        self.team_broadcast_pub = self.create_publisher(
            String, f'/team/{team}/state', 10)
        self.detection_pub = self.create_publisher(
            String, f'/drone_{drone_id}/detections', 10)
        
        # State
        self.position = [0.0, 0.0, 0.0]
        self.velocity = [0.0, 0.0, 0.0]
        self.detected_drones = {}
        self.threat_assessment = {}
        
        # Main loop timer (10Hz)
        self.timer = self.create_timer(0.1, self.step)
        
        self.get_logger().info(
            f'Drone {drone_id} ({team}) initialized with teammates: {teammates}')
    
    def on_pose(self, msg: Pose):
        """Receive drone position from Gazebo"""
        self.position = [
            msg.position.x,
            msg.position.y,
            msg.position.z
        ]
    
    def on_camera(self, msg: Image):
        """Receive camera image from Gazebo"""
        # TODO: Process with OpenCV
        pass
    
    def on_imu(self, msg: Imu):
        """Receive IMU data from Gazebo"""
        # TODO: Extract accelerometer/gyroscope
        pass
    
    def on_teammate_state(self, msg: String):
        """Receive state broadcasts from other friendly drones"""
        try:
            state_data = json.loads(msg.data)
            drone_id = state_data.get('drone_id')
            
            # Update coordinator knowledge
            self.coordinator.update_teammate_state(drone_id, msg.data)
            
            self.get_logger().debug(
                f'Updated state for drone {drone_id}')
        except json.JSONDecodeError:
            pass
    
    def step(self):
        """Main decision loop (runs at 10Hz)"""
        
        # 1. Broadcast own state to teammates
        self._broadcast_state()
        
        # 2. Detect other drones (placeholder - will add OpenCV)
        self._detect_drones()
        
        # 3. Assess threats
        self._assess_threats()
        
        # 4. Make decisions
        self._make_decisions()
        
        # 5. Execute actions
        self._execute_actions()
    
    def _broadcast_state(self):
        """Publish own state to team channel"""
        state_msg = String()
        state_msg.data = json.dumps({
            'drone_id': self.drone_id,
            'position': self.position,
            'team': self.team,
            'status': 'active',
            'detected_enemies': list(self.detected_drones.keys())
        })
        self.team_broadcast_pub.publish(state_msg)
    
    def _detect_drones(self):
        """Detect other drones (mock for now)"""
        # In real implementation: process camera image here
        # For now: simulate detection data
        
        # Mock: assume we can detect all drones within 10m
        friendly_positions = self.coordinator.get_all_friendly_positions()
        
        self.detected_drones = {
        drone_id: pos for drone_id, pos in friendly_positions.items()
        if drone_id != self.drone_id
    }
    
        self.get_logger().debug(f'Detected {len(self.detected_drones)} drones')
    
    def _assess_threats(self):
        """Calculate threat level for each detected drone"""
        self.threat_assessment = {}
        
        for drone_id, position in self.detected_drones.items():
            if drone_id == self.drone_id:
                continue  # Skip self
            
            # Calculate distance
            distance = self._distance_to(position)
            
            # Classify and get threat level
            classification = self.detection.classify_drone(drone_id)
            threat_level = self.detection.get_threat_level(drone_id, distance)
            
            self.threat_assessment[drone_id] = {
                'classification': classification,
                'distance': distance,
                'threat_level': threat_level
            }
            
            if classification == "ENEMY":
                self.get_logger().info(
                    f'THREAT: {drone_id} at {distance:.2f}m, threat={threat_level}')
    
    def _make_decisions(self):
        """Decide what actions to take"""
        # For now: just log threat assessments
        # TODO: Implement engagement logic
        pass
    
    def _execute_actions(self):
        """Send commands to motors/actuators"""
        # Placeholder: no movement yet
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.linear.y = 0.0
        cmd.linear.z = 0.0
        # self.cmd_vel_pub.publish(cmd)
    
    def _distance_to(self, position: list) -> float:
        """Calculate Euclidean distance to position"""
        dx = position[0] - self.position[0]
        dy = position[1] - self.position[1]
        dz = position[2] - self.position[2]
        return (dx**2 + dy**2 + dz**2) ** 0.5
    
    def is_friendly(self, drone_id: str) -> bool:
        """Check if drone is a teammate"""
        return drone_id in self.teammates


def main(args=None):
    rclpy.init(args=args)
    
    node = DroneNode(
        drone_id='1',
        team='friendly',
        teammates=['2', '3', '4']
    )
    
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()