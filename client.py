import socket
import logging
import time
import threading

# Configuration
HOST = 'localhost'  # Replace with the server's IP address or hostname
PORT = 9000         # Port for the C2 server
HEARTBEAT_INTERVAL = 10  # Seconds

# Logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def send_heartbeat(client_socket):
    """
    Periodically send heartbeat signals to the server.
    """
    while True:
        try:
            client_socket.sendall("HEARTBEAT".encode('utf-8'))
            logging.debug("[+] Sent HEARTBEAT to server.")
        except Exception as e:
            logging.error(f"[-] Failed to send HEARTBEAT: {e}")
            break
        time.sleep(HEARTBEAT_INTERVAL)


def parse_server_response(response):
    """
    Parse the server's initial response to extract CLIENT_ID and AUTH_TOKEN.
    
    :param response: The raw response string from the server
    :return: Tuple of (client_id, auth_token) or (None, None) if parsing fails
    """
    logging.debug(f"Parsing server response: {response}")
    lines = response.split("\n")
    client_id = None
    auth_token = None

    for line in lines:
        if line.startswith("CLIENT_ID"):
            try:
                client_id = line.split(" ")[1]
            except IndexError:
                logging.error("[-] CLIENT_ID format is invalid.")
        elif line.startswith("AUTH_TOKEN"):
            try:
                auth_token = line.split(" ")[1]
            except IndexError:
                logging.error("[-] AUTH_TOKEN format is invalid.")

    return client_id, auth_token


def main():
    while True:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            logging.info("[+] Connecting to server...")
            client.connect((HOST, PORT))
            logging.info(f"[+] Connected to {HOST}:{PORT}")

            # Receive initial response with CLIENT_ID and AUTH_TOKEN
            response = client.recv(1024).decode('utf-8').strip()
            logging.debug(f"Raw server response: {response}")

            client_id, auth_token = parse_server_response(response)

            if not client_id or not auth_token:
                logging.error("[-] Failed to receive valid CLIENT_ID or AUTH_TOKEN.")
                client.close()
                time.sleep(5)  # Retry after delay
                continue

            logging.info(f"[+] Assigned CLIENT_ID: {client_id}")
            logging.info(f"[+] Received AUTH_TOKEN: {auth_token}")

            # Send AUTH command
            client.sendall(f"AUTH {auth_token}".encode('utf-8'))
            auth_response = client.recv(1024).decode('utf-8').strip()
            logging.debug(f"Authentication response: {auth_response}")

            if auth_response != "AUTH_SUCCESS":
                logging.error("[-] Authentication failed.")
                client.close()
                time.sleep(5)  # Retry after delay
                continue

            logging.info("[+] Authentication successful. Entering session loop.")

            # Start the heartbeat thread
            heartbeat_thread = threading.Thread(target=send_heartbeat, args=(client,), daemon=True)
            heartbeat_thread.start()

            # Simple session loop
            while True:
                command = input("Enter a command (or 'exit' to quit): ")
                if command.lower() == "exit":
                    client.sendall("EXIT".encode('utf-8'))
                    break

                client.sendall(command.encode('utf-8'))
                response = client.recv(1024).decode('utf-8').strip()
                logging.info(f"[RESPONSE] {response}")

        except Exception as e:
            logging.error(f"[-] Error occurred: {e}")
            time.sleep(5)  # Retry after delay

        finally:
            client.close()
            logging.info("[-] Connection closed.")


if __name__ == "__main__":
    main()
