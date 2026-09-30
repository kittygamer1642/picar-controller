import socket
import pygame
import time

RPI_IP = '192.168.1.64'
PORT = 5005

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print('No Controller detected')
    exit()

controller = pygame.joystick.Joystick(0)
controller.init()
print(f'Connected to: {controller.get_name()}')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# controller buttons
CROSS = 0
CIRCLE = 1
TRI = 2
SQUARE = 3

L_BUMPER = 9
R_BUMPER = 10

L_STICK = 7
R_STICK = 8

camera_yaw = 0
camera_pitch = 0

last_button = [
    False, False, False, False,
    False, False, False, False,
    False, False, False
]

button = [
    False, False, False, False,
    False, False, False, False,
    False, False, False
]

def update_buttons():
    for i in range(len(button)):
        raw_button = bool(controller.get_button(i))
        button[i] = raw_button and not last_button[i]
        last_button[i] = raw_button

try:
    while True:
        pygame.event.pump()

        throttle = -int(controller.get_axis(1) * 60)
        steering = int(controller.get_axis(0) * 30)

        camera_yaw = int(controller.get_axis(3) * 10)
        camera_pitch = int(controller.get_axis(2) * 10)

        update_buttons()

        horn = button[CROSS]
        picture = button[L_BUMPER]

        zero = button[R_STICK]

        if abs(throttle) < 5: throttle = 0
        if abs(steering) < 5: steering = 0

        message = f'{throttle},{steering},{camera_yaw},{camera_pitch},{horn},{picture},{zero}'.encode()
        sock.sendto(message, (RPI_IP, PORT))

        time.sleep(0.05)
except KeyboardInterrupt:
    print('Disconecting controller.')