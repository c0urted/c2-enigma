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
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.log(f"Server started on {self.host}:{self.port}")

        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                with self.lock:
                    self.client_counter += 1
                    client_id = self.client_counter

                # Initialize client entry
                self.clients[client_id] = {
                    "socket": client_socket,
                    "address": client_address,
                    "last_heartbeat": time.time(),
                    "authenticated": False,
                    "active": True,
                }
                self.log(f"Client {client_id} ({client_address}) CONNECTED")
                threading.Thread(
                    target=self.handle_client, args=(client_id,), daemon=True
                ).start()

        except KeyboardInterrupt:
            self.log("Shutting down server...")
        finally:
            self.server_socket.close()

    def handle_client(self, client_id):
        client = self.clients[client_id]
        client_socket = client["socket"]
        client_address = client["address"]

        try:
            # Send initial authentication message with client ID
            auth_message = f"CLIENT_ID {client_id}\nAUTH_TOKEN PLACEHOLDER_TOKEN\n"
            client_socket.sendall(auth_message.encode("utf-8"))

            while client["active"]:
                try:
                    message = client_socket.recv(1024).decode("utf-8").strip()
                    if not message:
                        break

                    if message == "HEARTBEAT":
                        client["last_heartbeat"] = time.time()
                        self.log(f"Client {client_id} ({client_address}) HEARTBEAT received")

                    elif message.startswith("AUTH"):
                        _, auth_token = message.split(maxsplit=1)
                        if auth_token == "PLACEHOLDER_TOKEN":  # Replace with real validation
                            client["authenticated"] = True
                            client_socket.sendall("AUTH_SUCCESS\n".encode("utf-8"))
                            self.log(f"Client {client_id} ({client_address}) AUTHENTICATED")
                        else:
                            client_socket.sendall("AUTH_FAIL\n".encode("utf-8"))

                    elif message == "EXIT":
                        self.log(f"Client {client_id} ({client_address}) DISCONNECTED")
                        break

                    else:
                        response = "UNKNOWN_COMMAND\n"
                        client_socket.sendall(response.encode("utf-8"))

                except socket.timeout:
                    continue

                # Check for heartbeat timeout
                if time.time() - client["last_heartbeat"] > HEARTBEAT_INTERVAL:
                    self.log(f"Client {client_id} ({client_address}) HEARTBEAT_TIMEOUT")
                    break

        except Exception as e:
            self.log(f"Error with client {client_id}: {e}")

        finally:
            # Clean up client
            with self.lock:
                client["active"] = False
                client_socket.close()
                del self.clients[client_id]
            self.log(f"Client {client_id} ({client_address}) DISCONNECTED")

if __name__ == "__main__":
    server = C2Server(HOST, PORT)
    server.start()
