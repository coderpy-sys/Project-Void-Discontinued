import subprocess
import time

def start_main():
    process = subprocess.Popen(["python", "main.py"])
    return process

def monitor():
    process = start_main()
    while True:
        try:
            exit_code = process.wait()
            if exit_code != 0:
                print(f"main.py crashed with exit code {exit_code}. Restarting...")
                process = start_main()
            else:
                print("main.py exited successfully.")
                break
        except Exception as e:
            print(f"An error occurred: {e}")
            process = start_main()

if __name__ == "__main__":
    monitor()
