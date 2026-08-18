#!/usr/bin/env python3

import os
import time
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory('swarm_sim')
    world_file = os.path.join(pkg_share, 'worlds', 'swarm_arena.sdf')
    
    iris_model = os.path.join(pkg_share, 'models', 'iris_friendly', 'model.sdf')
    
    drones = [
        {'id': '1', 'team': 'friendly', 'x': '0.0', 'y': '0.0', 'z': '1.0'},
        {'id': '2', 'team': 'friendly', 'x': '2.0', 'y': '0.0', 'z': '1.0'},
        {'id': '3', 'team': 'friendly', 'x': '0.0', 'y': '2.0', 'z': '1.0'},
        {'id': '4', 'team': 'friendly', 'x': '2.0', 'y': '2.0', 'z': '1.0'},
        {'id': '5', 'team': 'enemy', 'x': '-5.0', 'y': '-5.0', 'z': '1.0'},
        {'id': '6', 'team': 'enemy', 'x': '-5.0', 'y': '5.0', 'z': '1.0'},
        {'id': '7', 'team': 'enemy', 'x': '5.0', 'y': '-5.0', 'z': '1.0'},
        {'id': '8', 'team': 'enemy', 'x': '5.0', 'y': '5.0', 'z': '1.0'},
    ]
    
    ld = LaunchDescription()
    
    # Start Gazebo with ogre rendering
    ld.add_action(
        ExecuteProcess(
            cmd=['bash', '-c', 'export SVGA_VGPU10=0 && export LIBGL_ALWAYS_INDIRECT=1 && export DISPLAY=:0 && gz sim --render-engine ogre ' + world_file],
            output='screen'
        )
    )
    
    for drone_config in drones:
        drone_id = drone_config['id']
        team = drone_config['team']
        x = drone_config['x']
        y = drone_config['y']
        z = drone_config['z']
        
        teammates = [
            d['id'] for d in drones 
            if d['team'] == team and d['id'] != drone_id
        ]
        
        # Spawn with delay to let Gazebo start
        ld.add_action(
            ExecuteProcess(
                cmd=['bash', '-c', f'sleep 5 && ros2 run ros_gz_sim create -name drone_{drone_id} -x {x} -y {y} -z {z} -file {iris_model}'],
                output='screen'
            )
        )
        
        # Launch ROS2 node
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
