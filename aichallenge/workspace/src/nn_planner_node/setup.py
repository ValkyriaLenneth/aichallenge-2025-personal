from setuptools import find_packages, setup
from setuptools.command.install import install
import os
from glob import glob
import shutil

package_name = 'nn_planner_node'

class CustomInstallCommand(install):
    """Custom installation to handle ROS2 executable placement"""
    def run(self):
        install.run(self)
        # After normal installation, copy executable to ROS2 expected location
        bin_dir = os.path.join(self.install_scripts, '..')
        lib_package_dir = os.path.join(self.install_lib, '..', 'lib', package_name)
        
        # Ensure the lib/package_name directory exists
        os.makedirs(lib_package_dir, exist_ok=True)
        
        # Copy the planner executable from bin to lib/package_name
        src_executable = os.path.join(bin_dir, 'bin', 'planner')
        dst_executable = os.path.join(lib_package_dir, 'planner')
        
        if os.path.exists(src_executable):
            shutil.copy2(src_executable, dst_executable)
            os.chmod(dst_executable, 0o755)  # Make sure it's executable

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='NN Planner for speed control',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'planner = nn_planner_node.planner_node:main'
        ],
    },
    cmdclass={
        'install': CustomInstallCommand,
    },
) 