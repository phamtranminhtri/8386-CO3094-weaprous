#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.proxy
~~~~~~~~~~~~~~~~~

This module implements a simple proxy server using Python's socket and threading libraries.
It routes incoming HTTP requests to backend services based on hostname mappings and returns
the corresponding responses to clients.

Requirement:
-----------------
- socket: provides socket networking interface.
- threading: enables concurrent client handling via threads.
- response: customized :class: `Response <Response>` utilities.
- httpadapter: :class: `HttpAdapter <HttpAdapter >` adapter for HTTP request processing.
- dictionary: :class: `CaseInsensitiveDict <CaseInsensitiveDict>` for managing headers and cookies.

"""
import socket
import threading
from .response import *
from .httpadapter import HttpAdapter
from .dictionary import CaseInsensitiveDict

#: A dictionary mapping hostnames to backend IP and port tuples.
#: Used to determine routing targets for incoming requests.
PROXY_PASS = {
    "localhost:8080": ('127.0.0.1', 9000),
    "127.0.0.1:8080": ('127.0.0.1', 9000),
    "192.168.1.100:8080": ('192.168.1.100', 9000),  # Replace with your actual local IP
    "192.168.1.101:8080": ('192.168.1.101', 9000),  # Replace with device 2 IP
    "app1.local": ('127.0.0.1', 9001),
    "app2.local": ('127.0.0.1', 9002),
}

ROUND_ROBIN_COUNTERS = {}######
ROUTING_LOCK = threading.Lock()#######

def forward_request(host, port, request):
    """
    Forwards an HTTP request to a backend server and retrieves the response.

    :params host (str): IP address of the backend server.
    :params port (int): port number of the backend server.
    :params request (str): incoming HTTP request.

    :rtype bytes: Raw HTTP response from the backend server. If the connection
                  fails, returns a 404 Not Found response.
    """

    backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        print("[Proxy] BUILDING: Connecting to backend {}:{}".format(host, port))
        backend.connect((host, port))
        print("[Proxy] BUILDING: Forwarding request ({} bytes)".format(len(request)))
        # backend.sendall(request.encode())
        backend.sendall(request)
        ##########
        print("[Proxy] BUILDING: Reading response from backend")
        response = b""
        while True:
            chunk = backend.recv(4096)
            if not chunk:
                break
            response += chunk
        print("[Proxy] BUILDING: Received complete response ({} bytes)".format(len(response)))
        return response
    except socket.error as e:
      print("Socket error: {}".format(e))
      return (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode('utf-8')


def resolve_routing_policy(hostname, routes):
    """
    Handles an routing policy to return the matching proxy_pass.
    It determines the target backend to forward the request to.

    :params host (str): IP address of the request target server.
    :params port (int): port number of the request target server.
    :params routes (dict): dictionary mapping hostnames and location.
    """

    print("[Proxy] BUILDING: Resolving routing policy for hostname: {}".format(hostname))
    proxy_map, policy = routes.get(hostname,('127.0.0.1:9000','round-robin'))
    print("[Proxy] BUILDING: Found proxy_map={}, policy={}".format(proxy_map, policy))

    proxy_host = ''
    proxy_port = '9000'
    if isinstance(proxy_map, list):
        if len(proxy_map) == 0:
            print("[Proxy] BUILDING: Empty resolved routing of hostname {}".format(hostname))
            print("[Proxy] BUILDING: Empty proxy_map result")
            # TODO: implement the error handling for non mapped host
            #       the policy is design by team, but it can be 
            #       basic default host in your self-defined system
            # IMPLEMENTED: Use a default host for invalid connections
            print("[Proxy] BUILDING: Using default fallback host")
            proxy_host = '127.0.0.1'
            proxy_port = '9000'
        elif len(proxy_map) == 1:
            print("[Proxy] BUILDING: Single backend found, using direct mapping")
            proxy_host, proxy_port = proxy_map[0].split(":", 1)  # Fixed split parameter
        #elif: # apply the policy handling 
        #   proxy_map
        #   policy
        elif policy == 'round-robin':
            print("[Proxy] BUILDING: Applying round-robin load balancing")
            with ROUTING_LOCK: # Khóa lại để tránh race condition
                # Lấy index hiện tại, nếu chưa có thì là 0
                current_index = ROUND_ROBIN_COUNTERS.get(hostname, 0)
                
                # Chọn backend từ danh sách
                chosen_backend = proxy_map[current_index]
                
                # Cập nhật index cho lần sau (quay vòng)
                next_index = (current_index + 1) % len(proxy_map)
                ROUND_ROBIN_COUNTERS[hostname] = next_index
            
            print("[Proxy] BUILDING: Round-robin for {}: selected backend {}".format(hostname, chosen_backend))
            proxy_host, proxy_port = chosen_backend.split(":", 1)  # Fixed split parameter
        else:
            # IMPLEMENTED: Default fallback for unhandled policies
            print("[Proxy] BUILDING: Using default backend for unhandled policy")
            proxy_host = '127.0.0.1'
            proxy_port = '9000'
    else:
        print("[Proxy] BUILDING: Single backend route for hostname {}".format(hostname))
        proxy_host, proxy_port = proxy_map.split(":", 1)  # Fixed split parameter

    print("[Proxy] BUILDING: Resolved to {}:{}".format(proxy_host, proxy_port))
    return proxy_host, proxy_port

def handle_client(ip, port, conn, addr, routes):
    """
    Handles an individual client connection by parsing the request,
    determining the target backend, and forwarding the request.

    The handler extracts the Host header from the request to
    matches the hostname against known routes. In the matching
    condition,it forwards the request to the appropriate backend.

    The handler sends the backend response back to the client or
    returns 404 if the hostname is unreachable or is not recognized.

    :params ip (str): IP address of the proxy server.
    :params port (int): port number of the proxy server.
    :params conn (socket.socket): client connection socket.
    :params addr (tuple): client address (IP, port).
    :params routes (dict): dictionary mapping hostnames and location.
    """

    # request = conn.recv(1024).decode()

    # # Extract hostname
    # for line in request.splitlines():
    #     if line.lower().startswith('host:'):
    #         hostname = line.split(':', 1)[1].strip()
    
    
    request_data = b""
    conn.settimeout(1.0)  # Đặt timeout 1 giây để tránh kẹt nếu client giữ kết nối
    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            request_data += chunk
    except socket.timeout:
        pass  # Coi như đã nhận xong

    # Nếu không nhận được gì, đóng kết nối
    if not request_data:
        print("[Proxy] Empty request from {}".format(addr))
        conn.close()
        return

    # Giải mã string chỉ để đọc header (dùng 'ignore' để tránh lỗi utf-8)
    request_string = request_data.decode('utf-8', errors='ignore')

    # Extract hostname
    hostname = "" # Khởi tạo
    for line in request_string.splitlines():
        if line.lower().startswith('host:'):
            hostname = line.split(':', 1)[1].strip()
            break # Tìm thấy rồi thì dừng

    # Nếu không tìm thấy header 'Host' -> Lỗi 400 Bad Request
    if not hostname:
        print("[Proxy] No Host header from {}".format(addr))
        response = (
            "HTTP/1.1 400 Bad Request\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 15\r\n"
            "Connection: close\r\n"
            "\r\n"
            "400 Bad Request"
        ).encode('utf-8')
        conn.sendall(response)
        conn.close()
        return
    # ##########
    

    print("[Proxy] {} at Host: {}".format(addr, hostname))

    # Resolve the matching destination in routes and need conver port
    # to integer value
    resolved_host, resolved_port = resolve_routing_policy(hostname, routes)
    try:
        resolved_port = int(resolved_port)
    except ValueError:
        print("Not a valid integer")

    if resolved_host:
        print("[Proxy] Host name {} is forwarded to {}:{}".format(hostname,resolved_host, resolved_port))
        response = forward_request(resolved_host, resolved_port, request_data)        
    else:
        response = (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode('utf-8')
    conn.sendall(response)
    conn.close()

def run_proxy(ip, port, routes):
    """
    Starts the proxy server and listens for incoming connections. 

    The process dinds the proxy server to the specified IP and port.
    In each incomping connection, it accepts the connections and
    spawns a new thread for each client using `handle_client`.
 

    :params ip (str): IP address to bind the proxy server.
    :params port (int): port number to listen on.
    :params routes (dict): dictionary mapping hostnames and location.

    """

    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        proxy.bind((ip, port))
        proxy.listen(50)
        print("[Proxy] Listening on IP {} port {}".format(ip,port))
        while True:
            conn, addr = proxy.accept()
            #
            #  TODO: implement the step of the client incomping connection
            #        using multi-thread programming with the
            #        provided handle_client routine
            #
            client_thread = threading.Thread(target=handle_client, args=(ip,port,conn, addr, routes))
            client_thread.daemon = True 
            client_thread.start()
            # 
            # 
            # 

    except socket.error as e:
      print("Socket error: {}".format(e))

def create_proxy(ip, port, routes):
    """
    Entry point for launching the proxy server.

    :params ip (str): IP address to bind the proxy server.
    :params port (int): port number to listen on.
    :params routes (dict): dictionary mapping hostnames and location.
    """

    run_proxy(ip, port, routes)
