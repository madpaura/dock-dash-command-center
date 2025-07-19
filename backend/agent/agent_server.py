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
    config_path = os.path.join('.streamlit', 'config.toml')
    if os.path.exists(config_path):
        config = toml.load(config_path)
        port = config.get('server', {}).get('backend_port', 8511)
    else:
        port = 8511
    
    app.run(host='0.0.0.0', port=port)
