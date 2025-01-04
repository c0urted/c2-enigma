import socket
import logging
import time
import random
import threading

# Configuration
HOST = '127.0.0.1'  # The server's IP address or hostname
PORT = 9000         # Port for the C2 server
HEARTBEAT_INTERVAL = 30  # Time in seconds between heartbeats

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variable to signal when to stop the client
stop_client = False

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

    # Create a socket object
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the server
        client.connect((HOST, PORT))
        logging.info(f"[+] Connected to {HOST}:{PORT}")

        # Receive CLIENT_ID and AUTH_TOKEN from the server
        response = client.recv(1024).decode('utf-8').strip()
        lines = response.split("\n")
        client_id = None
        auth_token = None

        for line in lines:
            if line.startswith("CLIENT_ID"):
                client_id = line.split(" ")[1]
            elif line.startswith("AUTH_TOKEN"):
                auth_token = line.split(" ")[1]

        if not client_id or not auth_token:
            logging.error("[-] Failed to receive valid CLIENT_ID or AUTH_TOKEN.")
            return

        logging.info(f"[+] Assigned CLIENT_ID: {client_id}")
        logging.info(f"[+] Received AUTH_TOKEN: {auth_token}")

        # Authenticate with the server
        client.sendall(f"AUTH {auth_token}".encode('utf-8'))
        auth_response = client.recv(1024).decode('utf-8').strip()

        if auth_response == "AUTH_SUCCESS":
            logging.info("[+] Authenticated successfully")
        else:
            logging.error("[-] Authentication failed")
            return

        # Start the heartbeat thread
        heartbeat_thread = threading.Thread(target=send_heartbeat, args=(client,))
        heartbeat_thread.daemon = True
        heartbeat_thread.start()

        # Main loop to pull commands from the server
        while True:
            # Receive commands from the server
            server_message = client.recv(1024).decode('utf-8').strip()
            logging.info(f"[SERVER] {server_message}")

            if server_message.startswith("CMD"):
                command = server_message.split(" ", 1)[1] if " " in server_message else ""
                logging.info(f"[+] Executing command: {command}")

                # Example: Respond back to the server after "executing" the command
                response = f"RESULT: Command '{command}' executed successfully"
                client.sendall(response.encode('utf-8'))

            elif server_message == "EXIT":
                logging.info("[+] Server requested disconnection")
                break

    except Exception as e:
        logging.error(f"[-] Error: {e}")
    finally:
        stop_client = True  # Signal the heartbeat thread to stop
        client.close()
        logging.info("[-] Connection closed")

if __name__ == "__main__":
    main()
