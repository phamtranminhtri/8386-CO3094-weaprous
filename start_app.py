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
start_app
~~~~~~~~~~~~~~~~~
"""

import json
import socket
import argparse
import os
import random
from urllib.parse import urlencode

from daemon.weaprous import WeApRous

PORT = 8000  # Default port

app = WeApRous()
accounts = dict()               # map: username -> hash password
session_to_account = dict()     # map: session id -> username
account_to_address = dict()     # map: username -> (peer ip, peer port, local port)
channels = dict()               # map: channel name -> ( peer address list, channel password )


@app.route('/login', methods=['POST'])
def login_post(headers, body):
    print(f"[App] login_post with\nHeader: {headers}\nBody: {body}")

    username, password = body["username"], body["password"]
    if (username == "admin" and password == "password") or (accounts.get(username, "") == hash(password)):
        session_id = str(random.randint(1, 1_000_000_000))
        session_to_account[session_id] = username
        return {"auth": "true", "redirect": "/", "session_id": session_id}
    
    return {"auth": "false"}


@app.route('/login', methods=['GET'])
def login_get(headers, body):
    print(f"[App] login_get with\nHeader: {headers}\nBody: {body}")
    return {"auth": "true", "content": "/login.html"}


@app.route('/register', methods=['POST'])
def register_post(headers, body):
    print(f"[App] register_post with\nHeader: {headers}\nBody: {body}")

    username, password = body["username"], body["password"]
    if username == "admin" or username in accounts:
        return {"auth": "false"}
    
    if username != "admin":
        accounts[username] = hash(password)
        
    session_id = str(random.randint(1, 1_000_000_000))
    session_to_account[session_id] = username

    return {"auth": "true", "redirect": "/", "session_id": session_id}


@app.route('/register', methods=['GET'])
def register_get(headers, body):
    print(f"[App] register_get with\nHeader: {headers}\nBody: {body}")
    return {"auth": "true", "content": "/register.html"}


@app.route('/logout', methods=['POST'])
def logout(headers, body):
    print(f"[App] logout with\nHeader: {headers}\nBody: {body}")
    
    cookie = headers.get("cookie-pair", None)
    username = get_username(headers)
    if cookie:
        session_id = cookie.get("session_id", "")
        session_to_account.pop(session_id, None)
    account_to_address.pop(username, None)
    return {"auth": "true", "redirect": "/login"}


@app.route('/', methods=['GET'])
def index(headers, body):
    print(f"[App] index with\nHeader: {headers}\nBody: {body}")

    if not authenticate(headers):
        return {"auth": "false"}
    
    username = get_username(headers)
    functions = ""
    user_ip, user_port, user_local_port = account_to_address.get(username, (None, None, None))
    if user_ip and user_port and user_local_port:
        address_noti_message = f"Your submitted chatting address is [ {user_ip}:{user_port} ]."
        functions = """
            <li><a href="/get-list">Get list of active peer address</a></li>
            <li><a href="/channel">View channels</a></li>
        """
    else:
        address_noti_message = "You need to submit a address (IP + port) before chatting."

    return {"auth": "true", "content": "index.html", "placeholder": (username, address_noti_message, functions)}


@app.route('/submit-info', methods=['POST'])
def submit_post(headers, body):
    print(f"[App] submit_post with\nHeader: {headers}\nBody: {body}")

    user_ip, user_port, user_local_port = body["ip"], body["port"], body["local-port"]
    
    if not validate_address(user_ip, user_port, user_local_port):
        return {"auth": "true", "redirect": "/submit-info"}

    if not authenticate(headers):
        return {"auth": "false"}
    
    username = get_username(headers)
    if not username:
        return {"auth": "false"}
    
    account_to_address[username] = (user_ip, int(user_port), int(user_local_port))
    return {"auth": "true", "redirect": "/"}


@app.route('/submit-info', methods=['GET'])
def submit_get(headers, body):
    print(f"[App] submit_get with\nHeader: {headers}\nBody: {body}")
    if authenticate(headers):
        return {"auth": "true", "content": "/submit-info.html"}
    return {"auth": "false"}


@app.route('/get-list', methods=['GET'])
def get_list(headers, body):
    print(f"[App] get_list with\nHeader: {headers}\nBody: {body}")
    if not authenticate(headers):
        return {"auth": "false"}
    
    html_list_string = ""
    address_list = []
    current_username = get_username(headers)

    if current_username not in account_to_address:
        html_list_string = "You need to submit a address (IP + port) before chatting."
        broadcast = ""
        return {"auth": "true", "content": "get-list.html", "placeholder": (html_list_string, broadcast)}


    _, _, current_user_local_port = account_to_address[current_username]
    for username, (user_ip, user_port, _) in account_to_address.items():
        html_list_item = f"""
            <li>
            <b>{username}</b>'s address: [ {user_ip}:{user_port} ]
        """
        if username != current_username:
            address_list.append(f"{user_ip}:{user_port}")
            html_list_item += f"""
                <form method="POST" action="http://127.0.0.1:{current_user_local_port}/connect-peer">
                    <input type="hidden" name="peer-ip" value="{user_ip}">
                    <input type="hidden" name="peer-port" value="{user_port}">
                    <input type="hidden" name="server-ip" value="{app.ip}">
                    <input type="hidden" name="server-port" value="{app.port}">
                    <input type="submit" value="Chat with {username}">
                </form>
            """
        html_list_item += "</li>"
        html_list_string += html_list_item

    addresses = "_".join(address_list)
    broadcast = f"""
                <form method="POST" action="http://127.0.0.1:{current_user_local_port}/broadcast0">
                    <input type="hidden" name="peer-list" value="{addresses}">
                    <input type="hidden" name="server-ip" value="{app.ip}">
                    <input type="hidden" name="server-port" value="{app.port}">
                    <input type="submit" value="Broadcast">
                </form>
            """

    return {"auth": "true", "content": "get-list.html", "placeholder": (html_list_string, broadcast)}


@app.route('/channel', methods=['GET'])
def channel_get(headers, body):
    print(f"[App] channel_get with\nHeader: {headers}\nBody: {body}")
    if not authenticate(headers):
        return {"auth": "false"}
    
    current_username = get_username(headers)
    joined_channel_html = ""
    available_channel_html = ""

    peer_ip, peer_port, local_port = account_to_address[current_username]
    peer_address = f"{peer_ip}:{peer_port}"
    for channel_name, (address_list, _) in channels.items():
        if peer_address in address_list:
            addresses = "_".join(address_list)
            # joined_channel_html += f"""
            #     <li>
            #     <b>{channel_name}</b>
            #     <form method="POST" action="http://127.0.0.1:{local_port}/connect-channel">
            #         <input type="hidden" name="peer-list" value="{addresses}">
            #         <input type="hidden" name="server-ip" value="{app.ip}">
            #         <input type="hidden" name="server-port" value="{app.port}">
            #         <input type="hidden" name="channel-name" value="{channel_name}">
            #         <input type="submit" value="Chat">
            #     </form>
            #     </li>
            # """
            joined_channel_html += f"""
                <li>
                <b>{channel_name}</b>
                <form method="POST" action="/connect-channel">
                    <input type="hidden" name="channel-name" value="{channel_name}">
                    <input type="submit" value="Chat">
                </form>
                </li>
            """

        else:
            available_channel_html += f"""
                <li>
                <b>{channel_name}</b>
                <form method="POST" action="/join-channel">
                    Channel password: <input name="channel-password" type="password"><br>
                    <input type="hidden" name="channel-name" value="{channel_name}">
                    <input type="submit" value="Join">
                </form>
                </li>
            """

    

    return {"auth": "true", "content": "channel-list.html", "placeholder": (joined_channel_html, available_channel_html)}


@app.route('/connect-channel', methods=['POST'])
def connect_channel(headers, body):
    print(f"[App] connect_channel with\nHeader: {headers}\nBody: {body}")
    if not authenticate(headers):
        return {"auth": "false"}
    
    channel_name = body.get("channel-name", "")
    
    if (not channel_name) or (channel_name not in channels):
        return {"auth": "true", "redirect": "/channel"}
    
    address_list, _ = channels[channel_name]
    addresses = "_".join(address_list)

    # 1. Represent your form data as a Python dictionary
    data = {
        'peer-list': addresses,
        'server-ip': app.ip,
        'server-port': app.port,
        'channel-name': channel_name
    }

    # # 2. Use urlencode to create the body string
    # raw_body = urlencode(data)

    # # 3. Print the result
    # print(raw_body)

    current_username = get_username(headers)
    _, _, local_port = account_to_address[current_username]
    
    return {"auth": "true", "temp_redirect": f"http://127.0.0.1:{local_port}/connect-channel", "temp_body": data}


@app.route('/create-channel', methods=['POST'])
def create_channel(headers, body):
    print(f"[App] create_channel with\nHeader: {headers}\nBody: {body}")
    if not authenticate(headers):
        return {"auth": "false"}
    
    channel_name = body.get("channel-name", "")
    channel_password = body.get("channel-password", "")
    if (not channel_name) or (channel_name in channels) or (not channel_password):
        return {"auth": "true", "redirect": "/channel"}
    
    username = get_username(headers)
    peer_ip, peer_port, _ = account_to_address[username]
    channels[channel_name] = ([f"{peer_ip}:{peer_port}"], hash(channel_password))
    return {"auth": "true", "redirect": "/channel"}


@app.route('/join-channel', methods=['POST'])
def join_channel(headers, body):
    print(f"[App] join_channel with\nHeader: {headers}\nBody: {body}")
    if not authenticate(headers):
        return {"auth": "false"}
    
    channel_name = body.get("channel-name", "")
    channel_password = body.get("channel-password", "")

    if (not channel_name) or (channel_name not in channels) or (not channel_password):
        return {"auth": "true", "redirect": "/channel"}
    
    address_list, password_hash = channels[channel_name]
    if hash(channel_password) != password_hash:
        return {"auth": "true", "redirect": "/channel"}

    username = get_username(headers)
    peer_ip, peer_port, _ = account_to_address[username]
    address_list.append(f"{peer_ip}:{peer_port}")

    return {"auth": "true", "redirect": "/channel"}


def authenticate(headers):
    cookie = headers.get("cookie-pair", None)
    if cookie:
        auth = cookie.get("auth", "")
        session_id = cookie.get("session_id", "")
        if auth == "true" and session_id in session_to_account:
            return True
    return False


def get_username(headers):
    cookie = headers.get("cookie-pair", None)
    if cookie:
        auth = cookie.get("auth", "")
        session_id = cookie.get("session_id", "")
        if auth == "true" and session_id in session_to_account:
            return session_to_account[session_id]
    return None


def validate_address(ip, port, local_port):
    parts = ip.split(".")

    if len(parts) != 4:
        return False
    
    try:
        parts = list(map(int, parts))
    except ValueError:
        return False
    
    for part in parts:
        if part < 0 or part > 255:
            return False
        
    try:
        port, local_port = int(port), int(local_port)
    except ValueError:
        return False

    if port < 0 or port > 65535 or local_port < 0 or local_port > 65535:
        return False
    
    return True


if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    # app.run()
    app.run_proxy()