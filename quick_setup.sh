#!/bin/bash

# WeApRous Hybrid Chat System - Quick Setup Script
# Sử dụng: ./quick_setup.sh [host|client]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}=================================================================================${NC}"
    echo -e "${BLUE} 🚀 WeApRous Hybrid Chat System - Quick Setup${NC}"
    echo -e "${BLUE}=================================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Detect local IP
get_local_ip() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        LOCAL_IP=$(ip route get 8.8.8.8 | grep -oP 'src \K\S+')
    else
        LOCAL_IP="127.0.0.1"
        print_warning "Could not detect OS, using localhost"
    fi
    
    if [ -z "$LOCAL_IP" ]; then
        LOCAL_IP="127.0.0.1"
        print_warning "Could not detect local IP, using localhost"
    fi
}

# Check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python 3 found: $PYTHON_VERSION"
    
    # Check required ports
    if ! check_port 8080; then
        print_error "Port 8080 is already in use"
        exit 1
    fi
    
    if ! check_port 9000; then
        print_error "Port 9000 is already in use" 
        exit 1
    fi
    
    print_success "Required ports 8080 and 9000 are available"
}

# Setup host (server)
setup_host() {
    print_info "Setting up HOST server on IP: $LOCAL_IP"
    
    # Create log directory
    mkdir -p logs
    
    # Start backend server
    print_info "Starting backend server on port 9000..."
    python3 start_backend.py --server-ip 0.0.0.0 --server-port 9000 > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    sleep 2
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        print_success "Backend server started (PID: $BACKEND_PID)"
        echo $BACKEND_PID > logs/backend.pid
    else
        print_error "Failed to start backend server"
        exit 1
    fi
    
    # Start proxy server
    print_info "Starting proxy server on port 8080..."
    python3 start_proxy.py --server-ip 0.0.0.0 --server-port 8080 > logs/proxy.log 2>&1 &
    PROXY_PID=$!
    sleep 2
    
    if kill -0 $PROXY_PID 2>/dev/null; then
        print_success "Proxy server started (PID: $PROXY_PID)"
        echo $PROXY_PID > logs/proxy.pid
    else
        print_error "Failed to start proxy server"
        exit 1
    fi
    
    # Test services
    print_info "Testing services..."
    sleep 3
    
    if curl -s http://localhost:8080/ >/dev/null 2>&1; then
        print_success "Proxy server is responding"
    else
        print_warning "Proxy server might not be fully ready yet"
    fi
    
    if curl -s http://localhost:9000/ >/dev/null 2>&1; then
        print_success "Backend server is responding"
    else
        print_warning "Backend server might not be fully ready yet"
    fi
    
    # Display access information
    echo ""
    echo -e "${GREEN}🎉 HOST SETUP COMPLETE! 🎉${NC}"
    echo ""
    echo -e "${YELLOW}📱 Access URLs:${NC}"
    echo -e "   Local:    http://localhost:8080/"
    echo -e "   Network:  http://$LOCAL_IP:8080/"
    echo ""
    echo -e "${YELLOW}🔧 Admin Credentials:${NC}"
    echo -e "   Username: admin"
    echo -e "   Password: password"
    echo ""
    echo -e "${YELLOW}📊 Process Information:${NC}"
    echo -e "   Backend PID: $BACKEND_PID (Port 9000)"
    echo -e "   Proxy PID:   $PROXY_PID (Port 8080)"
    echo ""
    echo -e "${YELLOW}📝 Logs:${NC}"
    echo -e "   Backend: logs/backend.log"
    echo -e "   Proxy:   logs/proxy.log"
    echo ""
    echo -e "${BLUE}📱 Share this URL with other devices:${NC}"
    echo -e "   ${GREEN}http://$LOCAL_IP:8080/${NC}"
}

# Setup client instructions
setup_client() {
    print_info "CLIENT setup instructions"
    echo ""
    echo -e "${YELLOW}📱 To connect as CLIENT:${NC}"
    echo ""
    echo -e "${BLUE}1. Get the HOST IP address from the host device${NC}"
    echo -e "${BLUE}2. Open web browser and navigate to: http://HOST_IP:8080/${NC}"
    echo -e "${BLUE}3. Login with credentials: admin/password${NC}"
    echo -e "${BLUE}4. Register as peer and start chatting!${NC}"
    echo ""
    echo -e "${YELLOW}🔍 Example URLs:${NC}"
    echo -e "   http://192.168.1.100:8080/"
    echo -e "   http://192.168.1.101:8080/"
    echo ""
    echo -e "${YELLOW}🧪 Test connectivity to host:${NC}"
    echo -e "   ping HOST_IP"
    echo -e "   curl -i http://HOST_IP:8080/"
}

# Stop services
stop_services() {
    print_info "Stopping services..."
    
    if [ -f logs/backend.pid ]; then
        BACKEND_PID=$(cat logs/backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            print_success "Backend server stopped"
        fi
        rm -f logs/backend.pid
    fi
    
    if [ -f logs/proxy.pid ]; then
        PROXY_PID=$(cat logs/proxy.pid)
        if kill -0 $PROXY_PID 2>/dev/null; then
            kill $PROXY_PID
            print_success "Proxy server stopped"
        fi
        rm -f logs/proxy.pid
    fi
    
    # Kill any remaining python processes for this project
    pkill -f "start_backend.py" 2>/dev/null || true
    pkill -f "start_proxy.py" 2>/dev/null || true
    
    print_success "All services stopped"
}

# Status check
check_status() {
    print_info "Checking service status..."
    
    if [ -f logs/backend.pid ]; then
        BACKEND_PID=$(cat logs/backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            print_success "Backend server running (PID: $BACKEND_PID)"
        else
            print_error "Backend server not running (stale PID file)"
        fi
    else
        print_error "Backend server not running"
    fi
    
    if [ -f logs/proxy.pid ]; then
        PROXY_PID=$(cat logs/proxy.pid)
        if kill -0 $PROXY_PID 2>/dev/null; then
            print_success "Proxy server running (PID: $PROXY_PID)"
        else
            print_error "Proxy server not running (stale PID file)"
        fi
    else
        print_error "Proxy server not running"
    fi
    
    # Check ports
    if check_port 8080; then
        print_error "Port 8080 not in use"
    else
        print_success "Port 8080 is active"
    fi
    
    if check_port 9000; then
        print_error "Port 9000 not in use"
    else
        print_success "Port 9000 is active"
    fi
}

# Show usage
show_usage() {
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 host     - Setup as HOST (runs backend + proxy servers)"
    echo "  $0 client   - Show CLIENT connection instructions"  
    echo "  $0 stop     - Stop all running services"
    echo "  $0 status   - Check service status"
    echo "  $0 help     - Show this help message"
    echo ""
}

# Cleanup on exit
cleanup() {
    if [ "$1" = "host" ]; then
        echo ""
        print_info "Cleaning up..."
        stop_services
    fi
}

# Main script
main() {
    print_header
    get_local_ip
    
    case "${1:-help}" in
        "host")
            trap 'cleanup host' EXIT INT TERM
            check_prerequisites
            setup_host
            
            echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"
            echo ""
            
            # Keep script running and monitor services
            while true; do
                sleep 5
                
                # Check if services are still running
                if [ -f logs/backend.pid ]; then
                    BACKEND_PID=$(cat logs/backend.pid)
                    if ! kill -0 $BACKEND_PID 2>/dev/null; then
                        print_error "Backend server has stopped unexpectedly"
                        break
                    fi
                fi
                
                if [ -f logs/proxy.pid ]; then
                    PROXY_PID=$(cat logs/proxy.pid)
                    if ! kill -0 $PROXY_PID 2>/dev/null; then
                        print_error "Proxy server has stopped unexpectedly"
                        break
                    fi
                fi
            done
            ;;
        "client")
            setup_client
            ;;
        "stop")
            stop_services
            ;;
        "status")
            check_status
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

# Run main function
main "$@"