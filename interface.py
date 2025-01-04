import socket
import logging
import time
from colorama import Fore, Style, init  # For color-coded feedback

# This serves as the operator panel for managing clients and sending commands
# 
# PLANNED:
# command logging for other operators
# better auth lol

# Initialize colorama
init(autoreset=True)

# Configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9000

# Authentication credentials (placeholder)
USERNAME = "admin"
PASSWORD = "password123"

# Function to display available commands
def show_commands():
    commands = {
        "LIST": "List all connected clients.",
        "COMMAND <CLIENT_ID/all> <COMMAND>": "Send a command to a specific client or broadcast to all.",
        "STATUS <CLIENT_ID>": "Get the status of a specific client.",
        "SCHEDULE <CLIENT_ID/all> <COMMAND> <SECONDS>": "Schedule a command to run after a delay.",
        "EXIT": "Exit the interface."
    }
    print(Fore.CYAN + "\n=== Available Commands ===")
    for cmd, desc in commands.items():
        print(f"{Fore.CYAN}{cmd:<40} - {desc}")
    print()

# Operator authentication
def authenticate():
    print(Fore.CYAN + "=== Operator Login ===")
    attempts = 3
    while attempts > 0:
        username = input("Username: ")
        password = input("Password: ")
        if username == USERNAME and password == PASSWORD:
            print(Fore.GREEN + "[+] Authentication successful!")
            return True
        else:
            attempts -= 1
            print(Fore.RED + f"[-] Invalid credentials. Attempts remaining: {attempts}")
    return False

# Send a command to the server
def send_command(sock):
    target = input("Enter target (CLIENT_ID or 'all'): ")
    command = input("Enter command: ")
    sock.sendall(f"COMMAND {target} {command}".encode("utf-8"))
    response = sock.recv(1024).decode("utf-8")
    print(Fore.GREEN + f"Server Response: {response}")

# Schedule a command
def schedule_command(sock):
    target = input("Enter target (CLIENT_ID or 'all'): ")
    command = input("Enter command: ")
    delay = int(input("Enter delay in seconds: "))
    print(Fore.YELLOW + f"Scheduling command '{command}' for {target} in {delay} seconds...")
    time.sleep(delay)
    sock.sendall(f"COMMAND {target} {command}".encode("utf-8"))
    response = sock.recv(1024).decode("utf-8")
    print(Fore.GREEN + f"Server Response: {response}")

# Main interface loop
def main():
    if not authenticate():
        print(Fore.RED + "[-] Authentication failed. Exiting.")
        return

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_HOST, SERVER_PORT))
        print(Fore.GREEN + f"[+] Connected to server at {SERVER_HOST}:{SERVER_PORT}")

        while True:
            print(Fore.CYAN + "\n=== Interface Options ===")
            print("1. List available commands")
            print("2. Send a command")
            print("3. Schedule a command")
            print("4. Exit")
            choice = input("Select an option: ")

            if choice == "1":
                show_commands()
            elif choice == "2":
                send_command(sock)
            elif choice == "3":
                schedule_command(sock)
            elif choice == "4":
                print(Fore.CYAN + "Exiting interface...")
                sock.sendall("EXIT".encode("utf-8"))
                break
            else:
                print(Fore.RED + "[-] Invalid choice. Please try again.")

    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        sock.close()
        print(Fore.CYAN + "[-] Disconnected from server.")

if __name__ == "__main__":
    main()
