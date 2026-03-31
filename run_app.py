import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "Backend"
FRONTEND_DIR = PROJECT_ROOT / "Front End" / "react-app"
BACKEND_URL = "http://127.0.0.1:5000/health"
FRONTEND_URL = "http://127.0.0.1:5173"


def _npm_command() -> str:
    if os.name == "nt":
        return "npm.cmd"
    return "npm"


def _ensure_requirements() -> None:
    if not BACKEND_DIR.exists():
        raise RuntimeError(f"Backend directory not found: {BACKEND_DIR}")
    if not FRONTEND_DIR.exists():
        raise RuntimeError(
            f"React frontend directory not found: {FRONTEND_DIR}\n"
            "Expected path: Front End/react-app"
        )
    if shutil.which(_npm_command()) is None:
        raise RuntimeError("npm was not found in PATH. Please install Node.js and npm.")


def start_backend() -> subprocess.Popen:
    print("Starting backend on http://127.0.0.1:5000 ...")
    return subprocess.Popen([sys.executable, "app.py"], cwd=BACKEND_DIR)


def start_frontend() -> subprocess.Popen:
    print("Starting React frontend on http://127.0.0.1:5173 ...")
    return subprocess.Popen(
        [_npm_command(), "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
        cwd=FRONTEND_DIR,
    )


def main() -> None:
    _ensure_requirements()
    backend_proc = start_backend()
    frontend_proc = start_frontend()

    # Give servers a moment to boot before opening browser.
    time.sleep(4)
    webbrowser.open(FRONTEND_URL)

    print("\nTermSheet AI is now running!")
    print(f"- Backend health: {BACKEND_URL}")
    print(f"- React frontend: {FRONTEND_URL}")
    print("\nPress Ctrl+C to stop both services.")

    try:
        while True:
            # Exit if either process crashes.
            if backend_proc.poll() is not None:
                raise RuntimeError("Backend process exited unexpectedly.")
            if frontend_proc.poll() is not None:
                raise RuntimeError("Frontend process exited unexpectedly.")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        for proc in (frontend_proc, backend_proc):
            if proc.poll() is None:
                proc.terminate()
        for proc in (frontend_proc, backend_proc):
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    main()
