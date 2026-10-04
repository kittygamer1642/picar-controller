import builtins
import getpass
import os
import sys

builtins.User = getpass.getuser()
try:
    card_num = sys.argv[1]
    card_str = f'hw:{card_num},0'
except IndexError:
    card_str = 'hw:0,0'

print(f'Using audio card {card_str}')

os.environ["SDL_AUDIODRIVER"] = "alsa"
os.environ["AUDIODEV"] = card_str

from robot_hat import Servo
from robot_hat import Motors
from robot_hat import Music

import pygame
from picamera2 import Picamera2, Preview
import time

camera = Picamera2()

SIZE = (300, 224)

camera.preview_configuration.main.size = SIZE
camera.preview_configuration.main.format = 'RGB888'  # Matches Pygame's expectations
camera.configure("preview")
camera.start()

def start_cam():
    camera.start_preview(Preview.QTGL)

    camera.start()

def capture_img(name):
    image = camera.capture_file(name + '.jpg')

motors = Motors()
pygame.mixer.init()

motors.set_left_id = 1
motors.set_right_id = 2

steer_servo = Servo(0)

cam_yaw_servo = Servo(1)
cam_pitch_servo = Servo(2)

yaw = 0
pitch = 0

horn_path = 'Toy Honk.wav'
image_folder = 'Camera'

horn_sound = pygame.mixer.Sound(horn_path)

pygame.init()
pygame.joystick.init()

font = pygame.font.Font(None, 24)

while pygame.joystick.get_count() == 0:
    pass

controller = pygame.joystick.Joystick(0)
controller.init()
print(f'Connected to: {controller.get_name()}')

screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption('Controller Car V2')

controller_img = pygame.image.load('controller_img.jpg')

button_coords = [
                 (389, 117), (422, 82), (352, 82), (387, 47),
                 (144, 32), (236, 150), (332, 32), (350, 300),
                 (400, 300), (65, 0), (357, 0)
                ]

button_type = ['circle', 'circle', 'circle', 'circle',
               'circle', 'circle', 'circle', 'none',
               'none', 'square', 'square']

mouse = pygame.mouse

# controller buttons
CROSS = 0
CIRCLE = 1
TRI = 2
SQUARE = 3

L_BUMPER = 9
R_BUMPER = 10

L_STICK = 7
R_STICK = 8

PS_BUTTON = 5

last_button = [
    False, False, False, False,
    False, False, False, False,
    False, False, False
]

buttons = [
    False, False, False, False,
    False, False, False, False,
    False, False, False
]

throttle = 0
steering = 0

yaw_stick = 0
pitch_stick = 0

images_taken = 0

year = time.localtime().tm_year
month = time.localtime().tm_mon
day = time.localtime().tm_mday
hour = time.localtime().tm_hour
min = time.localtime().tm_min
sec = time.localtime().tm_sec

def update_buttons():
    for i in range(len(buttons)):
        raw_button = bool(controller.get_button(i))
        buttons[i] = raw_button and not last_button[i]
        last_button[i] = raw_button

def draw_controller():
    screen.blit(controller_img, (0, 0))

    for i in range(len(buttons)):
        button = last_button[i]

        color = (255, 0, 0) if button else (0, 0, 0)

        if button:
            if button_type[i] == 'circle':
                pygame.draw.circle(screen, color, button_coords[i], 15)
            elif button_type[i] == 'square':
                pygame.draw.rect(screen, color, pygame.Rect(button_coords[i][0], button_coords[i][1], 50, 25))

    left_x, left_y = 162, 146
    right_x, right_y = 312, 148

    left_x += steering
    left_y -= throttle / 2

    right_x += controller.get_axis(2) * 30
    right_y += controller.get_axis(3) * 30

    color = (255, 0, 0) if last_button[L_STICK] else (0, 0, 0)
    pygame.draw.circle(screen, color, (left_x, left_y), 25)
    color = (255, 0, 0) if last_button[R_STICK] else (0, 0, 0)
    pygame.draw.circle(screen, color, (right_x, right_y), 25)
    
def draw_debug_txt(txt, x, y):
    for i in range(len(txt)):
        line = txt[i]
        debug_txt = font.render(line, True, (0, 0, 0))
        screen.blit(debug_txt, (x, y + i * 24))

try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        if pygame.joystick.get_count == 0:
            raise(RuntimeError, f'Controller "{controller.get_name()}" disconnected.')
        pygame.event.pump()

        throttle = -int(controller.get_axis(1) * 60)
        steering = int(controller.get_axis(0) * 30)

        yaw_stick = controller.get_axis(2)
        pitch_stick = controller.get_axis(3)

        if abs(yaw_stick) < 0.2: yaw_stick = 0
        if abs(pitch_stick) < 0.2: pitch_stick = 0

        yaw -= yaw_stick
        pitch += pitch_stick

        update_buttons()

        horn = buttons[CROSS]
        picture = buttons[L_BUMPER]

        zero = buttons[R_STICK]

        if abs(throttle) < 5: throttle = 0
        if abs(steering) < 5: steering = 0

        if (horn):
            horn_sound.play()

        if (picture):
            year = time.localtime().tm_year
            month = time.localtime().tm_mon
            day = time.localtime().tm_mday
            hour = time.localtime().tm_hour
            min = time.localtime().tm_min
            sec = time.localtime().tm_sec

            time_str = f'{month}-{day}-{year} {hour}-{min}-{sec}'

            capture_img(image_folder + '/' + time_str)

            images_taken += 1
            print(f'Took picture: {time_str}')

        if zero:
            yaw = 0
            pitch = 0

        motors.speed(-throttle, throttle)
        steer_servo.angle(steering)
        cam_yaw_servo.angle(yaw)
        cam_pitch_servo.angle(pitch)

        debug_str = []
        debug_str.append(f'Drivetrain:')
        debug_str.append(f'    Throttle: {throttle}, Steering: {steering}°')
        debug_str.append(f'Camera:')
        debug_str.append(f'    Yaw: {round(-yaw, 2)}°, Pitch: {round(pitch, 2)}°')
        if images_taken > 0: debug_str.append(f'    Last image taken on {month}/{day}/{year} at {(hour - 1) % 12 + 1}:{min}:{sec} {'AM' if hour < 12 else 'PM'}')

        array = camera.capture_array()
        camera_feed = pygame.image.frombuffer(array.data, SIZE, 'RGB')

        screen.fill((255, 255, 255))
        draw_controller()
        screen.blit(camera_feed, (500, 0))

        draw_debug_txt(debug_str, 0, 300)

        pygame.display.flip()

except KeyboardInterrupt:
    print('\nStopping Car...')
    
finally:
    motors.speed(0, 0)
    steer_servo.angle(0)
