#!/bin/bash

# Move service file to systemd directory
sudo mv cxl-manager.service /etc/systemd/system/

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable cxl-manager.service

# Start service and show status
sudo systemctl start cxl-manager.service
sudo systemctl status cxl-manager.service