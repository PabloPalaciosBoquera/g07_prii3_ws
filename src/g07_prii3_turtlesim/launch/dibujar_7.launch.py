from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    turtlesim = Node(
        package='turtlesim',
        executable='turtlesim_node',
        name='turtlesim',
        output='screen'
    )

    dibujar_7 = Node(
        package='g07_prii3_turtlesim',
        executable='dibujar_7',
        name='dibujar_7',
        output='screen'
    )

    return LaunchDescription([
        turtlesim,
        dibujar_7
    ])
