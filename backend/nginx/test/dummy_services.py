#!/usr/bin/env python3

import http.server
import socketserver
import threading
import time
import sys
import os

class DummyServiceHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve a simple HTML page for VSCode or Jupyter
        service_name = "VSCode" if "vscode" in self.server.service_type.lower() else "Jupyter"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Dummy {service_name} Service</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #333; }}
        .info {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Dummy {service_name} Service</h1>
        <div class="info">
            <p><strong>Service:</strong> {service_name}</p>
            <p><strong>Host:</strong> {self.headers.get('Host')}</p>
            <p><strong>Path:</strong> {self.path}</p>
            <p><strong>Server Port:</strong> {self.server.server_address[1]}</p>
            <p>This is a dummy service for testing NGINX routing.</p>
        </div>
    </div>
</body>
</html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())

    def do_POST(self):
        self.do_GET()

def start_dummy_service(port, service_type):
    """Start a dummy service on the specified port"""
    handler = DummyServiceHandler
    httpd = socketserver.TCPServer(("", port), handler)
    httpd.service_type = service_type
    
    print(f"Starting dummy {service_type} service on port {port}")
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    return httpd, server_thread

def main():
    # Start dummy services
    services = []
    
    # Start VSCode services
    vscode_ports = [8080, 8081, 8082, 8084]
    for port in vscode_ports:
        try:
            httpd, thread = start_dummy_service(port, "VSCode")
            services.append((httpd, thread, port, "VSCode"))
        except OSError as e:
            print(f"Could not start VSCode service on port {port}: {e}")
    
    # Start Jupyter services
    jupyter_ports = [8088, 8089, 8090, 8091]
    for port in jupyter_ports:
        try:
            httpd, thread = start_dummy_service(port, "Jupyter")
            services.append((httpd, thread, port, "Jupyter"))
        except OSError as e:
            print(f"Could not start Jupyter service on port {port}: {e}")
    
    if not services:
        print("No services could be started. Exiting.")
        return
    
    print(f"\nStarted {len(services)} dummy services:")
    for _, _, port, service_type in services:
        print(f"  - {service_type} on port {port}")
    
    print("\nServices are running. Press Ctrl+C to stop.")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down services...")
        for httpd, _, _, _ in services:
            httpd.shutdown()
        print("All services stopped.")

if __name__ == "__main__":
    main()