import os
import platform
import socket
import hashlib
import uuid
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import dateutil.parser
import webbrowser
import requests
from datetime import datetime
from typing import Dict, Optional
from loguru import logger
from dotenv import load_dotenv
from streamlit_option_menu import option_menu

# Project imports
from resource_allocator import PortManager

# Backend API configuration
BACKEND_URL = "http://localhost:8511"

def api_request(method, endpoint, data=None):
    try:
        url = f"{BACKEND_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

@st.dialog("Error")
def error_msg(msg, url=None):
    st.error(msg, icon="🚨")
    if url:
        st.write(f"Please visit to install necessary toolchain: {url}")
        if st.button("Go"):
            webbrowser.open(url)

def create_gauge(value, title, color="royalblue"):
    """Create a gauge chart using Plotly"""
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 50], "color": "lightgreen"},
                    {"range": [50, 80], "color": "orange"},
                    {"range": [80, 100], "color": "orangered"},
                ],
            },
        )
    ).update_layout(height=300)

def display_container_stats(container_id):
    st.header("Usage Statistics")
    try:
        stats = api_request("GET", f"/api/containers/{container_id}/stats")
        if stats and stats.get("success"):
            stats = stats["stats"]
            col1, col2 = st.columns(2)

            with col1:
                st.plotly_chart(
                    create_gauge(stats["cpu_usage"], "CPU Usage (%)"),
                    use_container_width=True,
                )

            with col2:
                st.plotly_chart(
                    create_gauge(stats["memory_usage"], "Memory Usage (%)"),
                    use_container_width=True,
                )

            st.metric("Memory Used (MB)", f"{stats['memory_used']:.2f}")
            st.metric("Memory Limit (MB)", f"{stats['memory_limit']:.2f}")
        else:
            error_msg("Failed to get container statistics")
    except Exception as e:
        error_msg(f"Failed to get container statistics: {str(e)}")

def display_container_actions(container_id, status, user):
    col1, col2, col3 = st.columns(3)

    with col1:
        if status != "running":
            if st.button("▶️ Start"):
                response = api_request("POST", f"/api/containers/{container_id}/start")
                if response and response.get("success"):
                    st.success("Container stopped successfully")
                    st.rerun()
                else:
                    error_msg("Failed to stop container")
        else:
            if st.button("⏹️ Stop"):
                response = api_request("POST", f"/api/containers/{container_id}/stop")
                if response and response.get("success"):
                    st.success("Container stopped successfully")
                    st.rerun()
                else:
                    error_msg("Failed to stop container")

    with col2:
        if st.button("🔄 Restart"):
            response = api_request("POST", f"/api/containers/{container_id}/restart")
            if response and response.get("success"):
                st.success("Container restarted successfully")
                st.rerun()
            else:
                error_msg("Failed to restart container")

    with col3:
        if st.button("🗑️ Remove"):
            response = api_request("POST", f"/api/containers/{container_id}/remove")
            if response and response.get("success"):
                port_manager = PortManager()
                new_ports = port_manager.deallocate_ports(user)
                st.success("Container removed successfully")
                st.rerun()
            else:
                error_msg("Failed to remove container")

def blue_header(text):
    st.markdown(f"<h3 style='color: blue;'> {text}</h3>", unsafe_allow_html=True)

def display_service_actions(container_id, user, page):
    port_manager = PortManager()
    port_range = port_manager.get_allocated_ports(user)

    ports = {
        "code_port_host": port_range["start_port"],
        "ssh_port_host": port_range["start_port"] + 1,
        "spice_port_host": port_range["start_port"] + 2,
        "fm_ui_port_host": port_range["start_port"] + 3,
        "fm_port_host": port_range["start_port"] + 4
    }

    container_info = api_request("GET", f"/api/containers/{container_id}")
    if not container_info or not container_info.get("success"):
        st.error("Failed to get container information")
        return

    container_ip = container_info["container"].get("NetworkSettings", {}).get("IPAddress") or "N/A"
    container_ip, publicip = get_machine_ip()

    if page == 'VS Code':
        url = f"http://{container_ip}:{ports['code_port_host']}"
        blue_header(url)
        webbrowser.open(url)

    elif page == 'SSH':
        cmd = f"ssh -p {ports['ssh_port_host']} root@{container_ip}"
        st.write("Run below command in putty or click below to download script")
        col0, col1 = st.columns(2)
        with col0:
            blue_header(cmd)
        with col1:
            if platform.system() == "Windows":
                st.download_button(label="📥 SSH", data=cmd, file_name="ssh.cmd", mime="application/bat")
            else:
                st.download_button(label="📥 SSH", data=cmd, file_name="ssh.sh", mime="application/bash")

    elif page == 'RDP':
        cmd = f"remote-viewer spice://{container_ip}:{ports['spice_port_host']}"
        st.write("Run below command in SPICE viewer or click below to download script")
        col0, col1 = st.columns(2)
        with col0:
            blue_header(cmd)
        with col1:
            if platform.system() == "Windows":
                st.download_button(label="📥 RDP", data=cmd, file_name="rdp.cmd", mime="application/bat")
            else:
                st.download_button(label="📥 RDP", data=cmd, file_name="rdp.sh", mime="application/bash")
    
    elif page == 'FM-UI':
        url = f"http://{container_ip}:{ports['fm_ui_port_host']}"
        blue_header(url)
        webbrowser.open(url)

    with st.sidebar.expander("### 🖥️ Desktop App"):
        system = platform.system().lower()
        if system == "windows":
            add_download_tools(
                "cxl-qvp_1.0.0.exe", 
                "📥 Windows Desktop App", 
                "static/downloads/cxl-qvp_1.0.0.exe", 
                "application/x-msdownload"
            )
        elif system == "linux":
            add_download_tools(
                "cxl-qvp_1.0.0_amd64.deb", 
                "📥 Linux .deb Package", 
                "static/downloads/cxl-qvp_1.0.0_amd64.deb", 
                "application/vnd.debian.binary-package"
            )

    with st.sidebar.expander("📡 Connection Info"):
        st.write(f"Container IP: {container_ip}")
        st.write("Default Ports:")
        for service, port in ports.items():
            service = service.replace("_port_host", "").upper()
            st.write(f"- {service} - {port}")

    with st.sidebar.expander("📥 Download Tools"):
        # Common tools
        add_download_tools("putty-64bit-0.82-installer.msi", "📥 Putty ", "static/downloads/putty-64bit-0.82-installer.msi", "application/msi")
        add_download_tools("virt-viewer-x64-11.0-1.0.msi", "📥 Spice Viewer ", "static/downloads/virt-viewer-x64-11.0-1.0.msi", "application/msi")
        add_download_tools("TRACE32.zip", "📥 TRACE32 ", "static/downloads/TRACE32.zip", "application/zip")
        
    
def add_download_tools(tool, label, path, mime):
    try:
        with open(path, "rb") as file:
            st.download_button(label=label, 
                            data=file, file_name=tool,
                                mime=mime)
    except Exception as e:                
        logger.warning(f"Failed setting up download {tool}")

def generate_user_hash(username: str) -> str:
    hash_obj = hashlib.sha256(username.encode())
    return hash_obj.hexdigest()[:16]

def render_page(user, session_token):
    st.set_page_config(page_title="QVP : CXL Remote Development", layout="wide")
    st.title("QVP : CXL Remote Development")

    with st.sidebar:        
        page = option_menu(
            menu_title=f'{user}',
            options=['Home', 'VS Code', 'SSH', 'RDP', "FM-UI"],
            icons=['house', 'braces-asterisk', 'terminal','pc-display-horizontal', 'hdd-network'],
            menu_icon='cast',
            default_index=0,
            styles={
                "container": {"padding": "0!important","background-color":'white'},
                "icon": {"color": "black", "font-size": "23px"},
                "nav-link-selected": {"background-color": "#02a2e8"},
                }
            )

    container_id = get_contianer_name(user)
    container_info = api_request("GET", f"/api/containers/{container_id}")

    if not container_info or not container_info.get("success"):
        st.info("No containers found")
        if st.button("▶️ Create"):
            create_start_container(user, session_token)
        return

    if page == 'Home':
        st.header("Available Instances")
        container_data = [{
            "Container ID": container_info["container"]["id"],
            "Name": container_info["container"]["name"],
            "Image": container_info["container"]["image"],
            "Status": container_info["container"]["status"],
            "Created": container_info["container"]["created"]
        }]

        df = pd.DataFrame(container_data)
        st.dataframe(df)

        st.header("Manage Instance")
        display_container_actions(container_id, container_info["container"]["status"] , user)

        if container_info["container"]["status"] == "running":
            display_container_stats(container_id)

    display_service_actions(container_id, user, page)

def get_contianer_name(user):
    name = f"code-server-{user}-{generate_user_hash(user)}"
    return name

def get_machine_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception as e:
        local_ip = "Could not determine local IP: " + str(e)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        public_ip = s.getsockname()[0]
        s.close()
    except Exception as e:
        public_ip = "Could not determine public IP: " + str(e)

    return local_ip, public_ip

def create_start_container(user, session_token):
    container_name = get_contianer_name(user)
    response = api_request("POST", "/api/containers", {
        "user": user,
        "session_token" : session_token
    })

    if response and response.get("success"):
        st.rerun()
    else:
        error_msg("Failed to start container")

def is_valid_session(remote_server_url, user_id, session_token):
    payload = {
        "user_id" : user_id,
        "session_token" : session_token
    }
    try:
        response = requests.post(
            f"{remote_server_url}/api/validate_session",
            json=payload,
            timeout=10
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"valid": False, "message": f"Request failed: {str(e)}"}

def main():
    load_dotenv("../.env", override=True)
    manager_ip = os.getenv("MGMT_SERVER_IP")
    manager_port = int(os.getenv("MGMT_SERVER_PORT")) + 1
    url = f"http://{manager_ip}:{manager_port}"

    query_params = st.query_params
    user_id = query_params.get("user")
    session_token = query_params.get("session_token")

    logger.info(f"Client manager new request : user = {user_id}, session = {session_token}")

    session = is_valid_session(url, user_id, session_token)
    if session.get("valid") == True:
        logger.success(f"Session is valid, rendering page...")
        render_page(user_id, session_token)
    else:
        st.error(f"Invalid session. {session.get('message', 'Please log in again.')}")
        logger.error(f"Invalid session. {session.get('message', 'Please log in again.')}")
        st.markdown(f'click [here] to login ({url})')

if __name__ == "__main__":
    main()
