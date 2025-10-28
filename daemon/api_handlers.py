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
daemon.api_handlers
~~~~~~~~~~~~~~~~~

This module provides API handlers for various endpoints including:
- login API
- submit-info API  
- add-list API
- get-list API
- connect-peer API
- broadcast-peer API
- send-peer API
"""

import json
import threading
from datetime import datetime
from .chat_system import chat_server, active_peers, ChatPeer

# Global storage for demonstration (in production, use proper database)
user_lists = {}
peer_connections = {}
peer_messages = []
storage_lock = threading.Lock()

class APIHandlers:
    """API handlers for various endpoints."""
    
    @staticmethod
    def handle_api_request(method, path, headers, body, cookies):
        """
        Route API requests to appropriate handlers.
        
        :param method: HTTP method
        :param path: Request path
        :param headers: Request headers dict
        :param body: Request body
        :param cookies: Request cookies dict
        :return: (status_code, headers_dict, response_body)
        """
        print("[API] BUILDING: Handling {} request to {}".format(method, path))
        
        # Check authentication for protected endpoints
        auth_required_paths = ['/submit-info/', '/add-list/', '/get-list/', 
                             '/connect-peer/', '/broadcast-peer/', '/send-peer/']
        
        if any(path.startswith(api_path) for api_path in auth_required_paths):
            if not APIHandlers.check_authentication(cookies):
                return APIHandlers.unauthorized_response()
        
        # Route to appropriate handler
        if path == '/login/' or path.startswith('/login'):
            return APIHandlers.login_api(method, body)
        elif path == '/submit-info/' or path.startswith('/submit-info'):
            return APIHandlers.submit_info_api(method, body, cookies)
        elif path == '/add-list/' or path.startswith('/add-list'):
            return APIHandlers.add_list_api(method, body, cookies)
        elif path == '/get-list/' or path.startswith('/get-list'):
            return APIHandlers.get_list_api(method, cookies)
        elif path == '/connect-peer/' or path.startswith('/connect-peer'):
            return APIHandlers.connect_peer_api(method, body, cookies)
        elif path == '/broadcast-peer/' or path.startswith('/broadcast-peer'):
            return APIHandlers.broadcast_peer_api(method, body, cookies)
        elif path == '/send-peer/' or path.startswith('/send-peer'):
            return APIHandlers.send_peer_api(method, body, cookies)
        else:
            return APIHandlers.not_found_response()
        if path.startswith('/login/'):
            return APIHandlers.login_api(method, body)
        elif path.startswith('/submit-info/'):
            return APIHandlers.submit_info_api(method, body, cookies)
        elif path.startswith('/add-list/'):
            return APIHandlers.add_list_api(method, body, cookies)
        elif path.startswith('/get-list/'):
            return APIHandlers.get_list_api(method, cookies)
        elif path.startswith('/connect-peer/'):
            return APIHandlers.connect_peer_api(method, body, cookies)
        elif path.startswith('/broadcast-peer/'):
            return APIHandlers.broadcast_peer_api(method, body, cookies)
        elif path.startswith('/send-peer/'):
            return APIHandlers.send_peer_api(method, body, cookies)
        else:
            return APIHandlers.not_found_response()
    
    @staticmethod
    def check_authentication(cookies):
        """Check if user is authenticated."""
        if cookies and cookies.get('auth') == 'true':
            return True
        return False
    
    @staticmethod
    def login_api(method, body):
        """Handle login API endpoint."""
        if method != 'POST':
            return 405, {}, {"error": "Method not allowed"}
        
        try:
            # Parse JSON body
            data = json.loads(body) if body else {}
            username = data.get('username', '')
            password = data.get('password', '')
            
            print("[API] BUILDING: Login attempt - username: {}".format(username))
            
            if username == 'admin' and password == 'password':
                response_data = {
                    "status": "success",
                    "message": "Login successful",
                    "user": username,
                    "timestamp": datetime.now().isoformat()
                }
                headers = {"Set-Cookie": "auth=true; Path=/"}
                return 200, headers, response_data
            else:
                return 401, {}, {"status": "error", "message": "Invalid credentials"}
                
        except json.JSONDecodeError:
            return 400, {}, {"error": "Invalid JSON"}
    
    @staticmethod
    def submit_info_api(method, body, cookies):
        """Handle submit-info API endpoint - Peer Registration."""
        if method != 'POST':
            return 405, {}, {"error": "Method not allowed"}
        
        try:
            data = json.loads(body) if body else {}
            peer_id = data.get('peer_id', '')
            peer_ip = data.get('ip', '')
            peer_port = data.get('port', 0)
            
            if not peer_id or not peer_ip or not peer_port:
                return 400, {}, {"error": "peer_id, ip and port required for registration"}
            
            # Register peer with chat server
            result = chat_server.register_peer(peer_id, peer_ip, peer_port)
            
            # Create peer instance for P2P communication
            if peer_id not in active_peers:
                peer_instance = ChatPeer(peer_id, peer_port)
                active_peers[peer_id] = peer_instance
                
                # Start listening for P2P connections in background
                listener_thread = threading.Thread(target=peer_instance.start_listening)
                listener_thread.daemon = True
                listener_thread.start()
            
            print("[API] BUILDING: Registered peer {} at {}:{}".format(peer_id, peer_ip, peer_port))
            
            # Set peer_id cookie for future requests
            headers = {"Set-Cookie": f"peer_id={peer_id}; Path=/"}
            
            return 200, headers, result
            
        except json.JSONDecodeError:
            return 400, {}, {"error": "Invalid JSON"}
    
    @staticmethod
    def add_list_api(method, body, cookies):
        """Handle add-list API endpoint - Channel Management."""
        if method == 'POST':
            # Create or join channel
            try:
                data = json.loads(body) if body else {}
                action = data.get('action', 'create')  # 'create' or 'join'
                channel_name = data.get('channel_name', '')
                peer_id = cookies.get('peer_id', 'anonymous')
                
                if not channel_name:
                    return 400, {}, {"error": "channel_name required"}
                
                if action == 'create':
                    result = chat_server.create_channel(channel_name, peer_id)
                elif action == 'join':
                    result = chat_server.join_channel(channel_name, peer_id)
                else:
                    return 400, {}, {"error": "Invalid action. Use 'create' or 'join'"}
                
                print("[API] BUILDING: Channel {} '{}' by {}".format(action, channel_name, peer_id))
                
                return 200, {}, result
                
            except json.JSONDecodeError:
                return 400, {}, {"error": "Invalid JSON"}
        else:
            return 405, {}, {"error": "Method not allowed"}
    
    @staticmethod
    def get_list_api(method, cookies):
        """Handle get-list API endpoint - Get Channels or Messages."""
        if method != 'GET':
            return 405, {}, {"error": "Method not allowed"}
        
        peer_id = cookies.get('peer_id', 'anonymous')
        
        # Get available channels
        result = chat_server.get_channel_list(peer_id)
        
        print("[API] BUILDING: Retrieved channel list for {}".format(peer_id))
        
        return 200, {}, result
    
    @staticmethod
    def connect_peer_api(method, body, cookies):
        """Handle connect-peer API endpoint - P2P connection establishment."""
        if method == 'POST':
            # Connect to another peer
            try:
                data = json.loads(body) if body else {}
                peer_id = data.get('peer_id', '')
                peer_address = data.get('address', '')
                peer_port = data.get('port', 0)
                current_peer_id = cookies.get('peer_id', 'anonymous')
                
                if not peer_id or not peer_address or not peer_port:
                    return 400, {}, {"error": "peer_id, address and port required"}
                
                # Get or create peer instance
                if current_peer_id not in active_peers:
                    return 400, {}, {"error": "Peer not registered. Please register first."}
                
                peer_instance = active_peers[current_peer_id]
                result = peer_instance.connect_to_peer(peer_address, peer_port, peer_id)
                
                print("[API] BUILDING: P2P connection attempt to {}:{}".format(peer_address, peer_port))
                
                return 200, {}, result
                
            except json.JSONDecodeError:
                return 400, {}, {"error": "Invalid JSON"}
        
        elif method == 'GET':
            # Get peer list from server
            current_peer_id = cookies.get('peer_id', None)
            result = chat_server.get_peer_list(current_peer_id)
            return 200, {}, result
        
        else:
            return 405, {}, {"error": "Method not allowed"}
    
    @staticmethod
    def broadcast_peer_api(method, body, cookies):
        """Handle broadcast-peer API endpoint - P2P Broadcasting."""
        if method != 'POST':
            return 405, {}, {"error": "Method not allowed"}
        
        try:
            data = json.loads(body) if body else {}
            message = data.get('message', '')
            peer_id = cookies.get('peer_id', 'anonymous')
            
            if not message:
                return 400, {}, {"error": "Message is required"}
            
            # Get peer instance
            if peer_id not in active_peers:
                return 400, {}, {"error": "Peer not registered"}
            
            peer_instance = active_peers[peer_id]
            result = peer_instance.broadcast_message(message)
            
            print("[API] BUILDING: Broadcasting message from {}".format(peer_id))
            
            return 200, {}, result
            
        except json.JSONDecodeError:
            return 400, {}, {"error": "Invalid JSON"}
    
    @staticmethod
    def send_peer_api(method, body, cookies):
        """Handle send-peer API endpoint - Send message to channel or get messages."""
        if method == 'POST':
            # Send message to channel
            try:
                data = json.loads(body) if body else {}
                message = data.get('message', '')
                channel = data.get('channel', 'general')
                peer_id = cookies.get('peer_id', 'anonymous')
                
                if not message:
                    return 400, {}, {"error": "Message is required"}
                
                # Get peer instance
                if peer_id not in active_peers:
                    return 400, {}, {"error": "Peer not registered"}
                
                peer_instance = active_peers[peer_id]
                result = peer_instance.send_message_to_channel(channel, message)
                
                print("[API] BUILDING: Sent message to channel '{}' from {}".format(channel, peer_id))
                
                return 200, {}, result
                
            except json.JSONDecodeError:
                return 400, {}, {"error": "Invalid JSON"}
        
        elif method == 'GET':
            # Get messages from channel
            import urllib.parse
            # For GET requests, we'd need to parse query parameters from the path
            # Simplified: return recent messages from all channels for this peer
            peer_id = cookies.get('peer_id', 'anonymous')
            
            if peer_id in active_peers:
                peer_instance = active_peers[peer_id]
                all_messages = {}
                
                for channel_name in peer_instance.channels.keys():
                    channel_messages = peer_instance.get_messages(channel_name)
                    if channel_messages.get('status') == 'success':
                        all_messages[channel_name] = channel_messages['messages']
                
                return 200, {}, {
                    "status": "success",
                    "peer_id": peer_id,
                    "channels": all_messages
                }
            else:
                return 400, {}, {"error": "Peer not registered"}
        
        else:
            return 405, {}, {"error": "Method not allowed"}
    
    @staticmethod
    def unauthorized_response():
        """Return 401 Unauthorized response."""
        return 401, {}, {
            "status": "error",
            "message": "Authentication required",
            "code": 401
        }
    
    @staticmethod
    def not_found_response():
        """Return 404 Not Found response."""
        return 404, {}, {
            "status": "error", 
            "message": "API endpoint not found",
            "code": 404
        }