#!/bin/bash

# Quick setup script for Exotic Flowers service
# This script sets up the application as a system service

set -e

echo "=== Exotic Flowers Service Setup ==="
echo

# Make service manager executable
chmod +x service-manager.sh

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "⚠️  Detected macOS - Creating launchd service instead of systemd"
    echo
    
    # Create launchd plist for macOS
    cat > com.exoticflowers.sync.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.exoticflowers.sync</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/stephen/exoticflowers/venv/bin/python</string>
        <string>main.py</string>
        <string>start-scheduler</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/stephen/exoticflowers</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/Users/stephen/exoticflowers/logs/service.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/stephen/exoticflowers/logs/service-error.log</string>
    
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF

    # Install the service
    echo "Installing launchd service..."
    cp com.exoticflowers.sync.plist ~/Library/LaunchAgents/
    launchctl load ~/Library/LaunchAgents/com.exoticflowers.sync.plist
    
    echo "✅ Service installed and started!"
    echo
    echo "Service commands:"
    echo "  Start:   launchctl start com.exoticflowers.sync"
    echo "  Stop:    launchctl stop com.exoticflowers.sync"
    echo "  Restart: launchctl stop com.exoticflowers.sync && launchctl start com.exoticflowers.sync"
    echo "  Status:  launchctl list | grep exoticflowers"
    echo "  Logs:    tail -f logs/service.log"
    echo "  Unload:  launchctl unload ~/Library/LaunchAgents/com.exoticflowers.sync.plist"
    echo
    
else
    # Linux/systemd
    echo "🐧 Detected Linux - Using systemd service"
    echo
    echo "Running complete service setup..."
    ./service-manager.sh setup
fi

echo "🎉 Setup complete!"
echo
echo "Your Exotic Flowers sync service is now:"
echo "  ✓ Installed as a system service"
echo "  ✓ Set to start automatically on boot/login"
echo "  ✓ Will restart automatically if it crashes"
echo "  ✓ Running the scheduler to sync sheets every hour"
echo
echo "Check the application status with:"
echo "  python main.py status"
