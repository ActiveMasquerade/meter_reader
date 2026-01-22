from setuptools import find_packages, setup
from glob import glob
import os
package_name = 'meter_reader'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[

    ('share/meter_reader', ['package.xml']),
    (os.path.join('share', 'meter_reader', 'launch'), glob('launch/*.launch.py')),
],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='root@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "fake_sensor=meter_reader.fake_sensor:main",
            "meter_diff=meter_reader.meter_differentiator:main",
            
            "digital_meter=meter_reader.digital_reader:main",
            "meter_logger=meter_reader.reader_logger_node:main"
        ],
    },
)
