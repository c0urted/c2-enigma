import socket
import threading
import time
import logging

# Server configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 9000       # Port for the C2 server
HEARTBEAT_INTERVAL = 60  # Time in seconds before a client is considered timed out

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class C2Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = {}  # Tracks clients by their ID
        self.client_counter = 0
        self.lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def log(self, message):
        logging.info(message)

    def start(self):
        """ Starts the server and listens for incoming client connections. """
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.log(f"Server started on {self.host}:{self.port}")

        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                threading.Thread(
                    target=self.handle_client, args=(client_socket, client_address), daemon=True
                ).start()

        except KeyboardInterrupt:
            self.log("Shutting down server...")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket, client_address):
        """
        Handles a client connection, verifying or assigning a CLIENT_ID.
        """
        client_id = None
        try:
            # Ask client for its ID (new clients won't have one)
            client_socket.sendall(b"REQUEST_CLIENT_ID\n")
            client_response = client_socket.recv(1024).decode("utf-8").strip()

            if client_response.startswith("CLIENT_ID"):
                requested_id = int(client_response.split(" ")[1])
                if requested_id in self.clients:
                    client_id = requested_id  # Reuse existing client ID
                else:
                    self.log(f"Unknown CLIENT_ID {requested_id}, assigning new ID.")

            if client_id is None:  # Assign new ID if needed
                with self.lock:
                    self.client_counter += 1
                    client_id = self.client_counter

            # Store client data
            self.clients[client_id] = {
                "socket": client_socket,
                "address": client_address,
                "last_heartbeat": time.time(),
                "authenticated": False,
                "active": True,
            }

            # Send assigned/verified ID back to the client
            client_socket.sendall(f"CLIENT_ID {client_id}\n".encode("utf-8"))
            self.log(f"Client {client_id} ({client_address}) CONNECTED")

            while self.clients[client_id]["active"]:
                try:
                    message = client_socket.recv(1024).decode("utf-8").strip()
                    if not message:
                        break

                    if message == "HEARTBEAT":
                        self.clients[client_id]["last_heartbeat"] = time.time()
                        self.log(f"Client {client_id} ({client_address}) HEARTBEAT received")

                    elif message.startswith("EXIT"):
                        self.log(f"Client {client_id} ({client_address}) DISCONNECTED")
                        break

                except socket.timeout:
                    continue

                # Check for heartbeat timeout
                if time.time() - self.clients[client_id]["last_heartbeat"] > HEARTBEAT_INTERVAL:
                    self.log(f"Client {client_id} ({client_address}) HEARTBEAT_TIMEOUT")
                    break

        except Exception as e:
            self.log(f"Error with client {client_id}: {e}")

        finally:
            with self.lock:
                if client_id in self.clients:
                    self.clients[client_id]["active"] = False
                    client_socket.close()
                    del self.clients[client_id]
            self.log(f"Client {client_id} ({client_address}) DISCONNECTED")


if __name__ == "__main__":
    server = C2Server(HOST, PORT)
    server.start()
