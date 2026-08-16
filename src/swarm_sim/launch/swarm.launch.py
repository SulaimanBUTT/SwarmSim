#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory('swarm_sim')
    
    urdf_file = os.path.join(pkg_share, 'urdf', 'drone.urdf')
    world_file = os.path.join(pkg_share, 'worlds', 'swarm_arena.sdf')
    
    # Drone configurations
    drones = [
        # Friendly drones (team='friendly')
        {'id': '1', 'team': 'friendly', 'x': '0.0', 'y': '0.0', 'z': '1.0'},
        {'id': '2', 'team': 'friendly', 'x': '2.0', 'y': '0.0', 'z': '1.0'},
        {'id': '3', 'team': 'friendly', 'x': '0.0', 'y': '2.0', 'z': '1.0'},
        {'id': '4', 'team': 'friendly', 'x': '2.0', 'y': '2.0', 'z': '1.0'},
        
        # Enemy drones (team='enemy')
        {'id': '5', 'team': 'enemy', 'x': '-5.0', 'y': '-5.0', 'z': '1.0'},
        {'id': '6', 'team': 'enemy', 'x': '-5.0', 'y': '5.0', 'z': '1.0'},
        {'id': '7', 'team': 'enemy', 'x': '5.0', 'y': '-5.0', 'z': '1.0'},
        {'id': '8', 'team': 'enemy', 'x': '5.0', 'y': '5.0', 'z': '1.0'},
    ]
    
    ld = LaunchDescription()
    
    # Start Gazebo (once for all drones)
    ld.add_action(
        ExecuteProcess(
            cmd=['gz', 'sim', world_file],
            output='screen'
        )
    )
    
    # Spawn each drone and launch its ROS2 node
    for drone_config in drones:
        drone_id = drone_config['id']
        team = drone_config['team']
        x = drone_config['x']
        y = drone_config['y']
        z = drone_config['z']
        
        # Determine teammates (all drones on same team except self)
        teammates = [
            d['id'] for d in drones 
            if d['team'] == team and d['id'] != drone_id
        ]
        
        # Spawn drone in Gazebo
        ld.add_action(
            ExecuteProcess(
                cmd=['ros2', 'run', 'ros_gz_sim', 'create',
                     '-name', f'drone_{drone_id}',
                     '-x', x, '-y', y, '-z', z,
                     '-file', urdf_file],
                output='screen'
            )
        )
        
        # Launch drone ROS2 node
        ld.add_action(
            Node(
                package='swarm_sim',
                executable='drone_node_multi',
                arguments=[drone_id, team, ','.join(teammates)],
                output='screen',
                name=f'drone_{drone_id}_node'
            )
        )
    
    return ld