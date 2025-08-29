#!/usr/bin/env python3
"""
Docker Container PID Inspector and Killer

This script inspects a Docker container to find its PID and kills it.
Usage:
    python3 kill_container_by_pid.py <container_name_or_id>
    python3 kill_container_by_pid.py test-jupyter-baseurl
"""

import sys
import subprocess
import json
import signal
import os


def get_container_pid(container_name):
    """Get the PID of a Docker container."""
    try:
        # Use docker inspect to get container information
        result = subprocess.run(
            ['docker', 'inspect', container_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse JSON output
        container_info = json.loads(result.stdout)
        
        if not container_info:
            print(f"Container '{container_name}' not found")
            return None
            
        # Get the PID from the container info
        pid = container_info[0]['State']['Pid']
        
        if pid == 0:
            print(f"Container '{container_name}' is not running (PID is 0)")
            return None
            
        return pid
        
    except subprocess.CalledProcessError as e:
        print(f"Error inspecting container: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing docker inspect output: {e}")
        return None
    except KeyError as e:
        print(f"Error accessing PID from container info: {e}")
        return None


def kill_process(pid):
    """Kill a process by PID."""
    try:
        # Check if process exists
        os.kill(pid, 0)  # Signal 0 just checks if process exists
        
        print(f"Killing process with PID {pid}...")
        
        # Try graceful termination first
        os.kill(pid, signal.SIGTERM)
        
        # Wait a moment for graceful shutdown
        import time
        time.sleep(2)
        
        # Check if process still exists
        try:
            os.kill(pid, 0)
            print(f"Process {pid} still running, forcing kill...")
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            print(f"Process {pid} terminated gracefully")
            
    except ProcessLookupError:
        print(f"Process with PID {pid} does not exist")
    except PermissionError:
        print(f"Permission denied: Cannot kill process {pid} (try running as root)")
    except Exception as e:
        print(f"Error killing process {pid}: {e}")


def inspect_container_details(container_name):
    """Show detailed container information including PID."""
    try:
        result = subprocess.run(
            ['docker', 'inspect', container_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        container_info = json.loads(result.stdout)[0]
        
        print(f"\n=== Container Details: {container_name} ===")
        print(f"Container ID: {container_info['Id'][:12]}")
        print(f"Name: {container_info['Name']}")
        print(f"Status: {container_info['State']['Status']}")
        print(f"Running: {container_info['State']['Running']}")
        print(f"PID: {container_info['State']['Pid']}")
        print(f"Started At: {container_info['State']['StartedAt']}")
        
        if container_info['State']['Running']:
            print(f"Image: {container_info['Config']['Image']}")
            
        return container_info['State']['Pid']
        
    except Exception as e:
        print(f"Error getting container details: {e}")
        return None


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 kill_container_by_pid.py <container_name_or_id>")
        print("Example: python3 kill_container_by_pid.py test-jupyter-baseurl")
        sys.exit(1)
    
    container_name = sys.argv[1]
    
    # Show container details first
    pid = inspect_container_details(container_name)
    
    if pid is None or pid == 0:
        print(f"Cannot get valid PID for container '{container_name}'")
        sys.exit(1)
    
    # Kill the process
    kill_process(pid)
    
    print(f"\nOperation completed for container '{container_name}'")


if __name__ == "__main__":
    main()
