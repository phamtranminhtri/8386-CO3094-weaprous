#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
start_p2p
~~~~~~~~~~~~~~~~~
"""

import json
import socket
import argparse
import os
import random
import threading
import datetime
import sys
import queue
import urllib.parse
from collections import defaultdict


from daemon.weaprous import WeApRous

# from daemon import p2p

PORT = 8386  # Default port

app = WeApRous()
accounts = dict()
session_to_account = dict()
account_to_address = dict()
server_ip = ""
server_port = ""
peer_list = []
channels = dict()

send_queue = queue.Queue()  # (peer ip, peer port, message to send)


# store chat history
# Format: {"ip:port": [("sent", "timestamp", "message"), ("received", "timestamp", "message")]}
chat_history = dict()
# Format: {"channel_name": [("ip:port", "timestamp", "message"), ("ip:port", "timestamp", "message")]}
channel_history = dict()

history_lock = threading.Lock()
channel_history_lock = threading.Lock()
channel_list_lock = threading.Lock()

# This will be set to this user's listening address (e.g., "192.168.1.6:5000")
my_listening_address = ""


def handle_incoming_connection(connection):
    """
    Handles an incoming connection from another peer.
    This runs in a new thread for each connection.
    """
    try:
        fragments = []
        while True:
            chunk = connection.recv(4096) 
            if not chunk: 
                break
            fragments.append(chunk)
            # Nếu gói tin nhỏ hơn buffer size, có thể là đã hết tin
            if len(chunk) < 4096: 
                break
        
        data = b"".join(fragments)
        if data:
            message_str = data.decode("utf-8")

            # Message format: "[sender_ip:port] [time] [content]"
            try:
                sender_address, timestamp, content = message_str.split(" ", 2)

                print(
                    f"\n[Received from {sender_address}] @ {timestamp}:\n  {content}\n"
                )

                # Update the chat history
                if content.startswith("[Channel]"):
                    _, channel_name, message = content.split("___")
                    if channel_name in channels:
                        address_list = channels[channel_name]
                        if sender_address not in address_list:
                            with channel_list_lock:
                                address_list.append(sender_address)
                        with channel_history_lock:
                            if channel_name not in channel_history:
                                channel_history[channel_name] = []
                            channel_history[channel_name].append(
                                (sender_address, timestamp, message)
                            )
                else:
                    with history_lock:
                        if sender_address not in chat_history:
                            chat_history[sender_address] = []
                        chat_history[sender_address].append(
                            ("received", timestamp, content)
                        )

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
            handler_thread = threading.Thread(
                target=handle_incoming_connection, args=(conn,), daemon=True
            )
            handler_thread.start()

    except OSError as e:
        print(f"\n[FATAL ERROR] Could not start server: {e}")
        print("This port might be in use. Please try a different port.")
        sys.exit(1)  # Exit the entire program
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

    if content.startswith("[Channel]"):
        # Logic channel giữ nguyên nếu có
        pass 
    else:
        with history_lock:
            if target_address_str not in chat_history:
                chat_history[target_address_str] = []
            # Lưu tin nhắn vào lịch sử ngay lập tức
            chat_history[target_address_str].append(("sent", timestamp, content))
    
    try:
        # Create a new socket for this *outgoing* connection
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(10)

        client_socket.connect((target_ip, target_port))
        client_socket.sendall(message.encode("utf-8"))

        print(f"\n[Message sent to {target_address_str}]\n")

        # update local chat history
        if content.startswith("[Channel]"):
            _, channel_name, message = content.split("___")
            # with channel_history_lock:
            #     if channel_name not in channel_history:
            #         channel_history[channel_name] = []
            #     channel_history[channel_name].append((my_listening_address, timestamp, message))
        else:
            with history_lock:
                if target_address_str not in chat_history:
                    chat_history[target_address_str] = []
                chat_history[target_address_str].append(("sent", timestamp, content))

    except socket.timeout:
        print(f"\n[Error] Connection to {target_address_str} timed out.\n")
    except ConnectionRefusedError:
        print(
            f"\n[Error] Connection to {target_address_str} was refused.\n  (Is the other peer running?)\n"
        )
    except Exception as e:
        print(f"\n[Error sending message to {target_address_str}]: {e}\n")
    finally:
        client_socket.close()


def run(my_ip, my_port):
    """
    Main function to run the P2P chat client.
    """
    global my_listening_address
    my_listening_address = f"{my_ip}:{my_port}"
    print(f"\nYour listening address is: {my_listening_address}")
    print("Share this with peers so they can message you.")

    # server thread listen on '0.0.0.0' to accept connections from any IP
    server_thread = threading.Thread(
        target=start_server, args=("0.0.0.0", my_port), daemon=True
    )
    server_thread.start()

    # main loop
    while True:
        try:
            target_ip, target_port_str, content = send_queue.get()
            target_port = int(target_port_str)

            if content:
                send_thread = threading.Thread(
                    target=send_message,
                    args=(target_ip, target_port, content),
                    daemon=True,
                )
                send_thread.start()
            else:
                print("Cannot send empty message.")

        except Exception as e:
            print(f"An error occurred: {e}")


@app.route("/connect-peer", methods=["POST"])
def connect_peer_post(headers, body):
    print(f"[App] connect_peer_post with\nHeader: {headers}\nBody: {body}")
    global server_ip
    server_ip = body.get("server-ip", "")
    global server_port
    server_port = body.get("server-port", "")

    peer_ip = body.get("peer-ip", "")
    peer_port = body.get("peer-port", "")

    return {"auth": "true", "redirect": f"/chat?ip={peer_ip}&port={peer_port}"}


@app.route("/chat", methods=["GET"])
def chat_get(headers, body):
    print(f"[App] chat_get with\nHeader: {headers}\nBody: {body}")
    peer_ip = headers["query"]["ip"]
    peer_port = headers["query"]["port"]
    peer_address = f"{peer_ip}:{peer_port}"
    history = chat_history.get(peer_address, "No history")
    return {
        "auth": "true",
        "content": "chat.html",
        "placeholder": (
            peer_address,
            display_message(history),
            peer_ip,
            peer_port,
            server_ip,
            str(server_port),
        ),
    }


@app.route("/chat", methods=["POST"])
def chat_post(headers, body):
    print(f"[App] chat_post with\nHeader: {headers}\nBody: {body}")
    peer_ip = headers["query"]["ip"]
    peer_port = headers["query"]["port"]
    peer_address = f"{peer_ip}:{peer_port}"
    history = chat_history.get(peer_address, "")

    message_to_send = body["message"]
    send_queue.put((peer_ip, peer_port, message_to_send))

    return {"auth": "true", "redirect": f"/chat?ip={peer_ip}&port={peer_port}"}


@app.route("/broadcast0", methods=["POST"])
def broadcast0(headers, body):
    print(f"[App] broadcast0 with\nHeader: {headers}\nBody: {body}")
    global server_ip
    server_ip = body.get("server-ip", "")
    global server_port
    server_port = body.get("server-port", "")
    global peer_list
    addresses = body.get("peer-list", "")
    if addresses:
        peer_list = addresses.split("_")
    else:
        peer_list = []
    return {"auth": "true", "redirect": "/broadcast"}


@app.route("/broadcast", methods=["GET"])
def broadcast_get(headers, body):
    print(f"[App] broadcast_get with\nHeader: {headers}\nBody: {body}")
    return {
        "auth": "true",
        "content": "broadcast.html",
        "placeholder": (server_ip, str(server_port)),
    }


@app.route("/broadcast", methods=["POST"])
def broadcast_post(headers, body):
    print(f"[App] broadcast_post with\nHeader: {headers}\nBody: {body}")
    message_to_send = "[Broadcast] " + body["message"]
    for peer in peer_list:
        peer_ip, peer_port = peer.split(":")
        send_queue.put((peer_ip, peer_port, message_to_send))

    return {"auth": "true", "redirect": "/broadcast"}


@app.route("/connect-channel", methods=["POST"])
def connect_channel(headers, body):
    print(f"[App] connect_channel with\nHeader: {headers}\nBody: {body}")

    global server_ip
    server_ip = body.get("server-ip", "")
    global server_port
    server_port = body.get("server-port", "")
    channel_name = body.get("channel-name", "")
    addresses = body.get("peer-list", "")
    address_list = addresses.split("_")

    # if channel_name in channels:
    #     return {"auth": "true", "redirect": f"/channel?name={urllib.parse.quote(channel_name)}"}

    channels[channel_name] = address_list
    message_to_send = "___".join(
        ["[Channel]", channel_name, f"{my_listening_address} has joined"]
    )
    broadcast_message(address_list, message_to_send)
    return {
        "auth": "true",
        "redirect": f"/channel?name={urllib.parse.quote(channel_name)}",
    }


@app.route("/channel", methods=["GET"])
def channel_get(headers, body):
    print(f"[App] channel_get with\nHeader: {headers}\nBody: {body}")

    channel_name = headers["query"]["name"]
    history = channel_history.get(channel_name, "No history")

    return {
        "auth": "true",
        "content": "channel.html",
        "placeholder": (
            channel_name,
            display_message(history),
            channel_name,
            server_ip,
            str(server_port),
        ),
    }


@app.route("/channel", methods=["POST"])
def channel_post(headers, body):
    print(f"[App] channel_post with\nHeader: {headers}\nBody: {body}")

    channel_name = headers["query"]["name"]
    message = body["message"]
    address_list = channels[channel_name]
    message_to_send = "___".join(["[Channel]", channel_name, message])
    broadcast_message(address_list, message_to_send)

    return {
        "auth": "true",
        "redirect": f"/channel?name={urllib.parse.quote(channel_name)}",
    }


def broadcast_message(address_list, message):
    for peer in address_list:
        # if peer != my_listening_address:
        peer_ip, peer_port = peer.split(":")
        send_queue.put((peer_ip, peer_port, message))


def display_message(message_list):
    if isinstance(message_list, str):
        return message_list

    html_message = ""
    for sender, timestamp, message in message_list:
        html_message += f"<b>{sender}</b> (<em>{timestamp}</em>): {message}<br>"
    return html_message



# --- SỬA LẠI TRONG start_p2p.py ---

@app.route("/get-messages", methods=["GET"])
def get_chat_messages(headers, body):
    try:
        peer_ip = headers["query"]["ip"]
        peer_port = headers["query"]["port"]
        peer_address = f"{peer_ip}:{peer_port}"
        
        history = chat_history.get(peer_address, [])
        
        json_data = []
        if isinstance(history, list):
            for direction, timestamp, content in history:
                json_data.append({
                    "sender": "Me" if direction == "sent" else peer_address,
                    "timestamp": timestamp,
                    "message": content,
                    "type": direction
                })
        
        import json
        # --- KHẮC PHỤC LỖI Ở ĐÂY ---
        # Thay vì return json.dumps(json_data), ta bọc nó vào dictionary
        return {
            "auth": "true",
            "content": json.dumps(json_data),
            "type": "application/json" # Gợi ý cho framework set header (nếu hỗ trợ)
        }
    except Exception as e:
        print(f"Error getting messages: {e}")
        return {"auth": "true", "content": "[]"}

@app.route("/get-channel-messages", methods=["GET"])
def get_channel_messages(headers, body):
    try:
        channel_name = headers["query"]["name"]
        history = channel_history.get(channel_name, [])
        
        json_data = []
        if isinstance(history, list):
            for sender, timestamp, content in history:
                json_data.append({
                    "sender": sender,
                    "timestamp": timestamp,
                    "message": content,
                    "type": "channel"
                })
        
        import json
        # --- KHẮC PHỤC LỖI Ở ĐÂY ---
        return {
            "auth": "true",
            "content": json.dumps(json_data)
        }
    except Exception as e:
        print(f"Error getting channel messages: {e}")
        return {"auth": "true", "content": "[]"}



if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(
        prog="P2P Chat",
        description="Peer-to-peer chat application",
        epilog="P2P daemon",
    )
    parser.add_argument("--server-port", type=int, default=PORT)
    parser.add_argument("--chat-ip", default="127.0.0.1")
    parser.add_argument(
        "--chat-port",
        type=int,
        default=PORT + 1000,
        help="Port to listen for incoming peer messages",
    )

    args = parser.parse_args()
    server_ip = "127.0.0.1"
    server_port = args.server_port
    chat_ip = args.chat_ip
    chat_port = args.chat_port

    chat_thread = threading.Thread(target=run, args=(chat_ip, chat_port))
    chat_thread.start()

    # Prepare and launch the RESTful application
    app.prepare_address(server_ip, server_port)
    app.run()
