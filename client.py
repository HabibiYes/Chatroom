import sys, os
import socket, json
import threading
import time

import pygame as pg
from pygame import Color

import ptext
from colorsys import hsv_to_rgb
from messages import *

def main():
    valid_keys = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',
                'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
                '1','2','3','4','5','6','7','8','9','0','`','~','!','@','#','$','%','^','&','*','(',')','-','_','=','+',
                '[',']','{','}','\\','|',';',':','\'','"',',','.','<','>','/','?',' ']
    
    # Font
    ptext.DEFAULT_FONT_NAME = 'font.ttf'

    # Pygame setup
    pg.init()

    # Display
    display = pg.display.set_mode((800, 600))
    bg_color = Color(128, 128, 128)

    # Get username and IPv4
    inputs_done = [False, False]
    current_input = 0
    user = ''
    ip = ''
    pg.event.set_allowed([pg.KEYDOWN])
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN:
                if event.unicode in valid_keys:
                    if current_input == 0:
                        user += event.unicode
                        print(user)
                    elif current_input == 1:
                        ip += event.unicode
                        print(ip)

                if event.key == pg.K_RETURN:
                    inputs_done[current_input] = True
                    current_input += 1
                    if current_input == 2:
                        break

                if event.key == pg.K_BACKSPACE:
                    if current_input == 0:
                        user = user[0:len(user)-1]
                    if current_input == 1:
                        ip = ip[0:len(ip)-1]

                if event.key == pg.K_ESCAPE:
                    pg.quit()
                    sys.exit()
        
        if all(inputs_done):
            break

        display.fill(bg_color)

        surf1 = ptext.getsurf('User: ' + user, width=display.get_width())
        surf2 = ptext.getsurf('IPv4: ' + ip, width=display.get_width())
        display.blit(surf1, (0,0))
        display.blit(surf2, (0,surf1.get_height()))

        pg.display.update()

    # Messages
    chat:list[dict] = []
    max_messages = 20
    chat_area = pg.rect.Rect(25, 25, display.get_width() - 125, display.get_height() - 125)
    scroll = 0
    scroll_speed = 5

    # Message box
    send = False
    typed_message = ''
    message_box_surface = pg.Surface((display.get_width() - 50, 75))
    max_chars = 500 - len(f'{user}: ')

    # Colors
    num_colors = 15
    color_choices = [(255, 255, 255), (0, 0, 0)]
    color_choices += [(hsv_to_rgb(_/num_colors, 1, 1)[0]*255, hsv_to_rgb(_/num_colors, 1, 1)[1]*255, hsv_to_rgb(_/num_colors, 1, 1)[2]*255) for _ in range(num_colors)]
    current_color = 0

    # Delta time
    dt = 0
    ticks = pg.time.get_ticks()
    last_ticks = ticks
    def get_delta_time():
        nonlocal dt, ticks, last_ticks
        ticks = pg.time.get_ticks()
        dt = (ticks - last_ticks) / 1000
        last_ticks = ticks

    # Client setup
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 50903
    s.settimeout(5)

    # Connect to server
    try:
        s.connect((ip, port))
        print(socket.gethostbyname(socket.gethostname()))
        time_since_last_interaction = time.time()
    except socket.timeout:
        raise
    except ConnectionError as e:
        print('Connection error. Make sure your IPv4 address and port number are correct. Also make sure the server is alive.')
        raise e

    print(s.recv(1024).decode())

    running = True

    def send_message():
        nonlocal running, time_since_last_interaction, chat, typed_message
        try:
            # Create data from message object to send
            msg = create_message(f'{user}: {typed_message}'.strip(), color_choices[current_color])
            msg_data = json.dumps(msg)

            # Send message
            s.send(msg_data.encode())
            chat.append(msg)
            chat = chat[-max_messages:]
            time_since_last_interaction = time.time()
            typed_message = ''
        except socket.timeout:
            return
        except:
            print('Failed to send')
            running = False
            return

    def receive_messages():
        nonlocal running, time_since_last_interaction, chat
        while running:
            try:
                data = s.recv(1024)

                # Check received data
                if len(data) > 0:
                    msg:dict = json.loads(data.decode())

                    # Check if message is a connection test message.
                    # Users cant send empty messages, so this has to be a test message.
                    if msg['text'] == '':
                        continue
                    
                    # Disconnect if server closes
                    if msg['text'] == 'close':
                        running = False
                        break

                    chat.append(msg)
                    chat = chat[-max_messages:]
                time_since_last_interaction = time.time()
            except socket.timeout:
                pass
            except:
                running = False
                break

    receive_messages_thread = threading.Thread(target=receive_messages)
    receive_messages_thread.start()

    def main_loop():
        nonlocal running, typed_message, send, current_color, scroll

        pg.event.set_allowed([pg.KEYDOWN, pg.MOUSEWHEEL])
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
                    keys = pg.key.get_pressed()

                    # Quit if escape key pressed
                    if event.key == pg.K_ESCAPE:
                        pg.quit()
                        running = False
                        return
                    
                    # Check unicode validity, then add it to the typed message
                    if event.unicode in valid_keys and len(typed_message) < max_chars:
                        typed_message += event.unicode

                    # New line in message
                    if keys[pg.K_RETURN] and keys[pg.K_LSHIFT]:
                        typed_message += '\n'

                    # Delete most recent character
                    if event.key == pg.K_BACKSPACE:
                        typed_message = typed_message[:len(typed_message) - 1]

                    current_color = min(max(current_color + int(event.key == pg.K_UP) - int(event.key == pg.K_DOWN), 0), len(color_choices)-1)

                    # Send the message
                    if keys[pg.K_RETURN] and not keys[pg.K_LSHIFT] and len(typed_message) > 0:
                        send_message()

                if event.type == pg.MOUSEWHEEL:
                    scroll += event.y * scroll_speed
                    scroll = max(scroll, 0)

            get_delta_time()


            display.fill(bg_color)

            # Get height of all chat messages to keep the on screen
            chat_surfs:list[pg.Surface] = []
            chat_height = 0
            for msg in chat:
                surf = ptext.getsurf(msg['text'], width=chat_area.width, color=msg['color'])
                chat_height += surf.get_height()
                chat_surfs.append(surf)

            # Display Messages
            y = chat_area.y
            for surf in chat_surfs:
                display.blit(surf, (chat_area.x,y - max(chat_height - chat_area.height, 0) + scroll))
                y += surf.get_height()

            # Message box
            message_box_surface.fill(Color(175, 175, 175))
            x = 25
            y = display.get_height() - 100
            text_surface = ptext.getsurf(typed_message, width=message_box_surface.get_width(), color=color_choices[current_color]) # Write text
            message_box_surface.blit(text_surface, (0,-max(0, text_surface.get_height() - message_box_surface.get_height())))

            display.blit(message_box_surface, (x, y))
            pg.display.update()

    main_loop()

    try:
        # Send intentional disconnect message
        s.send(json.dumps(create_message('close')))
        s.close()
    except:
        raise
    finally:
        print('Done running')
        os._exit(0)

if __name__ == '__main__':
    main()