# Hybrid Chat System - Two Device Testing Guide

This guide shows how to test the hybrid chat system with 2 devices using both direct connection and proxy server.

## Network Setup Overview

```
Device 1 (MacBook)          Device 2 (iPhone/Android/PC)
IP: 192.168.1.100           IP: 192.168.1.101
┌─────────────────┐         ┌─────────────────┐
│  Chat Client    │◄────────┤  Chat Client    │
│                 │         │                 │
│  Backend:9000   │         │  Connects to:   │
│  Proxy:8080     │         │  192.168.1.100  │
└─────────────────┘         └─────────────────┘
```

## Prerequisites

### Find Your Network IP Address

**On macOS/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Look for something like: inet 192.168.1.100
```

**On Windows:**
```cmd
ipconfig
# Look for IPv4 Address under your active network adapter
```

**Example Output:**
- Device 1 (Host): `192.168.1.100`
- Device 2 (Client): `192.168.1.101`

## Testing Scenario 1: Direct Backend Access

### Device 1 (Host - runs backend server)

1. **Start the Backend Server:**
```bash
cd /Users/khoi.lenguyenkim/Desktop/Computer\ Network/BTL/8386-CO3094-weaprous
python3 start_backend.py --server-ip 0.0.0.0 --server-port 9000
```

2. **Test Login Access:**
```bash
# Open browser and go to:
http://192.168.1.100:9000/

# You should see login form. Use:
# Username: admin
# Password: password
```

### Device 2 (Client)

1. **Install Python (if not available):**
   - **Android:** Install Termux app
   - **iOS:** Install Pythonista app
   - **Windows/Mac:** Install Python 3.x

2. **Download the test client:**
```bash
# Create this file on Device 2:
# simple_chat_client.py (copy from the project)
```

3. **Run Test Client:**
```bash
python3 simple_chat_client.py --server-host 192.168.1.100 --server-port 9000
```

## Testing Scenario 2: Using Proxy Server

### Device 1 (Host - runs both backend and proxy)

1. **Start Backend Server:**
```bash
# Terminal 1
python3 start_backend.py --server-ip 127.0.0.1 --server-port 9000
```

2. **Start Proxy Server:**
```bash
# Terminal 2
python3 start_proxy.py --server-ip 0.0.0.0 --server-port 8080
```

3. **Verify Services:**
```bash
# Check if services are running
netstat -an | grep LISTEN | grep -E "(9000|8080)"
# Should show:
# tcp4  0  0  127.0.0.1.9000  *.*  LISTEN
# tcp4  0  0  *.8080          *.*  LISTEN
```

### Device 2 (Client - connects through proxy)

1. **Test via Web Browser:**
```bash
# Open browser and navigate to:
http://192.168.1.100:8080/

# Login with:
# Username: admin
# Password: password
```

2. **Test via Chat Client:**
```bash
python3 simple_chat_client.py --server-host 192.168.1.100 --server-port 8080
```

## Complete Chat System Test

### Step-by-Step Chat Testing

#### Device 1 Setup:
```bash
# Terminal 1: Backend
python3 start_backend.py --server-ip 0.0.0.0 --server-port 9000

# Terminal 2: Proxy (optional)
python3 start_proxy.py --server-ip 0.0.0.0 --server-port 8080

# Terminal 3: Test Client 1
python3 simple_chat_client.py --server-host localhost --server-port 9000
```

#### Device 2 Setup:
```bash
# Connect directly to backend
python3 simple_chat_client.py --server-host 192.168.1.100 --server-port 9000

# OR connect through proxy
python3 simple_chat_client.py --server-host 192.168.1.100 --server-port 8080
```

### Chat Flow Test Sequence

**Device 1 (Alice):**
1. Login: `admin/password`
2. Register peer: `alice` at `192.168.1.100:9101`
3. Create channel: `general`
4. Send message: `Hello from Alice!`

**Device 2 (Bob):**
1. Login: `admin/password`
2. Register peer: `bob` at `192.168.1.101:9102`
3. Join channel: `general`
4. Send message: `Hi Alice! Bob here.`

## API Testing Examples

### 1. Authentication Test
```bash
# POST /login
curl -X POST http://192.168.1.100:9000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=password" \
  -c cookies.txt

# Expected: Set-Cookie: auth=true
```

### 2. Peer Registration Test
```bash
# POST /submit-info/ (Peer Registration)
curl -X POST http://192.168.1.100:9000/submit-info/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "peer_id": "alice",
    "ip": "192.168.1.100", 
    "port": 9101
  }'

# Expected: {"status": "success", "peer_id": "alice"}
```

### 3. Channel Management Test
```bash
# POST /add-list/ (Create Channel)
curl -X POST http://192.168.1.100:9000/add-list/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "action": "create",
    "channel_name": "general"
  }'

# GET /get-list/ (List Channels)
curl -X GET http://192.168.1.100:9000/get-list/ \
  -b cookies.txt
```

### 4. Message Sending Test
```bash
# POST /send-peer/ (Send Message)
curl -X POST http://192.168.1.100:9000/send-peer/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "channel": "general",
    "message": "Hello from API!"
  }'

# GET /send-peer/ (Get Messages)
curl -X GET http://192.168.1.100:9000/send-peer/ \
  -b cookies.txt
```

### 5. Broadcasting Test
```bash
# POST /broadcast-peer/
curl -X POST http://192.168.1.100:9000/broadcast-peer/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "message": "Broadcasting to all peers!"
  }'
```

## Firewall Configuration

### macOS (Device 1 - Host):
```bash
# Allow incoming connections on ports 8080 and 9000
sudo pfctl -f /etc/pf.conf
# Or disable firewall temporarily:
sudo pfctl -d
```

### Windows (if Device 2 is Windows):
```cmd
# Allow Python through Windows Firewall
# Go to: Settings > Network & Internet > Windows Security > Firewall & network protection
# Allow Python.exe through firewall
```

## Troubleshooting

### Common Issues:

1. **Connection Refused:**
   - Check if server is running: `netstat -an | grep 9000`
   - Verify IP address: `ifconfig` or `ipconfig`
   - Check firewall settings

2. **404 Not Found:**
   - Ensure using correct path: `/login`, `/submit-info/`, etc.
   - Check server logs for requests

3. **Authentication Errors:**
   - Verify credentials: `admin/password`
   - Check if cookies are being set

4. **Proxy Issues:**
   - Ensure backend is running before proxy
   - Check proxy configuration in `daemon/proxy.py`
   - Verify Host header in requests

### Debug Commands:

```bash
# Check processes
ps aux | grep python3

# Check network connections
netstat -an | grep -E "(8080|9000)"

# Monitor server logs
tail -f server.log  # if logging to file

# Test network connectivity
ping 192.168.1.100
telnet 192.168.1.100 9000
```

## Sample Test Session

### Terminal Output Examples:

**Device 1 (Host):**
```
[Backend] Listening on port 9000
[Request] BUILDING: Extracting request line from HTTP request
[Request] POST path /login version HTTP/1.1
[HttpAdapter] BUILDING: Processing login request
[HttpAdapter] BUILDING: Valid credentials - sending success response
```

**Device 2 (Client):**
```
=== Testing Login ===
✓ Successfully logged in
=== Testing Peer Registration ===
✓ Peer registered: alice at 192.168.1.100:9101
=== Testing Chat ===
✓ Message sent to general: Hello from Device 2!
```

This setup allows you to test:
- ✅ Authentication with Set-Cookie
- ✅ Peer registration and discovery
- ✅ Channel creation and joining
- ✅ P2P message sending
- ✅ Broadcasting
- ✅ Proxy forwarding
- ✅ Multi-device communication