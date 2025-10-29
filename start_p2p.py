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

from daemon.weaprous import WeApRous

PORT = 8386  # Default port

app = WeApRous()
accounts = dict()
session_to_account = dict()
account_to_address = dict()
server_ip = ""
server_port = ""


@app.route('/connect-peer', methods=['POST'])
def connect_peer_post(headers, body):
    print(f"[App] connect_peer_post with\nHeader: {headers}\nBody: {body}")
    global server_ip
    server_ip = body.get("server-ip", "")
    global server_port
    server_port = body.get("server-port", "")

    return {"auth": "true", "redirect": "/connect-peer"}
    


@app.route('/connect-peer', methods=['GET'])
def connect_peer_get(headers, body):
    print(f"[App] connect_peer_get with\nHeader: {headers}\nBody: {body}")

    return {"auth": "true", "content": "sample.html", "placeholder": (server_ip, server_port)}





if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='127.0.0.1')
    parser.add_argument('--server-port', type=int, default=PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()
    # app.run_proxy()