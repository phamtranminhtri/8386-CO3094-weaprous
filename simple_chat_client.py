#!/usr/bin/env python3
"""
Simple Chat System Test Client (No external dependencies)

This script demonstrates the hybrid chat system functionality using built-in libraries only:
1. Client-Server phase: Peer registration and discovery
2. P2P phase: Direct peer communication and broadcasting  
3. Channel management: Create, join channels, send messages

Usage:
    python3 simple_chat_client.py
"""

import socket
import json
import time
import threading
from datetime import datetime
import urllib.parse

class SimpleChatClient:
    """Simple test client for the hybrid chat system using only built-in libraries."""
    
    def __init__(self, server_host="localhost", server_port=9000, peer_id=None):
        self.server_host = server_host
        self.server_port = server_port
        self.peer_id = peer_id or f"peer_{int(time.time())}"
        self.auth_cookie = ""
        self.peer_cookie = ""
        
    def send_http_request(self, method, path, data=None, content_type="application/json"):
        """Send HTTP request to server."""
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.server_host, self.server_port))
            
            # Prepare body
            body = ""
            if data:
                if content_type == "application/json":
                    body = json.dumps(data)
                elif content_type == "application/x-www-form-urlencoded":
                    body = data
            
            # Prepare headers
            headers = [
                f"{method} {path} HTTP/1.1",
                f"Host: {self.server_host}:{self.server_port}",
                f"Content-Type: {content_type}",
                f"Content-Length: {len(body)}",
                "Connection: close"
            ]
            
            # Add cookies if available
            cookies = []
            if self.auth_cookie:
                cookies.append(f"auth={self.auth_cookie}")
            if self.peer_cookie:
                cookies.append(f"peer_id={self.peer_cookie}")
            
            if cookies:
                headers.append(f"Cookie: {'; '.join(cookies)}")
            
            # Send request
            request = "\\r\\n".join(headers) + "\\r\\n\\r\\n" + body
            sock.sendall(request.encode())
            
            # Receive response
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            sock.close()
            
            # Parse response
            response_str = response.decode()
            if "\\r\\n\\r\\n" in response_str:
                header_part, body_part = response_str.split("\\r\\n\\r\\n", 1)
            else:
                header_part = response_str
                body_part = ""
            
            # Extract status code
            status_line = header_part.split("\\r\\n")[0]
            status_code = int(status_line.split(" ")[1])
            
            # Extract Set-Cookie headers
            for line in header_part.split("\\r\\n"):
                if line.startswith("Set-Cookie:"):
                    cookie_value = line.split(":", 1)[1].strip()
                    if "auth=true" in cookie_value:
                        self.auth_cookie = "true"
                    elif "peer_id=" in cookie_value:
                        self.peer_cookie = cookie_value.split("peer_id=")[1].split(";")[0]
            
            # Parse JSON body if possible
            try:
                body_json = json.loads(body_part) if body_part.strip() else {}
            except:
                body_json = {"raw_body": body_part}
            
            return status_code, body_json
            
        except Exception as e:
            print(f"Request error: {e}")
            return 500, {"error": str(e)}
    
    def login(self, username="admin", password="password"):
        """Login to get authentication cookies."""
        print(f"=== Logging in as {username} ===")
        
        # Form data for login
        login_data = f"username={username}&password={password}"
        
        status_code, response = self.send_http_request(
            "POST", "/login", login_data, "application/x-www-form-urlencoded"
        )
        
        if status_code == 200:
            print("✓ Successfully logged in")
            return True
        else:
            print(f"✗ Login failed: {status_code}")
            print(f"  Response: {response}")
            return False
    
    def register_peer(self, peer_ip="127.0.0.1", peer_port=9100):
        """Register peer with the centralized server."""
        print(f"=== Registering Peer {self.peer_id} ===")
        
        registration_data = {
            "peer_id": self.peer_id,
            "ip": peer_ip, 
            "port": peer_port
        }
        
        status_code, response = self.send_http_request(
            "POST", "/submit-info/", registration_data
        )
        
        if status_code == 200:
            print(f"✓ Peer registered: {response.get('message', 'Success')}")
            return True
        else:
            print(f"✗ Registration failed: {status_code}")
            print(f"  Error: {response.get('message', 'Unknown error')}")
            return False
    
    def get_peer_list(self):
        """Get list of active peers from server."""
        print("=== Getting Peer List ===")
        
        status_code, response = self.send_http_request("GET", "/connect-peer/")
        
        if status_code == 200:
            peers = response.get('peers', {})
            print(f"✓ Found {len(peers)} active peers:")
            for peer_id, peer_info in peers.items():
                print(f"  - {peer_id}: {peer_info['ip']}:{peer_info['port']}")
            return peers
        else:
            print(f"✗ Failed to get peer list: {status_code}")
            return {}
    
    def create_channel(self, channel_name):
        """Create a new chat channel."""
        print(f"=== Creating Channel '{channel_name}' ===")
        
        channel_data = {
            "action": "create",
            "channel_name": channel_name
        }
        
        status_code, response = self.send_http_request("POST", "/add-list/", channel_data)
        
        if status_code == 200:
            print(f"✓ Channel created: {response.get('message', 'Success')}")
            return True
        else:
            print(f"✗ Channel creation failed: {status_code}")
            print(f"  Error: {response.get('message', 'Unknown error')}")
            return False
    
    def join_channel(self, channel_name):
        """Join an existing channel."""
        print(f"=== Joining Channel '{channel_name}' ===")
        
        join_data = {
            "action": "join",
            "channel_name": channel_name
        }
        
        status_code, response = self.send_http_request("POST", "/add-list/", join_data)
        
        if status_code == 200:
            print(f"✓ Joined channel: {response.get('message', 'Success')}")
            return True
        else:
            print(f"✗ Failed to join channel: {status_code}")
            print(f"  Error: {response.get('message', 'Unknown error')}")
            return False
    
    def get_channels(self):
        """Get list of available channels."""
        print("=== Getting Channel List ===")
        
        status_code, response = self.send_http_request("GET", "/get-list/")
        
        if status_code == 200:
            channels = response.get('channels', {})
            print(f"✓ Found {len(channels)} channels:")
            for channel_name, channel_info in channels.items():
                membership = "✓" if channel_info.get('is_member') else "✗"
                print(f"  {membership} {channel_name}: {channel_info['peer_count']} members")
            return channels
        else:
            print(f"✗ Failed to get channels: {status_code}")
            return {}
    
    def send_message(self, channel, message):
        """Send message to a channel via P2P."""
        print(f"=== Sending Message to '{channel}' ===")
        
        message_data = {
            "channel": channel,
            "message": message
        }
        
        status_code, response = self.send_http_request("POST", "/send-peer/", message_data)
        
        if status_code == 200:
            print(f"✓ Message sent: {response.get('message', 'Success')}")
            return True
        else:
            print(f"✗ Failed to send message: {status_code}")
            print(f"  Error: {response.get('message', 'Unknown error')}")
            return False
    
    def broadcast_message(self, message):
        """Broadcast message to all connected peers."""
        print("=== Broadcasting Message ===")
        
        broadcast_data = {
            "message": message
        }
        
        status_code, response = self.send_http_request("POST", "/broadcast-peer/", broadcast_data)
        
        if status_code == 200:
            print(f"✓ Broadcast sent: {response.get('message', 'Success')}")
            return True
        else:
            print(f"✗ Broadcast failed: {status_code}")
            print(f"  Error: {response.get('message', 'Unknown error')}")
            return False
    
    def get_messages(self):
        """Get messages from all channels."""
        print("=== Getting Messages ===")
        
        status_code, response = self.send_http_request("GET", "/send-peer/")
        
        if status_code == 200:
            channels = response.get('channels', {})
            print(f"✓ Messages retrieved from {len(channels)} channels:")
            
            for channel_name, messages in channels.items():
                print(f"\\n--- {channel_name} ({len(messages)} messages) ---")
                for msg in messages[-3:]:  # Show last 3 messages
                    timestamp = msg.get('timestamp', '')[:19]  # Remove microseconds
                    sender = msg.get('sender', 'unknown')
                    content = msg.get('content', '')
                    msg_type = msg.get('type', 'chat')
                    print(f"  [{timestamp}] {sender} ({msg_type}): {content}")
            
            return channels
        else:
            print(f"✗ Failed to get messages: {status_code}")
            return {}

def run_simple_demo():
    """Run a simple demo of the chat system."""
    print("Simple Hybrid Chat System Demo")
    print("==============================")
    print("Make sure the backend server is running:")
    print("  python3 start_backend.py --server-port 9000")
    print()
    
    # Create client
    client = SimpleChatClient(peer_id="demo_user")
    
    print("🚀 Starting Simple Chat Demo")
    
    # Step 1: Authentication
    print("\\n📋 Step 1: Authentication")
    if not client.login():
        print("❌ Login failed")
        return
    
    # Step 2: Peer Registration
    print("\\n🌐 Step 2: Peer Registration")
    if not client.register_peer(peer_port=9100):
        print("❌ Registration failed")
        return
    
    time.sleep(1)
    
    # Step 3: Create and manage channels
    print("\\n💬 Step 3: Channel Management")
    client.create_channel("general")
    time.sleep(1)
    client.create_channel("testing")
    time.sleep(1)
    
    client.get_channels()
    
    # Step 4: Send some messages
    print("\\n📨 Step 4: Message Testing")
    client.send_message("general", "Hello from the demo client!")
    time.sleep(1)
    
    client.send_message("testing", "This is a test message.")
    time.sleep(1)
    
    client.broadcast_message("Broadcasting to everyone!")
    time.sleep(1)
    
    # Step 5: Retrieve messages
    print("\\n📬 Step 5: Message Retrieval")
    client.get_messages()
    
    # Step 6: Peer discovery
    print("\\n🔍 Step 6: Peer Discovery")
    client.get_peer_list()
    
    print("\\n✅ Simple demo completed!")
    print("\\n🎯 What was demonstrated:")
    print("- ✓ POST /login authentication with Set-Cookie: auth=true")
    print("- ✓ Peer registration via /submit-info/")
    print("- ✓ Channel creation via /add-list/")
    print("- ✓ Message sending via /send-peer/")
    print("- ✓ Broadcasting via /broadcast-peer/")
    print("- ✓ Message retrieval and peer discovery")

def test_login_only():
    """Test just the login functionality."""
    print("Testing POST /login with Set-Cookie Implementation")
    print("=================================================")
    
    client = SimpleChatClient()
    
    print("1. Testing valid credentials (admin/password):")
    if client.login("admin", "password"):
        print(f"   ✓ Auth cookie set: {client.auth_cookie}")
    
    print("\\n2. Testing invalid credentials (admin/wrong):")
    client.auth_cookie = ""  # Reset
    client.login("admin", "wrong")
    
    print("\\n3. Testing access to protected resource:")
    client.auth_cookie = "true"  # Set manually
    status_code, response = client.send_http_request("GET", "/")
    print(f"   Status: {status_code}")
    if status_code == 200:
        print("   ✓ Successfully accessed protected resource with auth cookie")
    else:
        print("   ✗ Access denied or other error")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--login-only":
        test_login_only()
    else:
        run_simple_demo()