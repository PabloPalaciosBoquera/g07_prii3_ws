import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

CAJA_SDF = (
    '<sdf version="1.6"><model name="caja"><static>true</static><link name="link">'
    '<collision name="c"><geometry><box><size>0.2 0.2 0.3</size></box></geometry></collision>'
    '<visual name="v"><geometry><box><size>0.2 0.2 0.3</size></box></geometry>'
    '<material><diffuse>0.8 0.1 0.1 1</diffuse></material></visual>'
    '</link></model></sdf>')


def generate_launch_description():
    os.environ['TURTLEBOT3_MODEL'] = 'burger'

    # Gazebo con un mundo vacío y el TurtleBot3 en (0, 0) mirando hacia +x
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('turtlebot3_gazebo'),
            'launch', 'empty_world.launch.py')))

    nodo = Node(
        package='g07_prii3_move_turtlebot',
        executable='draw_number',
        name='draw_number',
        output='screen')

    # El nodo arranca 8 s después, cuando Gazebo ya está listo
    return LaunchDescription([
        gazebo,
        TimerAction(period=8.0, actions=[nodo]),
    ])
