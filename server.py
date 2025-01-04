import socket
import threading
import logging
import os

# Configuration
HOST = '0.0.0.0'  # Listen on all available interfaces
PORT = 9000       # Port for the C2 server
COUNTER_FILE = "client_counter.txt"
clients = []

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize client counter
client_counter = 0


def load_client_counter():
    """
    Load the client counter from a file.
    """
    global client_counter
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as file:
                client_counter = int(file.read().strip())
                logging.info(f"[+] Loaded client counter: {client_counter}")
        except Exception as e:
            logging.error(f"[-] Error reading client counter file: {e}")
            client_counter = 0
    else:
        logging.info("[+] No counter file found. Starting from 0.")


def save_client_counter():
    """
    Save the client counter to a file.
    """
    try:
        with open(COUNTER_FILE, "w") as file:
            file.write(str(client_counter))
            logging.info(f"[+] Saved client counter: {client_counter}")
    except Exception as e:
        logging.error(f"[-] Error saving client counter: {e}")


def process_command(data, addr, auth_token):
    """
    Processes incoming commands and returns the appropriate response.
    """
    command_parts = data.split(" ", 1)
    command = command_parts[0].upper()
    args = command_parts[1] if len(command_parts) > 1 else ""

    if command == "PING":
        return "PONG", auth_token
    elif command == "AUTH":
        if args == auth_token:
            return "AUTH_SUCCESS", auth_token
        else:
            return "AUTH_FAIL", auth_token
    elif command == "CMD":
        return f"EXECUTED: {args}", auth_token  # Replace with actual command execution logic
    elif command == "EXIT":
        return "GOODBYE", auth_token
    else:
        return "ERROR: UNKNOWN_COMMAND", auth_token


def handle_client(conn, addr):
    """
    Handles communication with a single client.
    """
    global client_counter
    logging.info(f"[+] New connection from {addr}")

    # Assign a unique client ID and token
    client_id = client_counter
    client_counter += 1
    auth_token = f"TOKEN-{client_id}"

    # Send client ID and auth token
    conn.sendall(f"CLIENT_ID {client_id}\nAUTH_TOKEN {auth_token}".encode('utf-8'))

    try:
        while True:
            data = conn.recv(1024).decode('utf-8').strip()
            if not data:
                break

            logging.info(f"[DATA] From {addr}: {data}")

            # Process the command
            response, auth_token = process_command(data, addr, auth_token)

            # Send the response back to the client
            conn.sendall(response.encode('utf-8'))

            if response == "GOODBYE":
                break
    except Exception as e:
        logging.error(f"[-] Error with {addr}: {e}")
    finally:
        clients.remove(conn)
        conn.close()
        logging.info(f"[-] Connection closed: {addr}")


def start_server():
    """
    Starts the server and listens for incoming connections.
    """
    global client_counter
    load_client_counter()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    logging.info(f"[+] Server started on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            clients.append(conn)
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        logging.info("[-] Server shutting down.")
        save_client_counter()
    finally:
        server.close()


if __name__ == "__main__":
    start_server()
