# Run Stats server

Which helps publishing agent server stats, where docker containers are launched.
stats published are cpu, memory, docker instances, docker cpu/memory allocated

## run

```bash
python stats.py
```


# Run Docker agent 

# QVP: CXL Remote Development

## Overview

QVP (Quick Virtualization Platform) is a tool designed to facilitate remote development environments using Docker containers.
It provides a web-based interface to manage and interact with development instances, allowing users to start, stop, and monitor
their containers. The platform also integrates with code-server for web-based IDE access, SSH for terminal access, and SPICE for
remote desktop access.

## Features

- **Container Management**: Start, stop, restart, and remove Docker containers.
- **Resource Monitoring**: Real-time CPU and memory usage statistics.
- **Web-based IDE**: Access to a code-server instance for web-based development.
- **SSH Access**: Direct SSH access to the guest OS running inside the container.
- **Remote Desktop**: SPICE protocol support for remote desktop access.
- **User Isolation**: Each user gets their own isolated environment with unique ports and directories.

## Prerequisites

- Docker installed and running on the host machine.
- Python 3.7 or higher.
- Required Python packages (listed in `requirements.txt`).

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/qvp.git
   cd qvp
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   Create a `.env` file in the root directory with the following variables or u pdate existing file:
   ```env
   WORKDIR_TEMPLATE=/opt/cxl/
   WORKDIR_DEPLOY=/home/vms/
   DEFAULT_WORKSPACE=/config/workspace
   DOCKER_IMAGE=cxl.io/dev/code-server
   DOCKER_TAG=latest
   DOCKER_CPU=2
   DOCKER_CPU_PERCENT=100
   DOCKER_MEM_LMT=2g
   DOCKER_MEM_SWAP=3g
   CODE_PORT=8443
   GUEST_OS_SSH_PORT=22
   GUEST_OS_SPICE_PORT=8100
   MGMT_SERVER_IP=127.0.0.1
   MGMT_SERVER_PORT=5000
   ```

4. **Run the Application**:
   ```bash
   streamlit run docker_agent.py
   ```

## Usage

1. **Access the Web Interface**:
   Open your web browser and navigate to `http://localhost:8501`.

2. **Login**:
   Use the provided user ID and session token to log in.

3. **Manage Instances**:
   - **Create Instance**: Click on the "Create" button to start a new development instance.
   - **Monitor Resources**: View real-time CPU and memory usage statistics.
   - **Access Services**: Use the provided links to access the web-based IDE, SSH terminal, and remote desktop.

4. **Stop/Remove Instances**:
   Use the action buttons to stop, restart, or remove instances as needed.

---

For more detailed information, refer to the code comments and documentation within the repository.
