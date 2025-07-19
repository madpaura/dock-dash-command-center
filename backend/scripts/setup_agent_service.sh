#!/bin/bash

# Move service file to systemd directory
sudo mv cxl-agent.service /etc/systemd/system/

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable cxl-agent.service

# Start service and show status
sudo systemctl start cxl-agent.service
sudo systemctl status cxl-agent.service