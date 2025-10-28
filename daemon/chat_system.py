#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#

"""
daemon.chat_system
~~~~~~~~~~~~~~~~~

Hybrid Chat System combining Client-Server and Peer-to-Peer paradigms.

This module implements:
1. Client-Server phase: Peer registration, tracking, discovery
2. P2P phase: Direct peer communication, broadcasting
3. Channel management: Create, join, leave channels
4. Message synchronization across distributed peers
"""

import json
import socket
import threading
import time
from datetime import datetime
from .dictionary import CaseInsensitiveDict

class ChatServer:
    """Centralized server for peer registration and discovery."""
    
    def __init__(self):
        self.peers = {}  # {peer_id: {'ip': str, 'port': int, 'channels': set, 'last_seen': datetime}}
        self.channels = {}  # {channel_name: {'peers': set, 'messages': list, 'created': datetime}}
        self.peer_lock = threading.Lock()
        self.channel_lock = threading.Lock()
        
    def register_peer(self, peer_id, ip, port):
        """Register a new peer or update existing peer info."""
        print("[ChatServer] BUILDING: Registering peer {} at {}:{}".format(peer_id, ip, port))
        
        with self.peer_lock:
            self.peers[peer_id] = {
                'ip': ip,
                'port': port, 
                'channels': set(),
                'last_seen': datetime.now(),
                'status': 'online'
            }
        
        return {"status": "success", "peer_id": peer_id, "message": "Peer registered successfully"}
    
    def get_peer_list(self, requesting_peer=None):
        """Get list of active peers."""
        print("[ChatServer] BUILDING: Getting peer list for {}".format(requesting_peer or "anonymous"))
        
        with self.peer_lock:
            active_peers = {}
            for peer_id, peer_info in self.peers.items():
                # Include all peers except the requesting one
                if peer_id != requesting_peer:
                    active_peers[peer_id] = {
                        'ip': peer_info['ip'],
                        'port': peer_info['port'],
                        'status': peer_info['status'],
                        'channels': list(peer_info['channels'])
                    }
        
        return {"status": "success", "peers": active_peers, "count": len(active_peers)}
    
    def create_channel(self, channel_name, creator_peer):
        """Create a new chat channel."""
        print("[ChatServer] BUILDING: Creating channel '{}' by {}".format(channel_name, creator_peer))
        
        with self.channel_lock:
            if channel_name not in self.channels:
                self.channels[channel_name] = {
                    'peers': {creator_peer},
                    'messages': [],
                    'created': datetime.now(),
                    'creator': creator_peer
                }
                
                # Add channel to peer's list
                with self.peer_lock:
                    if creator_peer in self.peers:
                        self.peers[creator_peer]['channels'].add(channel_name)
                
                return {"status": "success", "channel": channel_name, "message": "Channel created"}
            else:
                return {"status": "error", "message": "Channel already exists"}
    
    def join_channel(self, channel_name, peer_id):
        """Join an existing channel."""
        print("[ChatServer] BUILDING: Peer {} joining channel '{}'".format(peer_id, channel_name))
        
        with self.channel_lock:
            if channel_name in self.channels:
                self.channels[channel_name]['peers'].add(peer_id)
                
                with self.peer_lock:
                    if peer_id in self.peers:
                        self.peers[peer_id]['channels'].add(channel_name)
                
                return {"status": "success", "channel": channel_name, "message": "Joined channel"}
            else:
                return {"status": "error", "message": "Channel not found"}
    
    def get_channel_list(self, peer_id=None):
        """Get list of available channels."""
        print("[ChatServer] BUILDING: Getting channel list for {}".format(peer_id or "anonymous"))
        
        with self.channel_lock:
            channel_list = {}
            for channel_name, channel_info in self.channels.items():
                channel_list[channel_name] = {
                    'peer_count': len(channel_info['peers']),
                    'created': channel_info['created'].isoformat(),
                    'creator': channel_info['creator'],
                    'is_member': peer_id in channel_info['peers'] if peer_id else False
                }
        
        return {"status": "success", "channels": channel_list, "count": len(channel_list)}
    
    def get_channel_peers(self, channel_name):
        """Get peers in a specific channel."""
        with self.channel_lock:
            if channel_name in self.channels:
                peers = list(self.channels[channel_name]['peers'])
                return {"status": "success", "channel": channel_name, "peers": peers}
            else:
                return {"status": "error", "message": "Channel not found"}

class ChatPeer:
    """Peer node for P2P communication."""
    
    def __init__(self, peer_id, listen_port):
        self.peer_id = peer_id
        self.listen_port = listen_port
        self.connected_peers = {}  # {peer_id: {'ip': str, 'port': int, 'socket': socket}}
        self.channels = {}  # {channel_name: {'peers': set, 'messages': list}}
        self.peer_lock = threading.Lock()
        self.message_lock = threading.Lock()
        self.server_socket = None
        self.running = False
        
    def start_listening(self):
        """Start listening for incoming P2P connections."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.listen_port))
            self.server_socket.listen(10)
            self.running = True
            
            print("[ChatPeer] {} listening on port {}".format(self.peer_id, self.listen_port))
            
            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                    thread = threading.Thread(target=self.handle_peer_connection, args=(conn, addr))
                    thread.daemon = True
                    thread.start()
                except socket.error as e:
                    if self.running:
                        print("[ChatPeer] Accept error: {}".format(e))
        except Exception as e:
            print("[ChatPeer] Listen error: {}".format(e))
    
    def handle_peer_connection(self, conn, addr):
        """Handle incoming P2P connection."""
        try:
            print("[ChatPeer] BUILDING: Handling peer connection from {}".format(addr))
            
            # Receive message
            data = conn.recv(4096).decode()
            if data:
                message = json.loads(data)
                self.process_peer_message(message, conn, addr)
        except Exception as e:
            print("[ChatPeer] Error handling peer connection: {}".format(e))
        finally:
            conn.close()
    
    def process_peer_message(self, message, conn, addr):
        """Process message received from another peer."""
        msg_type = message.get('type', '')
        
        if msg_type == 'chat_message':
            self.handle_chat_message(message)
        elif msg_type == 'broadcast':
            self.handle_broadcast_message(message)
        elif msg_type == 'connect_request':
            self.handle_connect_request(message, conn, addr)
        else:
            print("[ChatPeer] Unknown message type: {}".format(msg_type))
    
    def handle_chat_message(self, message):
        """Handle incoming chat message."""
        channel = message.get('channel', 'general')
        sender = message.get('sender', 'unknown')
        content = message.get('content', '')
        timestamp = message.get('timestamp', datetime.now().isoformat())
        
        print("[ChatPeer] BUILDING: Received message in '{}' from {}: {}".format(channel, sender, content))
        
        # Store message
        with self.message_lock:
            if channel not in self.channels:
                self.channels[channel] = {'peers': set(), 'messages': []}
            
            self.channels[channel]['messages'].append({
                'sender': sender,
                'content': content,
                'timestamp': timestamp,
                'type': 'chat'
            })
    
    def handle_broadcast_message(self, message):
        """Handle broadcast message."""
        sender = message.get('sender', 'unknown')
        content = message.get('content', '')
        
        print("[ChatPeer] BUILDING: Received broadcast from {}: {}".format(sender, content))
        
        # Store in all joined channels or create a broadcast channel
        with self.message_lock:
            if 'broadcast' not in self.channels:
                self.channels['broadcast'] = {'peers': set(), 'messages': []}
            
            self.channels['broadcast']['messages'].append({
                'sender': sender,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'type': 'broadcast'
            })
    
    def connect_to_peer(self, peer_ip, peer_port, peer_id):
        """Establish direct P2P connection to another peer."""
        try:
            print("[ChatPeer] BUILDING: Connecting to peer {} at {}:{}".format(peer_id, peer_ip, peer_port))
            
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_ip, peer_port))
            
            # Send connection request
            connect_msg = {
                'type': 'connect_request',
                'from_peer': self.peer_id,
                'timestamp': datetime.now().isoformat()
            }
            
            peer_socket.sendall(json.dumps(connect_msg).encode())
            peer_socket.close()
            
            # Store peer info
            with self.peer_lock:
                self.connected_peers[peer_id] = {
                    'ip': peer_ip,
                    'port': peer_port,
                    'status': 'connected'
                }
            
            return {"status": "success", "peer": peer_id, "message": "Connected to peer"}
            
        except Exception as e:
            print("[ChatPeer] Connection error to {}: {}".format(peer_id, e))
            return {"status": "error", "message": str(e)}
    
    def send_message_to_channel(self, channel, content):
        """Send message to all peers in a channel."""
        print("[ChatPeer] BUILDING: Sending message to channel '{}': {}".format(channel, content))
        
        message = {
            'type': 'chat_message',
            'channel': channel,
            'sender': self.peer_id,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store message locally
        self.handle_chat_message(message)
        
        # Send to all connected peers (simplified - in real system, only send to channel members)
        sent_count = 0
        with self.peer_lock:
            for peer_id, peer_info in self.connected_peers.items():
                try:
                    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    peer_socket.connect((peer_info['ip'], peer_info['port']))
                    peer_socket.sendall(json.dumps(message).encode())
                    peer_socket.close()
                    sent_count += 1
                except Exception as e:
                    print("[ChatPeer] Failed to send to {}: {}".format(peer_id, e))
        
        return {"status": "success", "message": "Sent to {} peers".format(sent_count)}
    
    def broadcast_message(self, content):
        """Broadcast message to all connected peers."""
        print("[ChatPeer] BUILDING: Broadcasting message: {}".format(content))
        
        message = {
            'type': 'broadcast',
            'sender': self.peer_id,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store locally
        self.handle_broadcast_message(message)
        
        # Send to all connected peers
        sent_count = 0
        with self.peer_lock:
            for peer_id, peer_info in self.connected_peers.items():
                try:
                    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    peer_socket.connect((peer_info['ip'], peer_info['port']))
                    peer_socket.sendall(json.dumps(message).encode())
                    peer_socket.close()
                    sent_count += 1
                except Exception as e:
                    print("[ChatPeer] Failed to broadcast to {}: {}".format(peer_id, e))
        
        return {"status": "success", "message": "Broadcasted to {} peers".format(sent_count)}
    
    def get_messages(self, channel):
        """Get messages from a specific channel."""
        with self.message_lock:
            if channel in self.channels:
                return {
                    "status": "success", 
                    "channel": channel,
                    "messages": self.channels[channel]['messages']
                }
            else:
                return {"status": "error", "message": "Channel not found"}
    
    def stop(self):
        """Stop the peer server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()

# Global instances for the chat system
chat_server = ChatServer()
active_peers = {}  # {peer_id: ChatPeer instance}