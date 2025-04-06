import os
import socket, pickle
import threading
import time

import ptext

import pygame as pg
from pygame import Color

from colorsys import hsv_to_rgb

from objects import *

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
chat:list[Message] = []
max_messages = 20
chat_area = pg.rect.Rect(25, 25, display.get_width() - 125, display.get_height() - 125)

# Message box
send = False
typed_message = ''
valid_keys = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',
              'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
              '1','2','3','4','5','6','7','8','9','0','`','~','!','@','#','$','%','^','&','*','(',')','-','_','=','+',
              '[',']','{','}','\\','|',';',':','\'','"',',','.','<','>','/','?',' ']
message_box_surface = pg.Surface((display.get_width() - 50, 75))
max_chars = 500 - len(f'{user}: ')

num_colors = 15
color_choices = [(255, 255, 255), (0, 0, 0)]
color_choices += [(hsv_to_rgb(_/num_colors, 1, 1)[0]*255, hsv_to_rgb(_/num_colors, 1, 1)[1]*255, hsv_to_rgb(_/num_colors, 1, 1)[2]*255) for _ in range(num_colors)]
current_color = 0

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
    s.connect(('', port))
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
            msg = Message(f'{user}: {typed_message}'.strip(), color_choices[current_color])
            msg_data = pickle.dumps(msg)

            s.send(msg_data)
            chat.append(msg)
            chat = chat[-max_messages:]
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

            # Check received data
            if len(data) > 0:
                msg:Message = pickle.loads(data)

                # Check if message is a connection test message.
                # Users cant send empty messages, so this has to be a test message.
                if msg.text == '':
                    continue
                
                # Disconnect if server closes
                if msg.text == 'close':
                    running = False
                    break

                chat.append(msg)
                print('receive message')
                chat = chat[-max_messages:]
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
    global running, typed_message, send, last_time, current_color
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
                if event.unicode in valid_keys and len(typed_message) < max_chars:
                    typed_message += event.unicode

                if event.key == pg.K_BACKSPACE:
                    typed_message = typed_message[:len(typed_message) - 1]

                current_color = min(max(current_color + int(event.key == pg.K_UP) - int(event.key == pg.K_DOWN), 0), len(color_choices)-1)

                # Send the message
                if event.key == pg.K_RETURN and len(typed_message) > 0:
                    send = True

        dt = time.time() - last_time
        last_time = time.time()


        display.fill(bg_color)

        # Display Messages
        chat_surfs:list[pg.Surface] = []
        chat_height = 0
        for msg in chat:
            surf = ptext.getsurf(msg.text, width=chat_area.width, color=msg.color)
            chat_height += surf.get_height()
            chat_surfs.append(surf)

        y = chat_area.y
        for surf in chat_surfs:
            display.blit(surf, (chat_area.x,y - max(chat_height - chat_area.height, 0)))
            y += surf.get_height()

        # Message box
        message_box_surface.fill(Color(175, 175, 175))
        x = 25
        y = display.get_height() - 100
        text_surface = ptext.getsurf(typed_message, width=message_box_surface.get_width(), color=color_choices[current_color]) # Write text
        message_box_surface.blit(text_surface, (0,-max(0, text_surface.get_height() - message_box_surface.get_height())))

        display.blit(message_box_surface, (x, y))
        pg.draw.line(display, Color(0,0,0), chat_area.bottomleft, chat_area.bottomright, 3)
        pg.display.update()

main_loop()

try:
    s.send(Message('close'))
    s.close()
except:
    raise
finally:
    print('Done running')
    os._exit(0)