import os
import subprocess
import sys
import signal
from threading import Thread
import time
import webbrowser

def run_django():
    """Run the Django development server for HTTP requests"""
    print("Starting Django development server...")
    django_cmd = ["python", "manage.py", "runserver", "0.0.0.0:8000"]
    return subprocess.Popen(django_cmd)

def run_daphne():
    """Run Daphne server for WebSocket connections only"""
    print("Starting Daphne server for WebSocket connections...")
    daphne_cmd = ["daphne", "-b", "0.0.0.0", "-p", "8001", "strategy_game.asgi:application"]
    return subprocess.Popen(daphne_cmd)

def run_tailwind():
    """Run Tailwind CSS compiler"""
    print("Starting Tailwind CSS compiler...")
    subprocess.run(["python", "manage.py", "tailwind", "install"], check=True)
    subprocess.run(["python", "manage.py", "tailwind", "build"], check=True)
    tailwind_cmd = ["python", "manage.py", "tailwind", "start"]
    return subprocess.Popen(tailwind_cmd)

def run_venv():
    """Activate the virtual environment"""
    print("Activating virtual environment...")
    venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'Scripts', 'activate.bat')
    if os.path.exists(venv_path):
        return subprocess.Popen([venv_path])
    else:
        print("Virtual environment not found. Please create it first.")
        sys.exit(1)

def main():
    print("Starting development servers...")
    
    processes = []
    try:
        venv_process = run_venv()
        time.sleep(2)
        processes.append(venv_process)
        
        tailwind_process = run_tailwind()
        processes.append(tailwind_process)
        time.sleep(2)

        django_process = run_django()
        processes.append(django_process)

        daphne_process = run_daphne()
        processes.append(daphne_process)
        
        print("\nDevelopment servers are running!")
        print("Django server (HTTP): http://localhost:8000")
        print("Daphne server (WebSocket): ws://localhost:8001")
        print("\nPress Ctrl+C to stop all servers...")
        
        for process in processes:
            process.wait()
            
    except KeyboardInterrupt:
        print("\nShutting down development servers...")
        
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait()
                
        print("All servers stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 