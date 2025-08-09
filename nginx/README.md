# Nginx Routing for VSCode and Jupyter Services

This setup provides load balancing and routing for VSCode and Jupyter services hosted on multiple servers.

## Complete File Structure

- `nginx.conf` - Main Nginx configuration file with status endpoint
- `sites-available/dev-services` - Service configuration with load balancing
- `sites-enabled/dev-services` - Symlink to enable the site (created during setup)
- `manage_servers.sh` - Script to dynamically add/remove backend servers
- `nginx_manager_api.py` - REST API for programmatic server management
- `manager.html` - Web interface for managing servers
- `health_check.sh` - Script to check backend server health
- `enable-site.sh` - Script to ensure the site is enabled
- `dev-services-enable-site.service` - Systemd service to auto-enable site
- `dev-services-nginx.service` - Systemd service to reload Nginx config
- `nginx-manager-api.service` - Systemd service for the API server
- `README.md` - This file

## Setup Instructions

1. Install Nginx:
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. Copy the configuration files to the appropriate locations:
   ```bash
   sudo cp nginx.conf /etc/nginx/nginx.conf
   sudo cp sites-available/dev-services /etc/nginx/sites-available/
   sudo ln -s /etc/nginx/sites-available/dev-services /etc/nginx/sites-enabled/
   ```

3. Test the configuration:
   ```bash
   sudo nginx -t
   ```

4. Reload Nginx:
   ```bash
   sudo systemctl reload nginx
   ```

## Adding New Users

Use the `add_user.sh` script to add new users with their respective VSCode and Jupyter servers:

```bash
# Add a new user with their VSCode and Jupyter servers
sudo ./add_user.sh user3 192.168.1.10:8082 192.168.1.30:8090
```

The script will:
1. Validate the inputs
2. Check that the user doesn't already exist
3. Add the new user's upstream blocks to the NGINX configuration
4. Automatically reload NGINX to apply the changes

After adding a user, they can access their services at:
- VSCode: http://your-server-ip/username/vscode/
- Jupyter: http://your-server-ip/username/jupyter/

### Web Interface

Open `manager.html` in a web browser to manage servers through a graphical interface.

### REST API

Start the API server:
```bash
sudo cp nginx-manager-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nginx-manager-api
sudo systemctl start nginx-manager-api
```

The API will be available at http://your-server-ip:8081

API endpoints:
- `GET /api/servers` - List all servers
- `POST /api/servers` - Add a server
- `DELETE /api/servers?service=vscode&server=IP:PORT` - Remove a server

Example API usage:
```bash
# List servers
curl http://localhost:8081/api/servers

# Add a server
curl -X POST -H "Content-Type: application/json" \
  -d '{"service": "vscode", "server": "192.168.1.10:8080"}' \
  http://localhost:8081/api/servers

# Remove a server
curl -X DELETE "http://localhost:8081/api/servers?service=vscode&server=192.168.1.10:8080"
```

## Accessing Services

- User1 VSCode: http://your-server-ip/user1/vscode/
- User1 Jupyter: http://your-server-ip/user1/jupyter/
- User2 VSCode: http://your-server-ip/user2/vscode/
- User2 Jupyter: http://your-server-ip/user2/jupyter/
- Health check: http://your-server-ip/health
- API management: http://your-server-ip:8081/
- Nginx status: http://your-server-ip:8082/nginx_status

## Configuration Details

- Uses `least_conn` load balancing algorithm for better distribution
- Includes WebSocket support for both services
- Implements health checks with failover
- Provides session persistence
- Configured with appropriate timeouts

## Security Considerations

For production use, consider:

1. Enabling SSL/TLS with Let's Encrypt:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx
   ```

2. Adding authentication layer for sensitive services

3. Configuring rate limiting to prevent abuse

4. Setting up proper firewall rules

5. Restricting API access to authorized users only

## Advanced Configuration

To enable SSL for the API server, you can modify the systemd service file to use a reverse proxy through Nginx with SSL termination.

For high availability, consider setting up multiple Nginx instances with a load balancer in front of them.

## Monitoring

Use the provided `health_check.sh` script to monitor backend server status:

```bash
./health_check.sh
```

The script will show the status of all configured backend servers and return exit code 0 if all servers are healthy, or 1 if any servers are down.

You can also check Nginx's built-in status at http://your-server-ip:8082/nginx_status