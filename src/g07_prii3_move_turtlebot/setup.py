from glob import glob

from setuptools import find_packages, setup

package_name = 'g07_prii3_move_turtlebot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='grupo07',
    maintainer_email='iagoblast03@gmail.com',
    description='Grupo 07: dibujo del 7 y evitación de obstáculos con el TurtleBot3 simulado',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'draw_number = g07_prii3_move_turtlebot.draw_number:main',
            'collision_avoidance = g07_prii3_move_turtlebot.collision_avoidance:main',
        ],
    },
)
