import socket
import logging
import time
import json
import threading
import os

# Configuration
HOST = '127.0.0.1'  # The server's IP address or hostname
PORT = 9000         # Port for the C2 server
HEARTBEAT_INTERVAL = 30  # Time in seconds between heartbeats
CLIENT_DATA_FILE = "client_data.json"  # File to store client ID and authentication info

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

stop_client = False  # Global flag to stop the client gracefully


def load_client_data():
    """
    Loads the client ID and authentication data from a local file.
    """
    if os.path.exists(CLIENT_DATA_FILE):
        with open(CLIENT_DATA_FILE, "r") as f:
            return json.load(f)
    return None


def save_client_data(client_id):
    """
    Saves the client ID to a local file for persistence.
    """
    data = {
        "client_id": client_id,
        "created_at": time.strftime("%m/%d/%Y")
    }
    with open(CLIENT_DATA_FILE, "w") as f:
        json.dump(data, f)


def send_heartbeat(client_socket):
    """
    Sends periodic heartbeat messages to the server.
    """
    while not stop_client:
        try:
            client_socket.sendall("HEARTBEAT".encode('utf-8'))
            time.sleep(HEARTBEAT_INTERVAL)
        except Exception as e:
            logging.error(f"[-] Heartbeat error: {e}")
            break


def main():
    global stop_client

    # Load existing client ID if available
    client_data = load_client_data()
    existing_client_id = client_data["client_id"] if client_data else None

    # Create a socket object
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((HOST, PORT))
        logging.info(f"[+] Connected to {HOST}:{PORT}")

        if existing_client_id:
            logging.info(f"[+] Using existing CLIENT_ID: {existing_client_id}")
            client_id = existing_client_id
        else:
            # Receive new CLIENT_ID from the server
            response = client.recv(1024).decode('utf-8').strip()
            lines = response.split("\n")
            client_id = None

            for line in lines:
                if line.startswith("CLIENT_ID"):
                    client_id = line.split(" ")[1]

            if not client_id:
                logging.error("[-] Failed to receive valid CLIENT_ID.")
                return

            logging.info(f"[+] Assigned new CLIENT_ID: {client_id}")
            save_client_data(client_id)  # Save client ID for future use

        # Start the heartbeat thread
        heartbeat_thread = threading.Thread(target=send_heartbeat, args=(client,))
        heartbeat_thread.daemon = True
        heartbeat_thread.start()

        while True:
            server_message = client.recv(1024).decode('utf-8').strip()
            logging.info(f"[SERVER] {server_message}")

            if server_message.startswith("CMD"):
                command = server_message.split(" ", 1)[1] if " " in server_message else ""
                logging.info(f"[+] Executing command: {command}")
                response = f"RESULT: Command '{command}' executed successfully"
                client.sendall(response.encode('utf-8'))

            elif server_message == "EXIT":
                logging.info("[+] Server requested disconnection")
                break

    except Exception as e:
        logging.error(f"[-] Error: {e}")
    finally:
        stop_client = True
        client.close()
        logging.info("[-] Connection closed")


if __name__ == "__main__":
    main()
