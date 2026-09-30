import builtins
import getpass
import os
import sys

builtins.User = getpass.getuser()

from robot_hat import Servo
from robot_hat import Motors
from robot_hat import Music

import socket
import time

import camera

motors = Motors()
for i in range(3):
  try:
    card_str = f'hw:{i},0'
    print(f'Using audio card {card_str}')
    
    os.environ["SDL_AUDIODRIVER"] = "alsa"
    os.environ["AUDIODEV"] = card_str
    audio = Music()
    break;
  except pygame.error:
    pass

motors.set_left_id = 1
motors.set_right_id = 2

steer_servo = Servo(0)

cam_yaw_servo = Servo(1)
cam_pitch_servo = Servo(2)

audio.music_set_volume(100)

yaw = 0
pitch = 0

horn_sound = 'Toy Honk.wav'
image_folder = 'Camera'

UDP_IP = "0.0.0.0"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print("PiCar-X Remote Server Active. Awaiting controller input...")

camera.start_cam()

try:
    while True:
        data, addr = sock.recvfrom(1024)
        payload = data.decode().split(',')

        if len(payload) == 7:
            throttle = int(payload[0])
            steering = int(payload[1])

            yaw += float(payload[2])
            pitch -= float(payload[3])
            
            horn = True if(payload[4] == 'True') else False
            picture = True if(payload[5] == 'True') else False

            zero = True if(payload[6] == 'True') else False

            if (horn):
                audio.sound_play(horn_sound)

            if (picture):
                year = time.localtime().tm_year
                month = time.localtime().tm_mon
                day = time.localtime().tm_mday
                hour = time.localtime().tm_hour
                min = time.localtime().tm_min
                sec = time.localtime().tm_sec

                time_str = f'{month}-{day}-{year} {hour}-{min}-{sec}'

                camera.capture_img(image_folder + '/' + time_str)
                print(f'Took picture: {time_str}')

            if zero:
                yaw = 0
                pitch = 0

            motors.speed(-throttle, throttle)
            steer_servo.angle(steering)

            cam_yaw_servo.angle(yaw)
            cam_pitch_servo.angle(pitch)
except KeyboardInterrupt:
    print('\nStopping Server...')
finally:
    motors.speed(0, 0)
    steer_servo.angle(0)
