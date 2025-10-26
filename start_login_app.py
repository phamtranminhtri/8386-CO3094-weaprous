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

from daemon.weaprous import WeApRous

PORT = 8000  # Default port

app = WeApRous()

@app.route('/login', methods=['POST'])
def login_post(headers, body):
    print(f"[App] login_post with\nHeader: {headers}\nBody: {body}")

    if body["username"] == "admin" and body["password"] == "password":
        return {"auth": "true", "redirect": "/"}
    
    return {"auth": "false"}

@app.route('/login', methods=['GET'])
def login_get(headers, body):
    print(f"[App] login_get with\nHeader: {headers}\nBody: {body}")
    return {"auth": "true", "content": "/login.html"}

@app.route('/', methods=['GET'])
def index(headers, body):
    print(f"[App] index with\nHeader: {headers}\nBody: {body}")

    cookie = headers.get("cookie-pair", None)
    if cookie:
        auth = cookie.get("auth", "")
        if auth == "true":
            return {"auth": "true", "content": "/index.html"}
    return {"auth": "false"}

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