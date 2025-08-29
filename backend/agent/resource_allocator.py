import json
import os
from typing import Dict, Optional, List, Tuple
from loguru import logger

class PortManager:
    def __init__(self, config_file="port_allocations.json", settings_file="port_settings.json"):
        self.config_file = config_file
        self.settings_file = settings_file
        self._initialize_files()

    def _initialize_files(self):
        """Initialize the JSON files if they don't exist."""
        # Initialize port allocations file
        if not os.path.exists(self.config_file):
            initial_data = {
                "allocations": {},
                "metadata": {
                    "created_at": "2025-08-29T10:36:48+05:30",
                    "last_updated": "2025-08-29T10:36:48+05:30",
                    "version": "1.0"
                }
            }
            self._write_json(self.config_file, initial_data)
            logger.info(f"Created port allocations file: {self.config_file}")
        
        # Initialize settings file
        if not os.path.exists(self.settings_file):
            settings_data = {
                "port_range": {
                    "start": 9000,
                    "end": 65535,
                    "default_range_size": 10
                },
                "metadata": {
                    "description": "Port allocation settings for container services",
                    "version": "1.0"
                }
            }
            self._write_json(self.settings_file, settings_data)
            logger.info(f"Created port settings file: {self.settings_file}")

    def _read_json(self, file_path: str) -> Dict:
        """Read and parse JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error reading {file_path}: {e}")
            return {}

    def _write_json(self, file_path: str, data: Dict) -> bool:
        """Write data to JSON file."""
        try:
            # Update metadata timestamp
            if "metadata" in data:
                data["metadata"]["last_updated"] = "2025-08-29T10:36:48+05:30"
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error writing to {file_path}: {e}")
            return False

    def _get_settings(self) -> Dict:
        """Get port allocation settings."""
        settings = self._read_json(self.settings_file)
        return settings.get("port_range", {
            "start": 9000,
            "end": 65535,
            "default_range_size": 10
        })

    def allocate_ports(self, user_id: str, range_size: Optional[int] = None) -> Optional[Dict[str, int]]:
        """Allocate a range of ports to a user."""
        if range_size is None:
            settings = self._get_settings()
            range_size = settings.get("default_range_size", 10)
        
        data = self._read_json(self.config_file)
        allocations = data.get("allocations", {})
        
        # Check if the user already has allocated ports
        if user_id in allocations:
            logger.error(f"Ports already allocated for user {user_id}.")
            return self.get_allocated_ports(user_id)
        
        # Find the next available port range
        start_port = self._find_available_port_range(range_size)
        if start_port is None:
            logger.error("No available port range to allocate.")
            return None
        
        # Allocate the port range to the user
        end_port = start_port + range_size - 1
        allocations[user_id] = {
            "start_port": start_port,
            "end_port": end_port,
            "range_size": range_size,
            "allocated_at": "2025-08-29T10:36:48+05:30"
        }
        
        data["allocations"] = allocations
        if self._write_json(self.config_file, data):
            logger.info(f"Port range allocated for user {user_id}: [{start_port}-{end_port}]")
            return {"start_port": start_port, "end_port": end_port}
        else:
            logger.error(f"Failed to save port allocation for user {user_id}")
            return None

    def deallocate_ports(self, user_id: str) -> bool:
        """Deallocate the port range from a user and make it available for reuse."""
        data = self._read_json(self.config_file)
        allocations = data.get("allocations", {})
        
        # Check if the user has allocated ports
        if user_id not in allocations:
            logger.error(f"No ports allocated for user {user_id}.")
            return False
        
        user_ports = allocations[user_id]
        start_port = user_ports["start_port"]
        end_port = user_ports["end_port"]
        
        # Deallocate the port range
        del allocations[user_id]
        data["allocations"] = allocations
        
        if self._write_json(self.config_file, data):
            logger.success(f"Port range deallocated for user {user_id}: [{start_port}-{end_port}]")
            return True
        else:
            logger.error(f"Failed to deallocate ports for user {user_id}")
            return False

    def get_allocated_ports(self, user_id: str) -> Optional[Dict[str, int]]:
        """Get the allocated port range for a specific user."""
        data = self._read_json(self.config_file)
        allocations = data.get("allocations", {})
        
        if user_id not in allocations:
            logger.error(f"No ports allocated for user {user_id}.")
            return None
        
        user_ports = allocations[user_id]
        return {
            "start_port": user_ports["start_port"],
            "end_port": user_ports["end_port"]
        }

    def _get_allocated_port_ranges(self) -> List[Tuple[int, int]]:
        """Get all currently allocated port ranges."""
        data = self._read_json(self.config_file)
        allocations = data.get("allocations", {})
        
        ranges = []
        for user_data in allocations.values():
            ranges.append((user_data["start_port"], user_data["end_port"]))
        
        return ranges

    def _find_available_port_range(self, range_size: int) -> Optional[int]:
        """Find the next available port range of the specified size."""
        settings = self._get_settings()
        min_port = settings.get("start", 9000)
        max_port = settings.get("end", 65535)
        
        allocated_ranges = self._get_allocated_port_ranges()
        allocated_ranges.sort()  # Sort by start_port
        
        next_start_port = min_port
        
        for start_port, end_port in allocated_ranges:
            if next_start_port + range_size - 1 < start_port:
                # Found a gap large enough for the new range
                return next_start_port
            next_start_port = end_port + 1
        
        # Check if there's enough space after the last allocated range
        if next_start_port + range_size - 1 <= max_port:
            return next_start_port
        
        # No available range found
        return None
    
    def get_all_allocations(self) -> Dict[str, Dict]:
        """Get all port allocations for debugging/monitoring."""
        data = self._read_json(self.config_file)
        return data.get("allocations", {})
    
    def get_allocation_summary(self) -> Dict:
        """Get summary of port allocations."""
        data = self._read_json(self.config_file)
        allocations = data.get("allocations", {})
        settings = self._get_settings()
        
        total_users = len(allocations)
        total_ports_allocated = sum(
            alloc["range_size"] for alloc in allocations.values()
        )
        
        port_range = settings.get("end", 65535) - settings.get("start", 9000) + 1
        utilization = (total_ports_allocated / port_range) * 100 if port_range > 0 else 0
        
        return {
            "total_users": total_users,
            "total_ports_allocated": total_ports_allocated,
            "port_range_size": port_range,
            "utilization_percent": round(utilization, 2),
            "available_ports": port_range - total_ports_allocated
        }
