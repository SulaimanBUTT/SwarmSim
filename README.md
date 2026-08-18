# Autonomous Drone Swarm Simulation

Production-grade multi-agent autonomous system for drone swarm coordination, detection, and engagement.

## Quick Start

```bash
cd ~/swarm_sim_ws
colcon build
source install/setup.bash
ros2 launch swarm_sim swarm.launch.py
```

## Architecture

- **8 Drones**: 4 friendly + 4 enemy
- **ROS2 Lyrical**: Decentralized communication
- **Gazebo**: Physics simulation
- **Python 3.14**: Autonomous decision logic

## Features

✅ Autonomous team coordination  
✅ Friendly fire prevention  
✅ Threat detection & tracking  
✅ Engagement control with ammo management  
✅ Swarm tactics & formations  
  

## Topics

- `/team/friendly/state` - All friendly drones broadcast position, health, ammo
- `/team/enemy/state` - Enemy drones broadcast state
- `/drone_X/attack` - Engagement commands

## Testing

```bash
cd ~/swarm_sim_ws
colcon test
```

## Phases Completed

- ✅ Phase 0: Environment Setup
- ✅ Phase 1: Drone URDF Modeling
- ✅ Phase 2: Multi-Drone Swarm
- ✅ Phase 3: Vision & Detection
- ✅ Phase 4: Engagement System
- ✅ Phase 5: Swarm Tactics

## Next Steps

- Connect real Gazebo camera sensors
- Implement OpenCV blob detection
- Add movement commands (currently static)
- Performance profiling

## Author

Muhammad Sulaiman Butt  
SAFESKY NEXUS Internship - First Task
