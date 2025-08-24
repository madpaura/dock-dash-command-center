from flask import Flask
from flask_cors import CORS
from monitoring_service import init_stats_routes, register_agent_with_manager
from container_manager import init_backend_routes
import toml

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env", override=True)

app = Flask(__name__)
CORS(app)

register_agent_with_manager()

# Initialize routes from both modules
init_stats_routes(app)
init_backend_routes(app)

if __name__ == '__main__':
    config_path = os.path.join('..', 'config.toml')
    port = 8510
    
    if os.path.exists(config_path):
        try:
            config = toml.load(config_path)
            port = config.get('agent', {}).get('port', port)
        except Exception as e:
            print(f"Error loading config: {e}")
    
    print(f"Starting agent server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
