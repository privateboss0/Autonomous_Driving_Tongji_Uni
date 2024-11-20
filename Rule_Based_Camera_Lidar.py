#!/usr/bin/env python

import glob
import os
import sys

try:
    sys.path.append(glob.glob('**/*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import open3d as o3d
import random
import time
import numpy as np
import cv2
from matplotlib import cm

Horizontal_pixel = 800
Vertical_pixel = 600
point_cloud = o3d.geometry.pointcloud()

def do_nothing(image):
    img = np.array(image.raw_data)
    img2 = img.reshape((Vertical_pixel, Horizontal_pixel, 4))
    img3 = img2[:, :, :3]
    cv2.imshow("", img3)
    cv2.waitKey(1)
    return img3/255.0

def od_everything(point_cloud):
    data = np.copy(np.frombuffer(point_cloud.raw_data, dtype=np.dtype('f4')))
    data = np.reshape(data, (int(data.shape[0] / 4), 4))
    
    intensity = data[:, -1]
    intensity_colour = 1.0 - np.log(intensity) / np.log(np.exp(-0.004 * 100))
    int_color = np.c_[
        np.interp(intensity_col),
        np.interp(intensity_col),
        np.interp(intensity_col)]
    
    points = data[:, -1]
    points[:, :1] = -points[:, :1]
    point_list.points = o3d.utility. Vector3dVector (points)
    point_list.colors = o3d.utility.Vector3dVector (int_color)

actor_list = []

try:
    client = carla.Client('localhost', 2000)
    client.set_timeout(3.0)

    world = client.get_world()
    
    weather = carla.WeatherParameters(
    cloudyness=80.0,
    precipitation=30.0,
    sun_altitude_angle=70.0
    )
    world.set_weather(weather)
    blueprint_library = world.get_blueprint_library()

    vehicle_bp = random.choice(blueprint_library.filter('vehicle.chevrolet.*'))
    print(vehicle_bp)

    spawn_points = random.choice(world.get_map().get_spawn_points())

    vehicle = world.spawn_actor(vehicle_bp, spawn_points)
    #vehicle.apply_control(carla.VehicleControl(throttle=1.0, steer=0.0))
    vehicle.set_autopilot(True)
    actor_list.append(vehicle)
    
    # get the blueprint for camera sensor
    camera_bp = world.get_blueprint_library().find('sensor.camera.rgb')
    
    # Adjust the dimensions of the image from the camera sensor
    camera_bp.set_attribute('image_size_x', f'{Horizontal_pixel}')
    camera_bp.set_attribute('image_size_y', f'{Vertical_pixel}')
    camera_bp.set_attribute('fov', '100')
    camera_bp.set_attribute('sensor_tick', '0.0')
    
    # Provide the position of the sensor relative to the vehicle
    spawn_points = carla.Transform(carla.Location(x=0.8, z=1.5))
    
    # Tell the world to spawn the sensor, and attach it to your vehicle actor.
    camera_sensor = world.spawn_actor(camera_bp, spawn_points, attach_to=vehicle)
    actor_list.append(camera_sensor)
    
    camera_sensor.listen(lambda data: do_nothing(data))
    
    # get the blueprint for lidar sensor
    lidar_bp = world.get_blueprint_library().find('sensor.lidar.ray_cast')
    lidar_bp.set_attribute('range', '100.0')
    lidar_bp.set_attribute('noise_stddev', '0.1')
    lidar_bp.set_attribute('upper_fov', '15.0')
    lidar_bp.set_attribute('lower_fov', '-25.0')
    lidar_bp.set_attribute('rotation_frequency', '20.0')
    lidar_bp.set_attribute('points_per_second', '500000')
    
    # Provide the position of the sensor relative to the vehicle 
    spawn_points = carla.Transform(carla.Location(x=0.1, z=2.0))
    
    # Tell the world to spawn the sensor, and attach it to your vehicle actor.
    lidar_sensor = world.spawn_actor(lidar_bp, spawn_points, attach_to=vehicle)
    actor_list.append(lidar_sensor)

    
    lidar_sensor.listen(lambda data: od_everything(point_cloud))

    #sleep for 300 seconds, afterwhich you end:
    time.sleep(300)


finally:

    print('destroying actors')
    for actor in actor_list:
        actor.destroy()
    print('all done. Eveything back to normal')
