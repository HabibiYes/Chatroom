import os
import socket
import threading
import time

user = input('Username: ')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

port = 50903

s.settimeout(5)

# School ip -> 172.19.67.112
# House ip -> 192.168.254.99

try:
    s.connect(('172.19.67.112', port))
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
    global running, time_since_last_interaction
    while running:
        message = input('')
        if message.lower().strip() == 'close':
            running = False
            break
        
        try:
            s.send(f'{user}: {message}'.encode())
            time_since_last_interaction = time.time()
        except socket.timeout:
            pass
        except:
            print('Failed to send message')
            running = False
            break

def receive_messages():
    global running, time_since_last_interaction
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
while running:
    # Disconnect client if no interaction happens in 1 hour
    if time.time() - time_since_last_interaction > 3600:
        running = False
        break

try:
    s.send('close'.encode())
    s.close()
except:
    raise
finally:
    print('Done running')
    os._exit(0)