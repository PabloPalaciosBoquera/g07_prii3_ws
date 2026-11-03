from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    nodo = Node(
        package='g07_prii3_move_jetbot',
        executable='collision_avoidance',
        name='collision_avoidance',
        output='screen')

    return LaunchDescription([nodo])
