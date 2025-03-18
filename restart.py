"""
Restart script for Timetable application
This script will:
1. Stop any running Flask processes
2. Clear the Flask session data
3. Restart the server
"""
import os
import sys
import subprocess
import time
import signal
import platform

def kill_flask_process():
    """Kill any running Flask processes"""
    print("Stopping any running Flask processes...")
    
    if platform.system() == "Windows":
        # Windows approach
        try:
            os.system("taskkill /f /im python.exe")
            print("Flask processes stopped")
        except:
            print("No Flask processes found or unable to stop them")
    else:
        # Linux/Mac approach
        try:
            pid_cmd = "lsof -i:5000 -t"
            process = subprocess.Popen(pid_cmd, shell=True, stdout=subprocess.PIPE)
            pid = process.stdout.read().decode().strip()
            
            if pid:
                os.kill(int(pid), signal.SIGTERM)
                print(f"Process {pid} stopped")
            else:
                print("No Flask process found on port 5000")
        except:
            print("No Flask processes found or unable to stop them")

def clear_session_data():
    """Clear Flask session data"""
    print("Clearing session data...")
    if os.path.exists("flask_session"):
        for file in os.listdir("flask_session"):
            try:
                os.remove(os.path.join("flask_session", file))
            except:
                print(f"Unable to remove session file: {file}")

def restart_server():
    """Restart the Flask server"""
    print("Starting Flask server...")
    if platform.system() == "Windows":
        subprocess.Popen("start cmd /k run.bat", shell=True)
    else:
        subprocess.Popen("python -m flask run", shell=True)
    
    print("\nServer restarting! Please wait a moment and refresh your browser.")

if __name__ == "__main__":
    kill_flask_process()
    time.sleep(1)
    clear_session_data()
    time.sleep(1)
    restart_server() 