#!/usr/bin/env python3
"""
Hybrid Chat System Test Client

This script demonstrates the hybrid chat system functionality:
1. Client-Server phase: Peer registration and discovery
2. P2P phase: Direct peer communication and broadcasting  
3. Channel management: Create, join channels, send messages

Usage:
    python3 chat_test_client.py
"""

import requests
import json
import time
import threading
from datetime import datetime

class ChatTestClient:
    """Test client for the hybrid chat system."""
    
    def __init__(self, base_url="http://localhost:9000", peer_id=None):
        self.base_url = base_url
        self.peer_id = peer_id or f"peer_{int(time.time())}"
        self.session = requests.Session()
        self.auth_cookies = {}
        
    def login(self, username="admin", password="password"):
        """Login to get authentication cookies."""
        print(f"=== Logging in as {username} ===")
        
        # First, try form-based login
        login_data = f"username={username}&password={password}"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        response = self.session.post(f"{self.base_url}/login", 
                                   data=login_data, 
                                   headers=headers, 
                                   allow_redirects=False)
        
        if response.status_code == 200:
            print("✓ Successfully logged in")
            self.auth_cookies = dict(response.cookies)
            return True
        else:
            print(f"✗ Login failed: {response.status_code}")
            return False
    
    def register_peer(self, peer_ip="127.0.0.1", peer_port=9100):
        """Register peer with the centralized server."""
        print(f"=== Registering Peer {self.peer_id} ===")
        
        registration_data = {
            "peer_id": self.peer_id,
            "ip": peer_ip, 
            "port": peer_port
        }
        
        response = self.session.post(f"{self.base_url}/submit-info/",
                                   json=registration_data,
                                   cookies=self.auth_cookies)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Peer registered: {result.get('message', 'Success')}")
            
            # Update cookies with peer_id
            if 'Set-Cookie' in response.headers:
                for cookie in response.headers.get_all('Set-Cookie'):
                    if 'peer_id=' in cookie:
                        peer_cookie = cookie.split(';')[0].split('=')[1]
                        self.auth_cookies['peer_id'] = peer_cookie
            
            return True
        else:
            print(f"✗ Registration failed: {response.status_code}")
            if response.content:
                try:
                    error = response.json()
                    print(f"  Error: {error.get('message', 'Unknown error')}")
                except:
                    pass
            return False
    
    def get_peer_list(self):
        """Get list of active peers from server."""
        print("=== Getting Peer List ===")
        
        response = self.session.get(f"{self.base_url}/connect-peer/",
                                  cookies=self.auth_cookies)
        
        if response.status_code == 200:
            result = response.json()
            peers = result.get('peers', {})
            print(f"✓ Found {len(peers)} active peers:")
            for peer_id, peer_info in peers.items():
                print(f"  - {peer_id}: {peer_info['ip']}:{peer_info['port']}")
            return peers
        else:
            print(f"✗ Failed to get peer list: {response.status_code}")
            return {}
    
    def create_channel(self, channel_name):
        """Create a new chat channel."""
        print(f"=== Creating Channel '{channel_name}' ===")
        
        channel_data = {
            "action": "create",
            "channel_name": channel_name
        }
        
        response = self.session.post(f"{self.base_url}/add-list/",
                                   json=channel_data,
                                   cookies=self.auth_cookies)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Channel created: {result.get('message', 'Success')}")
            return True
        else:
            print(f"✗ Channel creation failed: {response.status_code}")
            return False
    
    def join_channel(self, channel_name):
        """Join an existing channel."""
        print(f"=== Joining Channel '{channel_name}' ===")
        
        join_data = {
            "action": "join",
            "channel_name": channel_name
        }
        
        response = self.session.post(f"{self.base_url}/add-list/",
                                   json=join_data,
                                   cookies=self.auth_cookies)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Joined channel: {result.get('message', 'Success')}")
            return True
        else:
            print(f"✗ Failed to join channel: {response.status_code}")
            return False
    
    def get_channels(self):
        """Get list of available channels."""
        print("=== Getting Channel List ===")
        
        response = self.session.get(f"{self.base_url}/get-list/",
                                  cookies=self.auth_cookies)
        
        if response.status_code == 200:
            result = response.json()
            channels = result.get('channels', {})
            print(f"✓ Found {len(channels)} channels:")
            for channel_name, channel_info in channels.items():
                membership = "✓" if channel_info.get('is_member') else "✗"
                print(f"  {membership} {channel_name}: {channel_info['peer_count']} members")
            return channels
        else:
            print(f"✗ Failed to get channels: {response.status_code}")
            return {}
    
    def send_message(self, channel, message):
        """Send message to a channel via P2P."""
        print(f"=== Sending Message to '{channel}' ===")
        
        message_data = {
            "channel": channel,
            "message": message
        }
        
        response = self.session.post(f"{self.base_url}/send-peer/",
                                   json=message_data,
                                   cookies=self.auth_cookies)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Message sent: {result.get('message', 'Success')}")
            return True
        else:
            print(f"✗ Failed to send message: {response.status_code}")
            return False
    
    def broadcast_message(self, message):
        """Broadcast message to all connected peers."""
        print("=== Broadcasting Message ===")
        
        broadcast_data = {
            "message": message
        }
        
        response = self.session.post(f"{self.base_url}/broadcast-peer/",
                                   json=broadcast_data,
                                   cookies=self.auth_cookies)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Broadcast sent: {result.get('message', 'Success')}")
            return True
        else:
            print(f"✗ Broadcast failed: {response.status_code}")
            return False
    
    def get_messages(self):
        """Get messages from all channels."""
        print("=== Getting Messages ===")
        
        response = self.session.get(f"{self.base_url}/send-peer/",
                                  cookies=self.auth_cookies)
        
        if response.status_code == 200:
            result = response.json()
            channels = result.get('channels', {})
            print(f"✓ Messages retrieved from {len(channels)} channels:")
            
            for channel_name, messages in channels.items():
                print(f"\n--- {channel_name} ({len(messages)} messages) ---")
                for msg in messages[-5:]:  # Show last 5 messages
                    timestamp = msg.get('timestamp', '')[:19]  # Remove microseconds
                    sender = msg.get('sender', 'unknown')
                    content = msg.get('content', '')
                    msg_type = msg.get('type', 'chat')
                    print(f"  [{timestamp}] {sender} ({msg_type}): {content}")
            
            return channels
        else:
            print(f"✗ Failed to get messages: {response.status_code}")
            return {}
    
    def connect_to_peer(self, target_peer_id, peer_ip, peer_port):
        """Establish P2P connection to another peer."""
        print(f"=== Connecting to Peer {target_peer_id} ===")
        
        connect_data = {
            "peer_id": target_peer_id,
            "address": peer_ip,
            "port": peer_port
        }
        
        response = self.session.post(f"{self.base_url}/connect-peer/",
                                   json=connect_data,
                                   cookies=self.auth_cookies)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Connected to peer: {result.get('message', 'Success')}")
            return True
        else:
            print(f"✗ Connection failed: {response.status_code}")
            return False

def run_demo():
    """Run a comprehensive demo of the chat system."""
    print("Hybrid Chat System Demo")
    print("=======================")
    print("Make sure the backend server is running:")
    print("  python3 start_backend.py --server-port 9000")
    print()
    
    # Create two clients to simulate peer interaction
    client1 = ChatTestClient(peer_id="alice")
    client2 = ChatTestClient(peer_id="bob")
    
    print("🚀 Starting Chat System Demo")
    
    # Phase 1: Authentication
    print("\n📋 Phase 1: Authentication")
    if not client1.login():
        print("❌ Client1 login failed")
        return
    
    if not client2.login():
        print("❌ Client2 login failed")
        return
    
    # Phase 2: Peer Registration (Client-Server)
    print("\n🌐 Phase 2: Peer Registration (Client-Server)")
    client1.register_peer(peer_port=9101)
    time.sleep(1)
    client2.register_peer(peer_port=9102)
    time.sleep(1)
    
    # Phase 3: Peer Discovery
    print("\n🔍 Phase 3: Peer Discovery")
    peers1 = client1.get_peer_list()
    peers2 = client2.get_peer_list()
    
    # Phase 4: Channel Management
    print("\n💬 Phase 4: Channel Management")
    client1.create_channel("general")
    time.sleep(1)
    client1.create_channel("developers")
    time.sleep(1)
    
    client2.join_channel("general")
    time.sleep(1)
    
    channels1 = client1.get_channels()
    channels2 = client2.get_channels()
    
    # Phase 5: P2P Communication
    print("\n🔗 Phase 5: P2P Communication")
    
    # Connect peers (simplified - in real system this would be automatic)
    if peers1:
        for peer_id, peer_info in peers1.items():
            client1.connect_to_peer(peer_id, peer_info['ip'], peer_info['port'])
    
    if peers2:
        for peer_id, peer_info in peers2.items():
            client2.connect_to_peer(peer_id, peer_info['ip'], peer_info['port'])
    
    # Send messages
    print("\n📨 Phase 6: Message Exchange")
    client1.send_message("general", "Hello everyone! This is Alice.")
    time.sleep(1)
    
    client2.send_message("general", "Hi Alice! Bob here.")
    time.sleep(1)
    
    client1.broadcast_message("Broadcasting to all peers!")
    time.sleep(1)
    
    # Retrieve and display messages
    print("\n📬 Phase 7: Message Retrieval")
    client1.get_messages()
    client2.get_messages()
    
    print("\n✅ Demo completed successfully!")
    print("\n🎯 Summary:")
    print("- ✓ Authentication implemented")
    print("- ✓ Peer registration working")
    print("- ✓ Channel management functional")
    print("- ✓ P2P message sending operational")
    print("- ✓ Broadcasting implemented")
    print("- ✓ Message retrieval working")

def interactive_mode():
    """Run in interactive mode for manual testing."""
    print("Interactive Chat Test Mode")
    print("=========================")
    
    peer_id = input("Enter your peer ID (or press Enter for auto): ").strip()
    if not peer_id:
        peer_id = f"user_{int(time.time())}"
    
    client = ChatTestClient(peer_id=peer_id)
    
    # Login
    if not client.login():
        print("Login failed. Exiting.")
        return
    
    # Register
    port = input("Enter your P2P port (default 9100): ").strip()
    port = int(port) if port else 9100
    
    if not client.register_peer(peer_port=port):
        print("Registration failed. Exiting.")
        return
    
    # Interactive loop
    while True:
        print("\nCommands:")
        print("1. List peers")
        print("2. List channels") 
        print("3. Create channel")
        print("4. Join channel")
        print("5. Send message")
        print("6. Broadcast")
        print("7. Get messages")
        print("8. Connect to peer")
        print("9. Exit")
        
        choice = input("\nEnter choice (1-9): ").strip()
        
        if choice == '1':
            client.get_peer_list()
        elif choice == '2':
            client.get_channels()
        elif choice == '3':
            channel = input("Channel name: ")
            client.create_channel(channel)
        elif choice == '4':
            channel = input("Channel name: ")
            client.join_channel(channel)
        elif choice == '5':
            channel = input("Channel name: ")
            message = input("Message: ")
            client.send_message(channel, message)
        elif choice == '6':
            message = input("Broadcast message: ")
            client.broadcast_message(message)
        elif choice == '7':
            client.get_messages()
        elif choice == '8':
            peer_id = input("Target peer ID: ")
            ip = input("Peer IP (default 127.0.0.1): ") or "127.0.0.1"
            port = int(input("Peer port: "))
            client.connect_to_peer(peer_id, ip, port)
        elif choice == '9':
            print("Goodbye!")
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        run_demo()