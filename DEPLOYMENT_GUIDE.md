# 🚀 WeApRous Hybrid Chat System - Hướng Dẫn Triển Khai Mạng Nội Bộ

## 📋 TỔNG QUAN HỆ THỐNG

### Kiến Trúc Hybrid
```
┌─────────────────────────────────────────────────────────────┐
│                    MẠNG NỘI BỘ (LAN)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Device 1 (Host)              Device 2 (Client)           │
│  IP: 192.168.1.100           IP: 192.168.1.101            │
│  ┌─────────────────┐          ┌─────────────────┐          │
│  │   Proxy:8080    │◄─────────┤   Web Browser   │          │
│  │   Backend:9000  │          │                 │          │
│  │   P2P:9100+     │◄─────────┤   P2P:9200+     │          │
│  └─────────────────┘          └─────────────────┘          │
│           │                            │                   │
│           └── HTTP/API Communication ──┘                   │
│           └── Direct P2P Messaging ────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 🔧 BƯỚC 1: CHUẨN BỊ MÔI TRƯỜNG

### 1.1 Kiểm Tra Python
```bash
# Kiểm tra phiên bản Python (yêu cầu 3.6+)
python3 --version

# Nếu chưa có, cài đặt Python 3
# macOS: brew install python3
# Ubuntu: sudo apt install python3
# Windows: Tải từ python.org
```

### 1.2 Chuẩn Bị Network
```bash
# Tìm IP của máy trong mạng nội bộ
# macOS/Linux:
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows:
ipconfig

# Ví dụ output:
# inet 192.168.1.100 netmask 0xffffff00 broadcast 192.168.1.255
```

### 1.3 Kiểm Tra Firewall
```bash
# macOS - Tắt firewall tạm thời (để test)
sudo pfctl -d

# Ubuntu - Mở ports
sudo ufw allow 8080
sudo ufw allow 9000
sudo ufw allow 9100:9200/tcp

# Windows - Mở Control Panel > Windows Defender Firewall
# Thêm exceptions cho ports 8080, 9000, 9100-9200
```

## 🚀 BƯỚC 2: KHỞI TẠO HỆ THỐNG

### 2.1 Device 1 (Host Server) - IP: 192.168.1.100

#### Terminal 1: Khởi tạo Backend Server
```bash
cd /Users/khoi.lenguyenkim/Desktop/Computer\ Network/BTL/8386-CO3094-weaprous

# Khởi tạo backend server trên tất cả interfaces
python3 start_backend.py --server-ip 0.0.0.0 --server-port 9000

# Expected output:
# [Backend] Listening on port 9000
```

#### Terminal 2: Khởi tạo Proxy Server
```bash
# Trong terminal mới
python3 start_proxy.py --server-ip 0.0.0.0 --server-port 8080

# Expected output:
# [Proxy] BUILDING: Resolving routing policy for hostname: localhost:8080
# [Proxy] Listening on port 8080
```

#### Terminal 3: Kiểm tra Services
```bash
# Kiểm tra các services đang chạy
netstat -an | grep LISTEN | grep -E "(8080|9000)"

# Expected output:
# tcp4  0  0  *.8080          *.*     LISTEN    # Proxy
# tcp4  0  0  *.9000          *.*     LISTEN    # Backend
```

### 2.2 Cấu hình Proxy (Đã có sẵn)
File `config/proxy.conf` đã được cấu hình:
```nginx
host "localhost:8080" {
    proxy_pass http://127.0.0.1:9000;
}

host "192.168.1.100:8080" {
    proxy_pass http://192.168.1.100:9000;
}
```

## 🌐 BƯỚC 3: TEST KẾT NỐI CƠ BẢN

### 3.1 Test từ Device 1 (Host)
```bash
# Test direct backend
curl -i http://localhost:9000/

# Test qua proxy
curl -i http://localhost:8080/

# Expected: Trả về login.html hoặc 401 Unauthorized
```

### 3.2 Test từ Device 2 (Client - IP: 192.168.1.101)
```bash
# Test kết nối đến host qua proxy
curl -i http://192.168.1.100:8080/

# Test ping connectivity
ping 192.168.1.100

# Expected: Successful connection
```

## 📱 BƯỚC 4: TRIỂN KHAI WEB INTERFACE

### 4.1 Truy cập từ Web Browser

#### Device 1 (Host):
```
URL: http://localhost:8080/
hoặc: http://192.168.1.100:8080/
```

#### Device 2 (Client):
```
URL: http://192.168.1.100:8080/
```

### 4.2 Luồng Đăng nhập
1. **Mở browser** → Truy cập URL
2. **Login form** xuất hiện (nếu chưa auth)
3. **Nhập credentials**:
   - Username: `admin`
   - Password: `password`
4. **Submit** → Backend xác thực
5. **Redirect** → Chat interface với `Set-Cookie: auth=true`

## 💬 BƯỚC 5: SỬ DỤNG CHAT SYSTEM

### 5.1 Phase 1: Peer Registration
```javascript
// Trình tự hoạt động trong browser:

1. Click "Register as Peer" button
   ↓
2. Auto-detect IP: 192.168.1.100 (Device 1) hoặc 192.168.1.101 (Device 2)
   ↓
3. POST /submit-info/ {
     "peer_id": "user_abc123",
     "ip": "192.168.1.100", 
     "port": 9101
   }
   ↓
4. Server response: {"status": "success", "peer_id": "user_abc123"}
   ↓
5. P2P socket listener started on port 9101
```

### 5.2 Phase 2: Channel Management
```javascript
// Tạo channel:
1. Click "Create Channel" → Modal xuất hiện
2. Nhập tên channel: "general"
3. POST /add-list/ {"action": "create", "channel_name": "general"}

// Join channel:
1. Click vào channel trong sidebar
2. POST /add-list/ {"action": "join", "channel_name": "general"}
```

### 5.3 Phase 3: P2P Messaging
```javascript
// Gửi message:
1. Nhập text trong input box
2. Click Send hoặc Enter
3. POST /send-peer/ {"channel": "general", "message": "Hello!"}
4. Message được gửi P2P trực tiếp đến các peers khác

// Broadcast:
1. Click "📢 Broadcast" button
2. POST /broadcast-peer/ {"message": "Hello everyone!"}
3. Message được gửi đến tất cả peers
```

## 🔍 BƯỚC 6: KIỂM TRA VÀ DEBUG

### 6.1 Monitoring Logs

#### Backend Logs:
```bash
# Terminal với backend server:
[Backend] Listening on port 9000
[Request] BUILDING: Extracting request line from HTTP request
[Request] POST path /login version HTTP/1.1
[HttpAdapter] BUILDING: Processing login request
[API] BUILDING: Handling POST request to /submit-info/
[ChatServer] BUILDING: Registering peer user_abc123 at 192.168.1.100:9101
```

#### Proxy Logs:
```bash
# Terminal với proxy server:
[Proxy] BUILDING: Resolving routing policy for hostname: 192.168.1.100:8080
[Proxy] BUILDING: Forwarding request to backend 192.168.1.100:9000
```

### 6.2 Kiểm tra P2P Connections
```bash
# Kiểm tra các P2P ports đang listen
netstat -an | grep LISTEN | grep 910

# Expected output:
# tcp4  0  0  *.9101          *.*     LISTEN    # Peer 1
# tcp4  0  0  *.9102          *.*     LISTEN    # Peer 2
```

### 6.3 Test API Endpoints
```bash
# Test peer registration
curl -X POST http://192.168.1.100:8080/submit-info/ \
  -H "Content-Type: application/json" \
  -H "Cookie: auth=true" \
  -d '{
    "peer_id": "test_user",
    "ip": "192.168.1.101",
    "port": 9102
  }'

# Test get peer list
curl -X GET http://192.168.1.100:8080/get-list/ \
  -H "Cookie: auth=true"

# Test send message
curl -X POST http://192.168.1.100:8080/send-peer/ \
  -H "Content-Type: application/json" \
  -H "Cookie: auth=true" \
  -d '{
    "channel": "general",
    "message": "Hello from API!"
  }'
```

## 🔧 TROUBLESHOOTING

### Lỗi thường gặp:

#### 1. Connection Refused
```bash
# Nguyên nhân: Backend chưa chạy hoặc firewall block
# Giải pháp:
netstat -an | grep 9000  # Kiểm tra backend
sudo pfctl -d            # Tắt firewall (macOS)
```

#### 2. 404 Not Found
```bash
# Nguyên nhân: Proxy config sai hoặc routing lỗi
# Giải pháp: Kiểm tra config/proxy.conf
# Đảm bảo hostname mapping đúng
```

#### 3. Authentication Failed
```bash
# Nguyên nhân: Cookie không được set
# Giải pháp: 
# - Kiểm tra POST /login với admin/password
# - Kiểm tra Set-Cookie header trong response
```

#### 4. P2P Connection Failed
```bash
# Nguyên nhân: Peer chưa register hoặc port bị block
# Giải pháp:
# - Đảm bảo peer đã register thành công
# - Kiểm tra P2P ports (9100+) không bị firewall block
```

## 📊 MONITORING VÀ PERFORMANCE

### Real-time monitoring:
```bash
# Monitor network connections
watch 'netstat -an | grep -E "(8080|9000|910[0-9])"'

# Monitor process usage
top -p $(pgrep -f "start_backend\|start_proxy")
```

## 🎯 SCENARIOS TEST

### Scenario 1: 2 Devices Basic Chat
1. Device 1: Register as peer_alice
2. Device 2: Register as peer_bob  
3. Device 1: Create channel "general"
4. Device 2: Join channel "general"
5. Both: Exchange messages via P2P

### Scenario 2: Broadcast Testing
1. Device 1: Send broadcast message
2. Device 2: Should receive broadcast
3. Verify message appears in all peers

### Scenario 3: Multi-Channel
1. Create multiple channels: "general", "tech", "random"
2. Join different combinations
3. Test message isolation between channels

## 🔐 SECURITY CONSIDERATIONS

### Production Deployment:
- ✅ Enable HTTPS với SSL certificates
- ✅ Implement proper authentication (JWT tokens)
- ✅ Add rate limiting cho API endpoints
- ✅ Validate all P2P connections
- ✅ Enable firewall với specific port rules

### Current Demo Limitations:
- ⚠️ Simple admin/password authentication
- ⚠️ No encryption cho P2P messages
- ⚠️ Basic error handling
- ⚠️ No persistent storage

---

## 📞 SUPPORT

Nếu gặp vấn đề:
1. Kiểm tra logs trong terminals
2. Test từng component riêng lẻ
3. Verify network connectivity
4. Check firewall settings

**Happy Chatting! 🎉**