from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    image_folder_arg = DeclareLaunchArgument(
        'image_folder',
        default_value='',
        description='Folder containing meter images'
    )

   

    fake_sensor_node = Node(
        package='meter_reader',
        executable='fake_sensor',
        name='fake_sensor',
        output='screen',
        parameters=[{
            'image_folder': LaunchConfiguration('image_folder'),
            'publish_rate': 1.0,
            'loop': True
        }]
    )

    meter_differentiator_node = Node(
        package='meter_reader',
        executable='meter_diff',
        name='meter_differentiator',
        output='screen'
    )

    digital_reader_node = Node(
        package='meter_reader',
        executable='digital_meter',
        name='digital_reader',
        output='screen'
    )

    

    meter_reader_client_node = Node(
        package='meter_reader',
        executable='meter_logger',
        name='meter_reader_client',
        output='screen'
    )

    return LaunchDescription([
        image_folder_arg,
        
        fake_sensor_node,
        meter_differentiator_node,
        digital_reader_node,
        
        meter_reader_client_node
    ])
