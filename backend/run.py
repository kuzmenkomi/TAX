#!/usr/bin/env python
"""Simple startup script for backend"""
import subprocess
import sys

if __name__ == "__main__":
    # Run uvicorn with correct Python path
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app.api.server:app",
        "--port", "8000",
        "--host", "127.0.0.1"
    ], cwd="C:\\Users\\kuzme\\Tax\\backend")
