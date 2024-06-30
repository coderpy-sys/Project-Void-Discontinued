import subprocess
import threading

def start_process(script_name):
    return subprocess.Popen(["python3", script_name])

def monitor_process(script_name):
    while True:
        process = start_process(script_name)
        process.wait()
        print(f"{script_name} crashed. Restarting...")

if __name__ == "__main__":
    main_thread = threading.Thread(target=monitor_process, args=("main.py",))
    backup_thread = threading.Thread(target=monitor_process, args=("auto_backup.py",))
    
    main_thread.start()
    backup_thread.start()

    try:
        main_thread.join()
        backup_thread.join()
    except KeyboardInterrupt:
        print("Processes terminated.")
