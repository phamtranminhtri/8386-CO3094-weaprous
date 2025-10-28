#!/usr/bin/env python3
"""
Quick Setup Script for 2-Device Chat Testing
"""

import sys
import subprocess
import socket
import time
import argparse

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def check_port_available(port):
    """Check if a port is available"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', port))
        s.close()
        return True
    except OSError:
        return False

def start_backend(ip="0.0.0.0", port=9000):
    """Start the backend server"""
    if not check_port_available(port):
        print(f"❌ Port {port} is already in use")
        return None
    
    print(f"🚀 Starting backend server on {ip}:{port}")
    cmd = ["python3", "start_backend.py", "--server-ip", ip, "--server-port", str(port)]
    return subprocess.Popen(cmd)

def start_proxy(ip="0.0.0.0", port=8080):
    """Start the proxy server"""
    if not check_port_available(port):
        print(f"❌ Port {port} is already in use")
        return None
    
    print(f"🔄 Starting proxy server on {ip}:{port}")
    cmd = ["python3", "start_proxy.py", "--server-ip", ip, "--server-port", str(port)]
    return subprocess.Popen(cmd)

def start_test_client(host, port=9000):
    """Start the test client"""
    print(f"💬 Starting test client connecting to {host}:{port}")
    cmd = ["python3", "simple_chat_client.py", "--server-host", host, "--server-port", str(port)]
    return subprocess.Popen(cmd)

def main():
    parser = argparse.ArgumentParser(description="Quick setup for 2-device chat testing")
    parser.add_argument("--mode", choices=["host", "client", "both"], default="host",
                       help="Running mode: host (server), client (test client), or both")
    parser.add_argument("--host-ip", default=None,
                       help="Host IP address (auto-detect if not provided)")
    parser.add_argument("--backend-port", type=int, default=9000,
                       help="Backend server port")
    parser.add_argument("--proxy-port", type=int, default=8080,
                       help="Proxy server port")
    parser.add_argument("--use-proxy", action="store_true",
                       help="Use proxy server for client connections")
    
    args = parser.parse_args()
    
    local_ip = get_local_ip()
    host_ip = args.host_ip or local_ip
    
    print("=" * 50)
    print("🌐 2-Device Chat System Setup")
    print("=" * 50)
    print(f"📍 Local IP: {local_ip}")
    print(f"📍 Host IP: {host_ip}")
    print(f"📍 Mode: {args.mode}")
    print("=" * 50)
    
    processes = []
    
    try:
        if args.mode in ["host", "both"]:
            # Start backend server
            backend_process = start_backend("0.0.0.0", args.backend_port)
            if backend_process:
                processes.append(("Backend", backend_process))
                time.sleep(2)  # Wait for backend to start
            
            # Start proxy server if requested
            if args.use_proxy:
                proxy_process = start_proxy("0.0.0.0", args.proxy_port)
                if proxy_process:
                    processes.append(("Proxy", proxy_process))
                    time.sleep(2)  # Wait for proxy to start
        
        if args.mode in ["client", "both"]:
            # Start test client
            client_port = args.proxy_port if args.use_proxy else args.backend_port
            client_process = start_test_client(host_ip, client_port)
            if client_process:
                processes.append(("Test Client", client_process))
        
        if processes:
            print("\n✅ Services started successfully!")
            print("\n📋 Connection Information:")
            if args.mode in ["host", "both"]:
                print(f"   Backend Server: http://{host_ip}:{args.backend_port}")
                if args.use_proxy:
                    print(f"   Proxy Server: http://{host_ip}:{args.proxy_port}")
                print(f"   Login: admin/password")
            
            print("\n🔧 For Device 2 (other device):")
            if args.use_proxy:
                print(f"   python3 simple_chat_client.py --server-host {host_ip} --server-port {args.proxy_port}")
            else:
                print(f"   python3 simple_chat_client.py --server-host {host_ip} --server-port {args.backend_port}")
            
            print("\n📱 Web Access:")
            if args.use_proxy:
                print(f"   http://{host_ip}:{args.proxy_port}")
            else:
                print(f"   http://{host_ip}:{args.backend_port}")
            
            print("\n⏹  Press Ctrl+C to stop all services")
            
            # Wait for all processes
            for name, process in processes:
                process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        for name, process in processes:
            print(f"   Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("✅ All services stopped")

if __name__ == "__main__":
    main()