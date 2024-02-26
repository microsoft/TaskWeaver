class PortManager:
    def __init__(self, min_port, max_port, allocation_size=5):
        self.allocated_ports = {}
        self.allocation_size = allocation_size
        self.available_ports = set(range(min_port, max_port + 1, self.allocation_size))

    def allocate_ports(self, client_id: str) -> int:
        if len(self.available_ports) == 0:
            raise RuntimeError("Insufficient available ports")

        port = self.available_ports.pop()  # Allocate ports from the available pool
        self.allocated_ports[client_id] = port
        return port

    def reclaim_ports(self, client_id: str) -> None:
        if client_id in self.allocated_ports:
            port = self.allocated_ports[client_id]
            self.available_ports.add(port)  # Reclaim ports back to the available pool
            del self.allocated_ports[client_id]
        else:
            raise RuntimeError("Client ID not found in the allocated ports")

    def get_port_for_client(self, client_id: str):
        return self.allocated_ports.get(client_id, None)
