import os
import socket
import threading
import time

import pygame as pg
from pygame import Color

user = input('Username: ')

# Pygame setup
pg.init()

# Display
display = pg.display.set_mode((800, 600))
bg_color = Color(128, 128, 128)

# Font
font = pg.font.Font('font.ttf', 32)

# Client setup
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 50903
s.settimeout(5)

# School ip -> 172.19.67.112
# House ip -> 192.168.254.99

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
    global running, time_since_last_interaction, chat
    while running:
        message = input('')
        if message.lower().strip() == 'close':
            running = False
            break
        
        try:
            s.send(f'{user}: {message}'.encode())
            chat.append(f'{user}: {message}' + '\n')
            chat = chat[-10:]
            time_since_last_interaction = time.time()
        except socket.timeout:
            pass
        except:
            print('Failed to send message')
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
                chat = chat[-10:]
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

chat = []
max_lines = 13

def main_loop():
    global running
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
                if event.key == pg.K_ESCAPE:
                    pg.quit()
                    running = False
                    return

        chat_objs = []
        for msg in chat:
            surf:pg.Surface = font.render(msg, False, Color(255, 255, 255))
            chat_objs.insert(0, surf)
        
        display.fill(bg_color)

        y = display.get_height()
        for surf in chat_objs:
            y -= surf.get_height()
            display.blit(surf, (display.get_width()/2 - surf.get_width()/2, y, surf.get_width(), surf.get_height()))

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