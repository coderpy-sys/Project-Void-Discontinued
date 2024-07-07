import subprocess
import threading
import time

BLUE = "\033[94m"
RESET = "\033[0m"

def start_process(script_name):
    return subprocess.Popen(["python3", script_name])

def monitor_main():
    while True:
        process = start_process("main.py")
        process.wait()
        print(f"{BLUE}INFO:{RESET} main.py crashed. Restarting...")

def run_backup():
    while True:
        process = start_process("auto_backup.py")
        process.wait()
        print(f"{BLUE}INFO:{RESET} auto_backup.py finished. Next run in 30 minutes.")
        time.sleep(1800)  

if __name__ == "__main__":
    main_thread = threading.Thread(target=monitor_main)
    backup_thread = threading.Thread(target=run_backup)
    
    main_thread.start()
    backup_thread.start()

    try:
        main_thread.join()
        backup_thread.join()
    except KeyboardInterrupt:
        print(f"{BLUE}INFO:{RESET} Processes terminated.")