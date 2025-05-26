#!/usr/bin/env python3

from modules import check, banner, control
from colorama import Back, Fore, Style
import random
import time
from datetime import datetime
import subprocess
import os

# Define paths
LOG_FILE = "/opt/Storm-breaker/logs/stormctl.log"
NGINX_CONF_SOURCE = "/opt/Storm-breaker/conf/myapp-nginx.conf"
NGINX_CONF_TARGET = "/opt/bitnami/nginx/conf/bitnami/myapp.conf"
NGINX_BIN = "/opt/bitnami/nginx/sbin/nginx"

# Ensure directories exist
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(os.path.dirname(NGINX_CONF_SOURCE), exist_ok=True)

def log_event(event):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()} - {event}\n")

def start_nginx():
    subprocess.run(["sudo", NGINX_BIN])
    print("NGINX started.")

def stop_nginx():
    subprocess.run(["sudo", NGINX_BIN, "-s", "stop"])
    print("NGINX stopped.")

def restart_nginx():
    subprocess.run(["sudo", NGINX_BIN, "-s", "reload"])
    print("NGINX reloaded.")

def configure_nginx_reverse_proxy(port):
    config = f'''
server {{
    listen 80;
    server_name localhost;

    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
'''
    with open(NGINX_CONF_SOURCE, "w") as f:
        f.write(config)
    print(f"NGINX reverse proxy configured to port {port}")
    log_event(f"NGINX configured for reverse proxy to port {port}")

    # Ensure NGINX reads it
    if not os.path.islink(NGINX_CONF_TARGET):
        subprocess.run(["sudo", "ln", "-sf", NGINX_CONF_SOURCE, NGINX_CONF_TARGET])
        print("Linked custom NGINX config into active directory.")


def main():
    check.dependency()
    check.check_started()
    check.check_update()

    MAX_RUNTIME = 300  # seconds (5 minutes)
    server_running = False
    current_port = None
    start_time = None

    while True:
        banner.banner()
        print("\nOptions:")
        print("[1] Start server on custom port")
        print("[2] Start server on random port")
        print("[3] Stop server")
        print("[4] Check server status")
        print("[5] Check for updates")
        print("[6] Start NGINX")
        print("[7] Stop NGINX")
        print("[8] Configure NGINX Reverse Proxy")
        print("[9] Restart NGINX")
        print("[0] Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            if not server_running:
                try:
                    custom_port = int(input("Enter the port number (1024-65535): "))
                    if 1024 <= custom_port <= 65535:
                        current_port = custom_port
                        control.run_php_server(current_port)
                        log_event(f"Server started on port {current_port}")
                        server_running = True
                        start_time = time.time()
                    else:
                        print("Invalid port. Choose between 1024 and 65535.")
                except ValueError:
                    print("Invalid input. Please enter a numeric port.")
            else:
                print("Server is already running.")

        elif choice == "2":
            if not server_running:
                current_port = random.randint(2000, 9000)
                control.run_php_server(current_port)
                log_event(f"Server started on random port {current_port}")
                server_running = True
                start_time = time.time()
            else:
                print("Server is already running.")

        elif choice == "3":
            if server_running:
                control.kill_php_proc()
                log_event(f"Server manually stopped on port {current_port}")
                server_running = False
            else:
                print("Server is not running.")

        elif choice == "4":
            control.check_server_status()

        elif choice == "5":
            check.check_update()

        elif choice == "6":
            start_nginx()

        elif choice == "7":
            stop_nginx()

        elif choice == "8":
            if current_port:
                configure_nginx_reverse_proxy(current_port)
            else:
                print("Start the server first to configure NGINX proxy.")

        elif choice == "9":
            restart_nginx()

        elif choice == "0":
            if server_running:
                control.kill_php_proc()
                log_event(f"Server stopped on exit from port {current_port}")
            print("Exiting...")
            break

        else:
            print("Invalid choice.")

        if server_running and (time.time() - start_time > MAX_RUNTIME):
            print("\nAuto shutdown: Maximum runtime reached.")
            control.kill_php_proc()
            log_event(f"Server auto-stopped after {MAX_RUNTIME} seconds")
            server_running = False

        if server_running:
            try:
                input(" " + Fore.WHITE + Back.RED + "Press Enter or CTRL+C to stop localhost " + Style.RESET_ALL)
                control.kill_php_proc()
                log_event(f"Server manually stopped on port {current_port}")
                server_running = False
            except KeyboardInterrupt:
                print("\n" + Fore.YELLOW + "Shutdown requested. Stopping server..." + Style.RESET_ALL)
                control.kill_php_proc()
                log_event(f"Server stopped via KeyboardInterrupt on port {current_port}")
                server_running = False
            except Exception as e:
                print("Server crashed. Restarting...", e)
                control.kill_php_proc()
                log_event(f"Server crashed with error: {e}")
                server_running = False
            finally:
                print(Fore.GREEN + "Localhost server stopped." + Style.RESET_ALL)

if __name__ == "__main__":
    main()

