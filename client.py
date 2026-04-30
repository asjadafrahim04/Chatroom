import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

HOST = '127.0.0.1'
PORT = 12345

class ChatClient:
    def __init__(self):
        self.socket = None
        self.username = None
        self.is_admin = False
        self.running = True
        
        self.window = tk.Tk()
        self.window.title("Chatroom")
        self.window.geometry("900x600")
        self.window.configure(bg='#2c3e50')
        
        self.show_connection_dialog()
        
    def show_connection_dialog(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Connect to Chatroom")
        dialog.geometry("350x350")
        dialog.configure(bg='#34495e')
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Server IP
        tk.Label(dialog, text="Server IP:", bg='#34495e', fg='white', font=('Arial', 11)).pack(pady=(20,5))
        ip_entry = tk.Entry(dialog, width=30, font=('Arial', 11))
        ip_entry.insert(0, HOST)
        ip_entry.pack(pady=5)
        
        # Port
        tk.Label(dialog, text="Port:", bg='#34495e', fg='white', font=('Arial', 11)).pack(pady=5)
        port_entry = tk.Entry(dialog, width=30, font=('Arial', 11))
        port_entry.insert(0, str(PORT))
        port_entry.pack(pady=5)
        
        # Role
        tk.Label(dialog, text="Role:", bg='#34495e', fg='white', font=('Arial', 11)).pack(pady=10)
        role_var = tk.StringVar(value="USER")
        tk.Radiobutton(dialog, text="User", variable=role_var, value="USER", 
                      bg='#34495e', fg='white', selectcolor='#2c3e50').pack()
        tk.Radiobutton(dialog, text="Admin (First only)", variable=role_var, value="ADMIN", 
                      bg='#34495e', fg='white', selectcolor='#2c3e50').pack()
        
        # Status label
        status_label = tk.Label(dialog, text="Ready to connect", bg='#34495e', fg='yellow')
        status_label.pack(pady=10)
        
        # Connect Button
        def do_connect():
            try:
                ip = ip_entry.get()
                port = int(port_entry.get())
                role = role_var.get()
                
                status_label.config(text="Connecting...")
                dialog.update()
                
                print(f"DEBUG: Connecting to {ip}:{port}")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((ip, port))
                print("DEBUG: Connected!")
                
                # Receive ASK_ROLE from server
                response = self.socket.recv(1024).decode()
                print(f"Server: {response}")
                
                if response == "ASK_ROLE":
                    # Send role
                    self.socket.send(role.encode())
                    
                    if role == "ADMIN":
                        self.is_admin = True
                        # Receive SET_PASSWORD
                        response2 = self.socket.recv(1024).decode()
                        if response2 == "SET_PASSWORD":
                            password = simpledialog.askstring("Set Password", "Create group password:", show='*', parent=dialog)
                            if password:
                                self.socket.send(password.encode())
                                # Receive OK
                                self.socket.recv(1024)
                                # Receive GET_USERNAME
                                response3 = self.socket.recv(1024).decode()
                                if response3 == "GET_USERNAME":
                                    self.get_username(dialog, status_label)
                            else:
                                self.socket.close()
                                
                    elif role == "USER":
                        self.is_admin = False
                        # Receive ASK_PASSWORD
                        response2 = self.socket.recv(1024).decode()
                        if response2 == "ASK_PASSWORD":
                            password = simpledialog.askstring("Password", "Enter group password:", show='*', parent=dialog)
                            if password:
                                self.socket.send(password.encode())
                                # Receive PASSWORD_OK or WRONG_PASSWORD
                                response3 = self.socket.recv(1024).decode()
                                if response3 == "PASSWORD_OK":
                                    # Receive GET_USERNAME
                                    response4 = self.socket.recv(1024).decode()
                                    if response4 == "GET_USERNAME":
                                        self.get_username(dialog, status_label)
                                else:
                                    messagebox.showerror("Error", "Wrong password!")
                                    self.socket.close()
                            else:
                                self.socket.close()
                                
            except Exception as e:
                print(f"DEBUG ERROR: {e}")
                messagebox.showerror("Error", f"Connection failed: {e}")
                status_label.config(text=f"Error: {str(e)[:30]}")
                self.socket = None
        
        connect_button = tk.Button(dialog, text="CONNECT", command=do_connect, 
                                   bg='#3498db', fg='white', font=('Arial', 12, 'bold'), 
                                   padx=20, pady=5)
        connect_button.pack(pady=20)
        
    def get_username(self, dialog, status_label):
        status_label.config(text="Enter username...")
        dialog.update()
        username = simpledialog.askstring("Username", "Enter your username:", parent=dialog)
        if username:
            self.username = username
            self.socket.send(username.encode())
            response = self.socket.recv(1024).decode()
            if response == "SUCCESS":
                dialog.destroy()
                self.setup_gui()
                self.start_receiving()
            else:
                messagebox.showerror("Error", f"Failed: {response}")
                self.socket.close()
    
    def setup_gui(self):
        # Left panel - Users
        left_frame = tk.Frame(self.window, bg='#34495e', width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        tk.Label(left_frame, text="📡 ONLINE USERS", bg='#34495e', fg='#3498db', 
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        self.users_listbox = tk.Listbox(left_frame, bg='#2c3e50', fg='white', 
                                        font=('Arial', 10), height=25)
        self.users_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right panel - Chat
        right_frame = tk.Frame(self.window, bg='#2c3e50')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.chat_display = scrolledtext.ScrolledText(right_frame, bg='#ecf0f1', fg='#2c3e50', 
                                                       font=('Arial', 11), wrap=tk.WORD)
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Input area
        bottom_frame = tk.Frame(right_frame, bg='#2c3e50')
        bottom_frame.pack(fill=tk.X, pady=10)
        
        self.msg_entry = tk.Entry(bottom_frame, bg='white', fg='#2c3e50', font=('Arial', 11))
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10))
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        
        send_button = tk.Button(bottom_frame, text="SEND", command=self.send_message, 
                                bg='#3498db', fg='white', font=('Arial', 10, 'bold'), padx=20)
        send_button.pack(side=tk.RIGHT)
        
        # Buttons
        btn_frame = tk.Frame(right_frame, bg='#2c3e50')
        btn_frame.pack(fill=tk.X, pady=5)
        
        private_button = tk.Button(btn_frame, text="PRIVATE MSG", command=self.private_msg, 
                                   bg='#e67e22', fg='white')
        private_button.pack(side=tk.LEFT, padx=5)
        
        leave_button = tk.Button(btn_frame, text="LEAVE", command=self.leave_group, 
                                 bg='#e74c3c', fg='white')
        leave_button.pack(side=tk.LEFT, padx=5)
        
        exit_button = tk.Button(btn_frame, text="EXIT", command=self.exit_chat, 
                                bg='#95a5a6', fg='white')
        exit_button.pack(side=tk.RIGHT, padx=5)
        
        # Only show kick button for admin
        if self.is_admin:
            kick_button = tk.Button(btn_frame, text="KICK", command=self.kick_user, 
                                    bg='#c0392b', fg='white')
            kick_button.pack(side=tk.LEFT, padx=5)
        
        self.window.title(f"💬 CHATROOM - {self.username}")
        self.add_message("SYSTEM", f"Welcome to the chatroom! You are logged in as {self.username}")
        if self.is_admin:
            self.add_message("SYSTEM", "You are the ADMIN. You can kick users.")
    
    def send_message(self):
        msg = self.msg_entry.get().strip()
        if msg:
            try:
                self.socket.send(msg.encode())
                
                from datetime import datetime
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.add_message("YOU", msg)
                
                self.msg_entry.delete(0, tk.END)
            except Exception as e:
                self.add_message("ERROR", f"Failed to send message: {e}")
    
    def private_msg(self):
        selected = self.users_listbox.curselection()
        if selected:
            target = self.users_listbox.get(selected[0])
            if target != self.username:
                msg = simpledialog.askstring("Private Message", f"Message to {target}:")
                if msg:
                    try:
                        self.socket.send(f"PRIVATE:{target}:{msg}".encode())
                        from datetime import datetime
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        self.add_message("YOU (PRIVATE to " + target + ")", msg)
                    except:
                        self.add_message("ERROR", "Failed to send private message!")
            else:
                messagebox.showinfo("Info", "Cannot send private message to yourself!")
        else:
            messagebox.showinfo("Info", "Select a user from the list first!")
    
    def kick_user(self):
        if not self.is_admin:
            messagebox.showerror("Error", "Only admin can kick users!")
            return
            
        selected = self.users_listbox.curselection()
        if selected:
            target = self.users_listbox.get(selected[0])
            if target != self.username:
                if messagebox.askyesno("Kick User", f"Kick {target} from the chatroom?"):
                    try:
                        self.socket.send(f"KICK:{target}".encode())
                        self.add_message("SYSTEM", f"You kicked {target}")
                    except:
                        self.add_message("ERROR", "Failed to kick user!")
            else:
                messagebox.showinfo("Info", "You cannot kick yourself!")
        else:
            messagebox.showinfo("Info", "Select a user to kick!")
    
    def leave_group(self):
        if messagebox.askyesno("Leave", "Leave the chatroom?"):
            self.running = False
            try:
                self.socket.close()
            except:
                pass
            self.window.destroy()
    
    def exit_chat(self):
        if messagebox.askyesno("Exit", "Exit chatroom?"):
            self.running = False
            try:
                self.socket.close()
            except:
                pass
            self.window.quit()
            self.window.destroy()
    
    def start_receiving(self):
        def receive():
            while self.running:
                try:
                    msg = self.socket.recv(1024).decode()
                    if not msg:
                        break
                    
                    print(f"Received: {msg}")
                    
                    if msg.startswith("USERS:"):
                        users = msg[6:].split(",")
                        self.users_listbox.delete(0, tk.END)
                        for user in users:
                            if user:
                                self.users_listbox.insert(tk.END, user)
                    elif msg.startswith("SYSTEM:"):
                        self.add_message("📢 SYSTEM", msg[7:])
                    elif msg.startswith("PRIVATE from"):
                        self.add_message("🔒 PRIVATE", msg)
                    elif msg == "KICKED":
                        messagebox.showwarning("Kicked", "You were kicked by the admin!")
                        self.running = False
                        self.window.destroy()
                        break
                    elif msg.startswith("ERROR:"):
                        messagebox.showerror("Error", msg[6:])
                    else:
                        # Regular chat message from others
                        self.add_message("💬", msg)
                except Exception as e:
                    print(f"Error receiving: {e}")
                    break
        
        thread = threading.Thread(target=receive)
        thread.daemon = True
        thread.start()
    
    def add_message(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding for different message types
        if sender == "YOU":
            self.chat_display.insert(tk.END, f"[{timestamp}] 👤 {sender}: {message}\n", "you")
            self.chat_display.tag_config("you", foreground="#2980b9", font=('Arial', 11, 'bold'))
        elif sender == "📢 SYSTEM":
            self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n", "system")
            self.chat_display.tag_config("system", foreground="#27ae60", font=('Arial', 10, 'italic'))
        elif sender == "🔒 PRIVATE":
            self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n", "private")
            self.chat_display.tag_config("private", foreground="#e67e22", font=('Arial', 10, 'bold'))
        elif sender == "💬":
            self.chat_display.insert(tk.END, f"[{timestamp}] {message}\n")
        else:
            self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    client = ChatClient()
    client.run()