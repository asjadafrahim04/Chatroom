import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

clients = []
usernames = []
client_roles = []  # Track roles for each client
group_password = None
admin_exists = False

def broadcast(message, sender=None):
    for client in clients:
        if client != sender:
            try:
                client.send(message.encode())
            except:
                pass

def update_user_list():
    user_list = "USERS:" + ",".join(usernames)
    for client in clients:
        try:
            client.send(user_list.encode())
        except:
            pass

def handle_client(client_socket):
    global group_password, admin_exists
    
    try:
        # Ask for role
        client_socket.send("ASK_ROLE".encode())
        role = client_socket.recv(1024).decode().strip()
        print(f"Role received: {role}")
        
        if role == "ADMIN":
            # Check if admin already exists
            if admin_exists:
                client_socket.send("ERROR:Admin already exists".encode())
                client_socket.close()
                return
            
            admin_exists = True
            
            # Set password
            client_socket.send("SET_PASSWORD".encode())
            group_password = client_socket.recv(1024).decode().strip()
            print(f"Password set: {group_password}")
            client_socket.send("OK".encode())
            
            # Get username
            client_socket.send("GET_USERNAME".encode())
            username = client_socket.recv(1024).decode().strip()
            print(f"Admin username: {username}")
            
            clients.append(client_socket)
            usernames.append(username)
            client_roles.append("ADMIN")
            
            client_socket.send("SUCCESS".encode())
            broadcast(f"SYSTEM: Admin {username} joined the chat!", client_socket)
            update_user_list()
            
            # Message loop
            while True:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                
                if message.startswith("PRIVATE:"):
                    parts = message.split(":", 2)
                    if len(parts) == 3:
                        target = parts[1]
                        msg = parts[2]
                        for i, name in enumerate(usernames):
                            if name == target:
                                clients[i].send(f"PRIVATE from {username}: {msg}".encode())
                                client_socket.send(f"PRIVATE to {target}: {msg}".encode())
                                break
                elif message.startswith("KICK:"):
                    # Only admin can kick
                    try:
                        sender_index = clients.index(client_socket)
                        if client_roles[sender_index] == "ADMIN":
                            target = message.split(":", 1)[1]
                            kicked = False
                            for i, name in enumerate(usernames):
                                if name == target:
                                    # Send kick signal and close connection
                                    try:
                                        clients[i].send("KICKED".encode())
                                        clients[i].close()
                                    except:
                                        pass
                                    # Remove from lists
                                    clients.pop(i)
                                    usernames.pop(i)
                                    client_roles.pop(i)
                                    broadcast(f"SYSTEM: {target} was kicked by admin {username}", None)
                                    update_user_list()
                                    kicked = True
                                    break
                            if not kicked:
                                client_socket.send(f"ERROR: User {target} not found".encode())
                        else:
                            client_socket.send("ERROR: Only admin can kick users".encode())
                    except ValueError:
                        pass
                else:
                    broadcast(f"{username}: {message}", client_socket)
                    
        elif role == "USER":
            # Check if password is set
            if group_password is None:
                client_socket.send("ERROR:No admin has set password yet".encode())
                client_socket.close()
                return
            
            # Ask for password
            client_socket.send("ASK_PASSWORD".encode())
            password = client_socket.recv(1024).decode().strip()
            
            if password != group_password:
                client_socket.send("WRONG_PASSWORD".encode())
                client_socket.close()
                return
            
            client_socket.send("PASSWORD_OK".encode())
            
            # Get username
            client_socket.send("GET_USERNAME".encode())
            username = client_socket.recv(1024).decode().strip()
            
            # Check if username already taken
            if username in usernames:
                client_socket.send("USERNAME_TAKEN".encode())
                client_socket.close()
                return
            
            clients.append(client_socket)
            usernames.append(username)
            client_roles.append("USER")
            
            client_socket.send("SUCCESS".encode())
            broadcast(f"SYSTEM: {username} joined the chat!", client_socket)
            update_user_list()
            
            # Message loop
            while True:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                
                if message.startswith("PRIVATE:"):
                    parts = message.split(":", 2)
                    if len(parts) == 3:
                        target = parts[1]
                        msg = parts[2]
                        for i, name in enumerate(usernames):
                            if name == target:
                                clients[i].send(f"PRIVATE from {username}: {msg}".encode())
                                client_socket.send(f"PRIVATE to {target}: {msg}".encode())
                                break
                elif message.startswith("KICK:"):
                    # Users cannot kick
                    client_socket.send("ERROR: Only admin can kick users".encode())
                else:
                    broadcast(f"{username}: {message}", client_socket)
        else:
            client_socket.send("INVALID_ROLE".encode())
            client_socket.close()
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Remove client on disconnect
        if client_socket in clients:
            index = clients.index(client_socket)
            name = usernames[index]
            clients.pop(index)
            usernames.pop(index)
            client_roles.pop(index)
            broadcast(f"SYSTEM: {name} left the chat", None)
            update_user_list()

# Start server
print(f"Starting server on {HOST}:{PORT}")
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"Server running! Waiting for connections...")

while True:
    client_socket, address = server.accept()
    print(f"New connection from {address}")
    thread = threading.Thread(target=handle_client, args=(client_socket,))
    thread.start()