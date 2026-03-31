import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "Front End" / "react-app"
TRAIN_SCRIPT = PROJECT_ROOT / "Backend" / "model" / "train_model.py"


def run_step(command, cwd=None):
    print(f"\n> {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True)


def npm_command() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def main():
    parser = argparse.ArgumentParser(
        description="Train model, build frontend, and run production server."
    )
    parser.add_argument("--skip-train", action="store_true", help="Skip model training.")
    parser.add_argument("--skip-build", action="store_true", help="Skip frontend build.")
    parser.add_argument("--port", type=int, default=5000, help="Production server port.")
    args = parser.parse_args()

    if not args.skip_train:
        run_step([sys.executable, str(TRAIN_SCRIPT)], cwd=PROJECT_ROOT)

    if not args.skip_build:
        if shutil.which(npm_command()) is None:
            raise RuntimeError("npm not found in PATH. Install Node.js before building frontend.")
        run_step([npm_command(), "install"], cwd=FRONTEND_DIR)
        run_step([npm_command(), "run", "build"], cwd=FRONTEND_DIR)

    run_step(
        [
            "waitress-serve",
            f"--listen=0.0.0.0:{args.port}",
            "Backend.app:app",
        ],
        cwd=PROJECT_ROOT,
    )


if __name__ == "__main__":
    main()
