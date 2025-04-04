import os
import socket
import threading
import time

import ptext

import pygame as pg
from pygame import Color

import numpy as np

user = input('Username: ')

# Pygame setup
pg.init()

# Display
display = pg.display.set_mode((800, 600))
pg.display.set_caption(user)
bg_color = Color(128, 128, 128)

# Font
font = pg.font.Font('font.ttf', 32)
ptext.DEFAULT_FONT_NAME = 'font.ttf'


# Messages
chat = []
max_lines = 14
chat_area = pg.rect.Rect(25, 25, display.get_width() - 50, display.get_height() - 50)

# Message box
send = False
typed_message = ''
valid_keys = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',
              'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
              '1','2','3','4','5','6','7','8','9','0','`','~','!','@','#','$','%','^','&','*','(',')','-','_','=','+',
              '[',']','{','}','\\','|',';',':','\'','"',',','.','<','>','/','?',' ']
message_box_surface = pg.Surface((display.get_width() - 50, 75))
backspace_delay = 0.15
backspace_time = 0

# Delta time
dt = 0
last_time = time.time()

# Client setup
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 50903
s.settimeout(5)

# School ip -> 172.19.67.xxx
# House ip -> 192.168.254.xx

try:
    s.connect(('172.19.67.101', port))
    print(socket.gethostbyname(socket.gethostname()))
    time_since_last_interaction = time.time()
except socket.timeout:
    raise
except ConnectionError as e:
    print('Connection error. Make sure your IPv4 address and port number are correct. Also make sure the server is alive.')
    raise e

print(s.recv(1024).decode())

running = True

def send_messages():
    global running, time_since_last_interaction, chat, send, typed_message
    while running:
        while not send:
            pass
        send = False

        try:
            # Send text
            s.send(f'{user}: {typed_message}'.encode())
            chat.append(f'{user}: {typed_message}' + '\n')
            chat = chat[-max_lines:]
            time_since_last_interaction = time.time()
            typed_message = ''
        except socket.timeout:
            pass
        except:
            print('Failed to send')
            running = False
            break

def receive_messages():
    global running, time_since_last_interaction, chat
    while running:
        try:
            data = s.recv(1024)

            # Disconnect if server closes
            if data.decode() == 'close':
                running = False
                break

            # Print server message
            if len(data) > 0:
                print(data.decode())
                chat.append(data.decode() + '\n')
                chat = chat[-max_lines:]
            time_since_last_interaction = time.time()
        except socket.timeout:
            pass
        except:
            running = False
            break

send_messages_thread = threading.Thread(target=send_messages)
receive_messages_thread = threading.Thread(target=receive_messages)

send_messages_thread.start()
receive_messages_thread.start()

def main_loop():
    global running, typed_message, send, backspace_time, last_time
    while running:
        # Disconnect client if no interaction happens in 1 hour
        if time.time() - time_since_last_interaction > 3600:
            pg.quit()
            running = False
            return

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                running = False
                return

            if event.type == pg.KEYDOWN:
                # Quit if escape key pressed
                if event.key == pg.K_ESCAPE:
                    pg.quit()
                    running = False
                    return
                
                # Check unicode validity, then add it to the typed message
                if event.unicode in valid_keys:
                    typed_message += event.unicode

                # Send the message
                if event.key == pg.K_RETURN and len(typed_message) > 0:
                    send = True

        dt = time.time() - last_time
        last_time = time.time()


        keys = pg.key.get_pressed()

        backspace_time -= dt
        if keys[pg.K_BACKSPACE] and backspace_time <= 0:
            backspace_time = backspace_delay
            typed_message = typed_message[:len(typed_message) - 1]
                


        display.fill(bg_color)

        # Messages
        chat_str = ''.join(chat)
        ptext.draw(chat_str, (chat_area.x, chat_area.y), width=chat_area.width, color=(255, 255, 255))

        # Message box
        message_box_surface.fill(Color(175, 175, 175))
        x = 25
        y = display.get_height() - 100
        text_surface = ptext.getsurf(typed_message, width=message_box_surface.get_width(), color=(30, 30, 30)) # Write text
        message_box_surface.blit(text_surface, (0,-max(0, text_surface.get_height() - message_box_surface.get_height())))

        display.blit(message_box_surface, (x, y))
        pg.display.update()

main_loop()

try:
    s.send('close'.encode())
    s.close()
except:
    raise
finally:
    print('Done running')
    os._exit(0)