import socket
import threading
import datetime
import sys

# A dictionary to store chat history
# Format: {"ip:port": [("sent", "timestamp", "message"), ("received", "timestamp", "message")]}
chat_history = {}
# A lock to ensure thread-safe access to chat_history
history_lock = threading.Lock()

# This will be set to this user's listening address (e.g., "192.168.1.6:5000")
my_listening_address = ""

def handle_incoming_connection(connection):
    """
    Handles an incoming connection from another peer.
    This runs in a new thread for each connection.
    """
    try:
        data = connection.recv(1024)
        if data:
            message_str = data.decode('utf-8')
            
            # Message format: "[sender_ip:port] [time] [content]"
            # We split on the first two spaces to isolate the 3 parts
            try:
                sender_address, timestamp, content = message_str.split(' ', 2)
                
                # Log the received message
                print(f"\n[Received from {sender_address}] @ {timestamp}:\n  {content}\n")
                
                # Update the chat history
                with history_lock:
                    if sender_address not in chat_history:
                        chat_history[sender_address] = []
                    chat_history[sender_address].append(("received", timestamp, content))
                    
            except ValueError:
                print(f"\n[Received malformed message]: {message_str}\n")
                
    except Exception as e:
        print(f"\n[Error handling connection]: {e}\n")
    finally:
        connection.close()

def start_server(host, port):
    """
    Starts the listening server on a background thread.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Reuse the address to avoid "Address already in use" errors on restart
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"[Server Started] Listening for connections on {host}:{port}")
        
        while True:
            # Wait for and accept an incoming connection
            conn, addr = server_socket.accept()
            # Start a new thread to handle this connection
            # daemon=True so threads exit when the main program exits
            handler_thread = threading.Thread(target=handle_incoming_connection, args=(conn,), daemon=True)
            handler_thread.start()
            
    except OSError as e:
        print(f"\n[FATAL ERROR] Could not start server: {e}")
        print("This port might be in use. Please try a different port.")
        sys.exit(1) # Exit the entire program
    except Exception as e:
        print(f"\n[Server Error]: {e}\n")
    finally:
        server_socket.close()

def send_message(target_ip, target_port, content):
    """
    Connects to a peer's listening socket to send a message.
    """
    global my_listening_address
    
    # Create the timestamp
    timestamp = datetime.datetime.now().isoformat()
    
    # Format the message
    # Format: [sender's listening IP:port] [time] [content]
    message = f"{my_listening_address} {timestamp} {content}"
    
    target_address_str = f"{target_ip}:{target_port}"

    try:
        # Create a new socket for this *outgoing* connection
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set a timeout for the connection attempt
        client_socket.settimeout(5)
        
        client_socket.connect((target_ip, target_port))
        client_socket.sendall(message.encode('utf-8'))
        
        print(f"\n[Message sent to {target_address_str}]\n")
        
        # Update our local chat history
        with history_lock:
            if target_address_str not in chat_history:
                chat_history[target_address_str] = []
            chat_history[target_address_str].append(("sent", timestamp, content))
            
    except socket.timeout:
        print(f"\n[Error] Connection to {target_address_str} timed out.\n")
    except ConnectionRefusedError:
        print(f"\n[Error] Connection to {target_address_str} was refused.\n  (Is the other peer running?)\n")
    except Exception as e:
        print(f"\n[Error sending message to {target_address_str}]: {e}\n")
    finally:
        client_socket.close()

def get_my_ip():
    """
    Finds the local IP address of this machine.
    This is a common, simple way to find the LAN IP.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        # If it fails, fall back to hostname (might be 127.0.0.1)
        print("Could not automatically determine local IP. Using hostname.")
        IP = socket.gethostbyname(socket.gethostname())
    finally:
        s.close()
    return IP

def print_history():
    """
    Prints the formatted chat history from the global dict.
    """
    print("\n--- Chat History ---")
    with history_lock:
        if not chat_history:
            print("  No messages yet.")
        
        for peer, messages in chat_history.items():
            print(f"\n[Peer: {peer}]")
            for direction, time_str, msg in messages:
                # Parse timestamp for cleaner printing
                time_obj = datetime.datetime.fromisoformat(time_str)
                friendly_time = time_obj.strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {direction.upper()} @ {friendly_time}:")
                print(f"    {msg}")
    print("----------------------\n")

def run(my_ip, my_port):
    """
    Main function to run the P2P chat client.
    """
    global my_listening_address

    # 1. Setup Listening Port
    # my_port = 0
    # while True:
    #     try:
    #         port_str = input("Enter your listening port (e.g., 5000): ")
    #         my_port = int(port_str)
    #         if 1024 <= my_port <= 65535:
    #             break
    #         else:
    #             print("Port must be between 1024 and 65535.")
    #     except ValueError:
    #         print("Invalid port. Please enter a number.")

    # 2. Setup Listening IP and Address
    # my_ip = get_my_ip()
    my_listening_address = f"{my_ip}:{my_port}"
    print(f"\nYour listening address is: {my_listening_address}")
    print("Share this with peers so they can message you.")

    # 3. Start the Server Thread
    # We listen on '0.0.0.0' to accept connections from any IP
    server_thread = threading.Thread(target=start_server, args=('0.0.0.0', my_port), daemon=True)
    server_thread.start()

    # 4. Start the Main UI Loop
    while True:
        print("\n--- P2P Chat Menu ---")
        print("1. Send a message")
        print("2. View chat history")
        print("q. Quit")
        choice = input("Enter your choice: ").strip().lower()

        if choice == '1':
            try:
                target_addr_str = input("Enter target IP:port (e.g., 192.168.1.12:7000): ")
                target_ip, target_port_str = target_addr_str.split(':')
                target_port = int(target_port_str)
                
                content = input("Enter message: ")
                if content:
                    # Send the message in a separate thread to keep UI responsive
                    # (though it's fast, this is good practice)
                    send_thread = threading.Thread(target=send_message, args=(target_ip, target_port, content), daemon=True)
                    send_thread.start()
                else:
                    print("Cannot send empty message.")

            except ValueError:
                print("Invalid format. Please use IP:PORT (e.g., 192.168.1.12:7000)")
            except Exception as e:
                print(f"An error occurred: {e}")
        
        elif choice == '2':
            print_history()
        
        elif choice == 'q':
            print("Exiting...")
            sys.exit(0)
        
        else:
            print("Invalid choice. Please try again.")

