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
    
    with open(urdf_file, 'r') as f:
        urdf_content = f.read()
    
    return LaunchDescription([
        ExecuteProcess(
            cmd=['gz', 'sim', world_file],
            output='screen'
        ),
        
        ExecuteProcess(
            cmd=['ros2', 'run', 'ros_gz_sim', 'create',
                 '-name', 'drone_1',
                 '-x', '0', '-y', '0', '-z', '1',
                 '-file', urdf_file],
            output='screen'
        ),
    ])