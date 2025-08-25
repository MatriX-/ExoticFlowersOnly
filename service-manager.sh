#!/bin/bash

# Exotic Flowers Service Manager
# Manages the Exotic Flowers Google Sheets sync service

set -e

SERVICE_NAME="exoticflowers"
PROJECT_DIR="/Users/stephen/exoticflowers"
SERVICE_FILE="${PROJECT_DIR}/${SERVICE_NAME}.service"
SYSTEMD_DIR="/etc/systemd/system"
USER=$(whoami)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root for certain operations
check_root() {
    if [[ $EUID -eq 0 ]]; then
        return 0
    else
        return 1
    fi
}

# Check if service exists
service_exists() {
    systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"
}

# Check if service is running
service_running() {
    systemctl is-active --quiet "${SERVICE_NAME}.service" 2>/dev/null
}

# Check if service is enabled
service_enabled() {
    systemctl is-enabled --quiet "${SERVICE_NAME}.service" 2>/dev/null
}

# Install the service
install_service() {
    log "Installing Exotic Flowers service..."
    
    # Check if project directory exists
    if [[ ! -d "$PROJECT_DIR" ]]; then
        error "Project directory $PROJECT_DIR does not exist!"
        exit 1
    fi
    
    # Check if Python virtual environment exists
    if [[ ! -f "$PROJECT_DIR/venv/bin/python" ]]; then
        error "Python virtual environment not found at $PROJECT_DIR/venv/"
        error "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
    
    # Check if main.py exists
    if [[ ! -f "$PROJECT_DIR/main.py" ]]; then
        error "main.py not found in $PROJECT_DIR"
        exit 1
    fi
    
    # Update service file with current user
    sed "s/%i/$USER/g" "$SERVICE_FILE" > "/tmp/${SERVICE_NAME}.service"
    
    # Copy service file (requires sudo)
    if ! check_root; then
        log "Copying service file (requires sudo)..."
        sudo cp "/tmp/${SERVICE_NAME}.service" "$SYSTEMD_DIR/${SERVICE_NAME}.service"
        sudo chown root:root "$SYSTEMD_DIR/${SERVICE_NAME}.service"
        sudo chmod 644 "$SYSTEMD_DIR/${SERVICE_NAME}.service"
    else
        cp "/tmp/${SERVICE_NAME}.service" "$SYSTEMD_DIR/${SERVICE_NAME}.service"
        chown root:root "$SYSTEMD_DIR/${SERVICE_NAME}.service"
        chmod 644 "$SYSTEMD_DIR/${SERVICE_NAME}.service"
    fi
    
    # Reload systemd
    if ! check_root; then
        sudo systemctl daemon-reload
    else
        systemctl daemon-reload
    fi
    
    success "Service installed successfully!"
}

# Enable the service
enable_service() {
    log "Enabling service to start on boot..."
    
    if ! service_exists; then
        error "Service not installed. Run '$0 install' first."
        exit 1
    fi
    
    if ! check_root; then
        sudo systemctl enable "${SERVICE_NAME}.service"
    else
        systemctl enable "${SERVICE_NAME}.service"
    fi
    
    success "Service enabled for automatic startup!"
}

# Start the service
start_service() {
    log "Starting Exotic Flowers service..."
    
    if ! service_exists; then
        error "Service not installed. Run '$0 install' first."
        exit 1
    fi
    
    if service_running; then
        warning "Service is already running!"
        return 0
    fi
    
    if ! check_root; then
        sudo systemctl start "${SERVICE_NAME}.service"
    else
        systemctl start "${SERVICE_NAME}.service"
    fi
    
    # Wait a moment and check if it started successfully
    sleep 2
    if service_running; then
        success "Service started successfully!"
    else
        error "Service failed to start. Check status with '$0 status'"
        exit 1
    fi
}

# Stop the service
stop_service() {
    log "Stopping Exotic Flowers service..."
    
    if ! service_exists; then
        warning "Service not installed."
        return 0
    fi
    
    if ! service_running; then
        warning "Service is not running."
        return 0
    fi
    
    if ! check_root; then
        sudo systemctl stop "${SERVICE_NAME}.service"
    else
        systemctl stop "${SERVICE_NAME}.service"
    fi
    
    success "Service stopped!"
}

# Restart the service
restart_service() {
    log "Restarting Exotic Flowers service..."
    
    if ! service_exists; then
        error "Service not installed. Run '$0 install' first."
        exit 1
    fi
    
    if ! check_root; then
        sudo systemctl restart "${SERVICE_NAME}.service"
    else
        systemctl restart "${SERVICE_NAME}.service"
    fi
    
    # Wait a moment and check if it started successfully
    sleep 2
    if service_running; then
        success "Service restarted successfully!"
    else
        error "Service failed to restart. Check status with '$0 status'"
        exit 1
    fi
}

# Show service status
show_status() {
    log "Checking service status..."
    echo
    
    if ! service_exists; then
        echo "Service Status: ${RED}Not Installed${NC}"
        echo "Run '$0 install' to install the service."
        return 0
    fi
    
    # Service status
    if service_running; then
        echo -e "Service Status: ${GREEN}Running${NC}"
    else
        echo -e "Service Status: ${RED}Stopped${NC}"
    fi
    
    # Enabled status
    if service_enabled; then
        echo -e "Auto-start: ${GREEN}Enabled${NC}"
    else
        echo -e "Auto-start: ${RED}Disabled${NC}"
    fi
    
    echo
    echo "Detailed status:"
    systemctl status "${SERVICE_NAME}.service" --no-pager -l
}

# Show service logs
show_logs() {
    if ! service_exists; then
        error "Service not installed."
        exit 1
    fi
    
    log "Showing service logs (press Ctrl+C to exit)..."
    echo
    
    # Follow logs
    if [[ "$1" == "--follow" ]] || [[ "$1" == "-f" ]]; then
        journalctl -u "${SERVICE_NAME}.service" -f --no-pager
    else
        journalctl -u "${SERVICE_NAME}.service" --no-pager -l
    fi
}

# Uninstall the service
uninstall_service() {
    log "Uninstalling Exotic Flowers service..."
    
    if ! service_exists; then
        warning "Service not installed."
        return 0
    fi
    
    # Stop service if running
    if service_running; then
        stop_service
    fi
    
    # Disable service if enabled
    if service_enabled; then
        log "Disabling service..."
        if ! check_root; then
            sudo systemctl disable "${SERVICE_NAME}.service"
        else
            systemctl disable "${SERVICE_NAME}.service"
        fi
    fi
    
    # Remove service file
    if ! check_root; then
        sudo rm -f "$SYSTEMD_DIR/${SERVICE_NAME}.service"
        sudo systemctl daemon-reload
    else
        rm -f "$SYSTEMD_DIR/${SERVICE_NAME}.service"
        systemctl daemon-reload
    fi
    
    success "Service uninstalled successfully!"
}

# Setup complete installation
setup_complete() {
    log "Setting up Exotic Flowers service for auto-start..."
    
    install_service
    enable_service
    start_service
    
    echo
    success "Setup complete! The service will now:"
    echo "  ✓ Start automatically on system boot"
    echo "  ✓ Restart automatically if it crashes"
    echo "  ✓ Run the scheduler to sync sheets every hour"
    echo
    echo "Use '$0 status' to check the service status"
    echo "Use '$0 logs' to view service logs"
}

# Show help
show_help() {
    echo "Exotic Flowers Service Manager"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  setup     Install, enable, and start the service (complete setup)"
    echo "  install   Install the service files"
    echo "  enable    Enable auto-start on boot"
    echo "  start     Start the service"
    echo "  stop      Stop the service"
    echo "  restart   Restart the service"
    echo "  status    Show service status"
    echo "  logs      Show service logs"
    echo "  logs -f   Follow service logs in real-time"
    echo "  uninstall Remove the service completely"
    echo "  help      Show this help message"
    echo
    echo "Examples:"
    echo "  $0 setup          # Complete setup (recommended)"
    echo "  $0 status         # Check if service is running"
    echo "  $0 logs -f        # Watch logs in real-time"
    echo "  $0 restart        # Restart the service"
    echo
}

# Main script logic
case "${1:-help}" in
    "setup")
        setup_complete
        ;;
    "install")
        install_service
        ;;
    "enable")
        enable_service
        ;;
    "start")
        start_service
        ;;
    "stop")
        stop_service
        ;;
    "restart")
        restart_service
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$2"
        ;;
    "uninstall")
        uninstall_service
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
