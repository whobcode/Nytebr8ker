from modules import check, banner, control
from colorama import Back, Fore, Style
import random
import time
from datetime import datetime

def log_event(event):
    with open("server.log", "a") as f:
        f.write(f"{datetime.now()} - {event}\n")

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

