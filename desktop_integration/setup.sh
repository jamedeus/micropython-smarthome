#!/bin/bash

# Install dependencies
pip3 install -r requirements.txt > /dev/null 2>&1 || { printf "Failed to install dependencies.\n"; exit 1; }
printf "Dependencies installed.\n"

# Copy executable to local bin
cp desktop_integration.py /home/$USER/.local/bin/desktop_integration.py || { printf "Failed to install application.\n"; exit 1; }
printf "Application installed.\n"

# Create service file for current user
cat > micropython-smarthome-integration.service << EOL
[Unit]
Description=Micropython smarthome desktop integration served by gunicorn
After=network.target
StartLimitIntervalSec=30
StartLimitBurst=12

[Service]
Restart=on-failure
User=$USER
Environment="DISPLAY=$DISPLAY"
WorkingDirectory=/home/$USER/.local/bin
ExecStart=/home/$USER/.local/bin/gunicorn --workers 2 --timeout 60 --bind 0.0.0.0:5000 desktop_integration:app

[Install]
WantedBy=network.target
EOL

# Install + detect new service
sudo mv micropython-smarthome-integration.service /usr/lib/systemd/system/ || { printf "Failed to install service file.\n"; exit 1; }
sudo systemctl daemon-reload || { printf "Failed to detect service file.\n"; exit 1; }
printf "Service installed.\n"

# Enable + start
sudo systemctl enable --now micropython-smarthome-integration.service || { printf "Failed to start service.\n"; exit 1; }
printf "\nInstallation complete, service started.\n"
