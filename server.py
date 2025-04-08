import os
import socket, pickle
import threading
import time

from objects import *

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

port = 50903

s.bind(('', port))
print(socket.gethostbyname(socket.gethostname()))
print('Listening to port: ', port)

s.listen(5)
print('Socket is listening')

connections:list[socket.socket] = []
client_threads:list[threading.Thread] = []

running = True

s.settimeout(1)

time_since_last_interaction = time.time()

def clients():
    global time_since_last_interaction
    while running:
        try:
            # Accept connection
            c, addr = s.accept()
            connections.append(c)
            print('Connection from ', addr)
            c.send('Thanks for connecting! To disconnect, close the application or kill the terminal.'.encode())

            time_since_last_interaction = time.time()

            # Create a receive and send thread for new client
            # This thread will send a received message to all other clients
            client_thread = threading.Thread(target=lambda : receive_and_send_messages(c))
            client_thread.start()
            client_threads.append(client_thread)
        except socket.timeout:
            pass
        except:
            raise

def receive_and_send_messages(client: socket.socket):
    global time_since_last_interaction
    while running:
        try:
            data = client.recv(1024)
            time_since_last_interaction = time.time()
            # If data is valid, then perform actions
            # If not valid, then stop receiving from this client (client has disconnected)
            if len(data) > 0:
                msg:Message = pickle.loads(data)

                # Check for intentional disconnection
                if msg.text == 'close':
                    index = connections.index(client)
                    client_threads.pop(index)
                    connections.pop(index)
                    print('Intentional disconnect')
                    break
                
                # Verify connections, remove any clients not connected
                temp_list = connections.copy()
                for i, c in enumerate(temp_list):
                    try:
                        c.send(pickle.dumps(Message('')))
                    except BrokenPipeError:
                        client_threads.pop(i)
                        connections.pop(i)
                        print('Client not connected')
                    except:
                        raise

                # Send message to all clients
                for c in connections:
                    if client == c:
                        continue
                    try:
                        c.send(data)
                    except BrokenPipeError:
                        index = connections.index(c)
                        client_threads.pop(i)
                        connections.pop(i)
                    except:
                        raise
            else:
                break
        except socket.timeout:
            pass
        except:
            raise

def server_idle_loop():
    global running
    while running:
        if time.time() - time_since_last_interaction > 7200:
            running = False
            return
        
def server_close_prompt():
    global running
    while running:
        inp = input()
        # Close server on 'close' message
        if inp.lower().strip() == 'close':
            running = False
            break

# Start threads
client_connection_thread = threading.Thread(target=clients)
client_connection_thread.start()
server_idle_thread = threading.Thread(target=server_idle_loop)
server_idle_thread.start()
server_close_thread = threading.Thread(target=server_close_prompt)
server_close_thread.start()

while running:
    pass

try:
    for c in connections:
        c.send('close'.encode())
except:
    raise
finally:
    s.close()
    os._exit(0)