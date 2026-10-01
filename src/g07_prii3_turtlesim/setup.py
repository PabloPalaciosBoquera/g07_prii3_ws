import os
from glob import glob

from setuptools import find_packages, setup


package_name = 'g07_prii3_turtlesim'


setup(
    name=package_name,
    version='0.0.0',

    packages=find_packages(
        exclude=['test']
    ),

    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
        (
            os.path.join(
                'share',
                package_name,
                'launch'
            ),
            glob('launch/*.launch.py')
        ),
    ],

    install_requires=[
        'setuptools'
    ],

    zip_safe=True,

    maintainer='pabloubnt',

    maintainer_email='ppalboq@upv.edu.es',

    description='Paquete ROS 2 del grupo 07 para controlar turtlesim',

    license='Apache-2.0',

    tests_require=[
        'pytest'
    ],

    entry_points={
        'console_scripts': [
            'dibujar_7 = g07_prii3_turtlesim.dibujar_7:main',
        ],
    },
)
