import subprocess
import time

def start_process(script_name):
    return subprocess.Popen(["python3", script_name])

def monitor_process(main_process, backup_process):
    while True:
        if main_process.poll() is not None:
            print("main.py crashed. Restarting...")
            main_process = start_process("main.py")
        
        if backup_process.poll() is not None:
            print("auto_backup.py crashed. Not restarting...")
            backup_process = None

        time.sleep(5)

if __name__ == "__main__":
    main_process = start_process("main.py")
    backup_process = start_process("auto_backup.py")

    try:
        monitor_process(main_process, backup_process)
    except KeyboardInterrupt:
        main_process.terminate()
        if backup_process is not None:
            backup_process.terminate()
        print("Processes terminated.")
