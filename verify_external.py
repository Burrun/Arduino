import requests
import time
import threading
import os
import subprocess
import signal
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configuration
LOCAL_SERVER_PORT = 5000
MOCK_EXTERNAL_PORT = 6000
BASE_URL = f"http://localhost:{LOCAL_SERVER_PORT}"
MOCK_EXTERNAL_URL = f"http://localhost:{MOCK_EXTERNAL_PORT}"

# Mock External Server
class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
        # print(f"[MOCK] Received POST at {self.path}")

def run_mock_server():
    server = HTTPServer(('localhost', MOCK_EXTERNAL_PORT), MockHandler)
    print(f"[MOCK] Starting mock external server on port {MOCK_EXTERNAL_PORT}")
    server.serve_forever()

def start_server(env=None):
    # Kill existing server on port 5000
    subprocess.run(["fuser", "-k", f"{LOCAL_SERVER_PORT}/tcp"], stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    cmd = ["./venv/bin/python3", "server.py"]
    process = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[TEST] Started server.py (PID: {process.pid})")
    time.sleep(3) # Wait for startup
    return process

def stop_server(process):
    if process:
        process.terminate()
        process.wait()
        print("[TEST] Stopped server.py")

def test_local_mode():
    print("\n=== Testing Local Mode (No External URL) ===")
    env = os.environ.copy()
    if "EXTERNAL_SERVER_URL" in env:
        del env["EXTERNAL_SERVER_URL"]
    
    process = start_server(env)
    try:
        # Test GPS (easiest to test)
        # First upload some data
        requests.post(f"{BASE_URL}/upload_gps", data="37.0,127.0,2023-01-01")
        
        # Then get it
        res = requests.get(f"{BASE_URL}/api/gps")
        if res.status_code == 200:
            print("   [PASS] Local Mode GPS Request succeeded")
        else:
            print(f"   [FAIL] Local Mode GPS Request failed: {res.status_code}")
            
    finally:
        stop_server(process)

def test_external_mode():
    print("\n=== Testing External Mode (With External URL) ===")
    
    # Start Mock Server
    mock_thread = threading.Thread(target=run_mock_server, daemon=True)
    mock_thread.start()
    time.sleep(1)
    
    # Start Local Server with Env Var
    env = os.environ.copy()
    env["EXTERNAL_SERVER_URL"] = MOCK_EXTERNAL_URL
    
    process = start_server(env)
    try:
        # Test GPS
        requests.post(f"{BASE_URL}/upload_gps", data="37.0,127.0,2023-01-01")
        
        res = requests.get(f"{BASE_URL}/api/gps")
        if res.status_code == 200:
            print("   [PASS] External Mode GPS Request succeeded (Validated)")
        else:
            print(f"   [FAIL] External Mode GPS Request failed: {res.status_code}")
            
    finally:
        stop_server(process)

if __name__ == "__main__":
    try:
        test_local_mode()
        test_external_mode()
    except Exception as e:
        print(f"Test failed: {e}")
