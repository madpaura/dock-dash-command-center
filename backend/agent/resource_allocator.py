import sqlite3
from loguru import logger

class PortManager:
    def __init__(self, db_path="port_manager.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Initialize the database and create the table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS port_allocations (
                    user_id TEXT PRIMARY KEY,
                    start_port INTEGER,
                    end_port INTEGER
                )
            ''')
            conn.commit()

    def allocate_ports(self, user_id, range_size=10):
        """Allocate a range of ports to a user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if the user already has allocated ports
            cursor.execute("SELECT * FROM port_allocations WHERE user_id = ?", (user_id,))
            if cursor.fetchone():
                logger.error(f"Ports already allocated for user {user_id}.")
                return self.get_allocated_ports(user_id)

            # Find the next available port range
            start_port = self._find_available_port_range(range_size)
            if start_port is None:
                logger.error("No available port range to allocate.")
                return None

            # Allocate the port range to the user
            end_port = start_port + range_size - 1
            cursor.execute('''
                INSERT INTO port_allocations (user_id, start_port, end_port)
                VALUES (?, ?, ?)
            ''', (user_id, start_port, end_port))
            conn.commit()

            logger.info(f"Port range allocated for user {user_id}: [{start_port}-{end_port}]")
            return {"start_port": start_port, "end_port": end_port}

    def deallocate_ports(self, user_id):
        """Deallocate the port range from a user and make it available for reuse."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if the user has allocated ports
            cursor.execute("SELECT * FROM port_allocations WHERE user_id = ?", (user_id,))
            user_ports = cursor.fetchone()
            if not user_ports:
                logger.error(f"No ports allocated for user {user_id}.")
                return False

            # Deallocate the port range
            cursor.execute("DELETE FROM port_allocations WHERE user_id = ?", (user_id,))
            conn.commit()

            logger.success(f"Port range deallocated for user {user_id}: [{user_ports[1]}-{user_ports[2]}]")
            return True

    def get_allocated_ports(self, user_id):
        """Get the allocated port range for a specific user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM port_allocations WHERE user_id = ?", (user_id,))
            user_ports = cursor.fetchone()
            if not user_ports:
                logger.error(f"No ports allocated for user {user_id}.")
                return None

            return {"start_port": user_ports[1], "end_port": user_ports[2]}

    def _get_allocated_port_ranges(self):
        """Get all currently allocated port ranges."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT start_port, end_port FROM port_allocations")
            return cursor.fetchall()

    def _find_available_port_range(self, range_size):
        """Find the next available port range of the specified size."""
        allocated_ranges = self._get_allocated_port_ranges()
        allocated_ranges.sort()  # Sort by start_port

        # Start searching from port 8000
        next_start_port = 9000

        for start_port, end_port in allocated_ranges:
            if next_start_port + range_size - 1 < start_port:
                # Found a gap large enough for the new range
                return next_start_port
            next_start_port = end_port + 1

        # Check if there's enough space after the last allocated range
        if next_start_port + range_size - 1 <= 65535:
            return next_start_port

        # No available range found
        return None
