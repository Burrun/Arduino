from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
from pathlib import Path
import requests
import shutil
import subprocess
import threading
import time

# Add the current directory to sys.path to allow importing modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.sensors import rtc, fingerprint, signature, camera, gps

app = FastAPI()

# Configuration
# ESP32-CAM IP Address (Default: 192.168.4.1 for AP mode)
# If your ESP32 is connected to your router, change this to its assigned IP.
ESP32_CAM_URL = os.getenv("ESP32_CAM_URL", "http://192.168.4.1")

# External Server URL for validation (Optional)
# If set, data will be sent here for validation.
# Example: "http://external-server.com/api"
EXTERNAL_SERVER_URL = os.getenv("EXTERNAL_SERVER_URL", "")

# Kiosk browser auto-launch configuration
AUTO_LAUNCH_KIOSK = os.getenv("AUTO_LAUNCH_KIOSK", "1").lower() not in {"0", "false", "no"}
KIOSK_URL = os.getenv("KIOSK_URL", "http://localhost:5000")

# Frontend build configuration
AUTO_BUILD_FRONTEND = os.getenv("AUTO_BUILD_FRONTEND", "1").lower() not in {"0", "false", "no"}
FRONTEND_DIR = Path(__file__).parent / "frontend"

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files will be configured at the end

def run_frontend_build() -> bool:
    """Run `npm run build` inside the frontend directory."""
    if not AUTO_BUILD_FRONTEND:
        print("[FRONTEND] Auto-build disabled via AUTO_BUILD_FRONTEND.")
        return False

    if not FRONTEND_DIR.exists():
        print(f"[FRONTEND] Frontend directory not found at {FRONTEND_DIR}. Skipping build.")
        return False

    print(f"[FRONTEND] Running npm run build in {FRONTEND_DIR} ...")
    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=FRONTEND_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        print("[FRONTEND] Build completed.")
        return True
    except FileNotFoundError:
        print("[FRONTEND] npm not found. Install Node.js and npm to build the frontend.")
    except subprocess.CalledProcessError as e:
        combined_output = f"{(e.stdout or '').strip()}\n{(e.stderr or '').strip()}".strip()
        print(f"[FRONTEND] Build failed (exit {e.returncode}).")
        if combined_output:
            print(combined_output)
    return False

def ensure_frontend_assets():
    """Build the frontend (if enabled) and mount the static files."""
    dist_dir = FRONTEND_DIR / "dist"
    build_attempted = run_frontend_build()

    if dist_dir.exists():
        app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")
        print(f"[FRONTEND] Serving static files from {dist_dir}")
    else:
        if build_attempted:
            print("[FRONTEND] Build attempted but frontend/dist not found; static files will not be served.")
        else:
            print("[FRONTEND] frontend/dist not found. Please run 'npm run build' in the frontend directory.")

# Helper for external validation
async def validate_with_external(endpoint: str, data: dict | bytes, is_json: bool = True):
    if not EXTERNAL_SERVER_URL:
        print(f"[VALIDATION] External URL not set. Skipping validation for {endpoint}.")
        return True # Local mode: always success

    target_url = f"{EXTERNAL_SERVER_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    print(f"[VALIDATION] Sending data to {target_url}...")
    
    try:
        if is_json:
            response = requests.post(target_url, json=data, timeout=5)
        else:
            # For binary data (images), we might need to decide how to send.
            # Usually multipart/form-data or raw body. Let's assume raw body or specific key.
            # For simplicity in this demo, let's send as raw body if bytes.
            response = requests.post(target_url, data=data, timeout=5)
            
        if response.status_code == 200:
            print(f"[VALIDATION] Success: {response.status_code}")
            return True
        else:
            print(f"[VALIDATION] Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[VALIDATION] Error: {e}")
        return False

class CamRequest(BaseModel):
    command: str

# Global storage for latest data
latest_gps_data = {"latitude": "0.0", "longitude": "0.0", "timestamp": ""}
latest_camera_image = ""

@app.post("/upload_gps")
async def upload_gps(request: Request):
    global latest_gps_data
    try:
        body = await request.body()
        gps_data = body.decode("utf-8").strip()
        print(f"[GPS UPLOAD] Received: {gps_data}")
        
        # Parse GPS data (Assuming format: "lat,lon,timestamp" or similar from ESP32)
        # Based on cpp: Serial.println("[GPS] " + line); uploadGPS(line);
        # We need to know the exact format. For now, store raw or try to parse.
        # Let's assume comma separated for now or just store as is.
        parts = gps_data.split(',')
        if len(parts) >= 2:
            latest_gps_data["latitude"] = parts[0]
            latest_gps_data["longitude"] = parts[1]
            if len(parts) > 2:
                latest_gps_data["timestamp"] = parts[2]
            else:
                timestamp, _ = rtc.get_current_time(verbose=False)
                latest_gps_data["timestamp"] = timestamp.isoformat()
        
        return {"status": "success"}
    except Exception as e:
        print(f"[GPS UPLOAD] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_image")
async def upload_image(request: Request):
    global latest_camera_image
    try:
        # ESP32 sends raw bytes as body
        body = await request.body()
        
        image_dir = Path("data/camera")
        image_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp, _ = rtc.get_current_time(verbose=False)
        filename = f"camera_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        image_path = image_dir / filename
        
        with open(image_path, "wb") as f:
            f.write(body)
            
        latest_camera_image = str(image_path)
        print(f"[IMAGE UPLOAD] Saved to {image_path}, Size: {len(body)} bytes")
        
        return {"status": "success"}
    except Exception as e:
        print(f"[IMAGE UPLOAD] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rtc")
async def get_rtc_time():
    try:
        timestamp, source = rtc.get_current_time(verbose=False)
        return {"timestamp": timestamp.isoformat(), "source": source}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sensors/status")
async def check_sensors():
    """Check the status of all sensors."""
    try:
        return {
            "rtc": rtc.is_rtc_connected(),
            "fingerprint": fingerprint.is_sensor_connected(),
            "camera": camera.is_camera_connected(),
            "gps": gps.is_gps_connected(),
            "signature": True  # Signature is software-based, always available
        }
    except Exception as e:
        print(f"[SENSORS] Error checking sensors: {e}")
        # Return partial results even if some checks fail
        return {
            "rtc": False,
            "fingerprint": False,
            "camera": False,
            "gps": False,
            "signature": True
        }

@app.post("/api/fingerprint")
async def scan_fingerprint():
    try:
        image_dir = Path("data/fingerprints")
        image_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp, _ = rtc.get_current_time(verbose=False)
        filename = f"fingerprint_{timestamp.strftime('%Y%m%d_%H%M%S')}.pgm"
        image_path = image_dir / filename

        finger = fingerprint.connect_fingerprint_sensor()
        saved_path = fingerprint.capture_fingerprint_image(
            finger, save_path=str(image_path), timeout_sec=15
        )
        
        # External Validation
        # Read the file and send it
        with open(saved_path, "rb") as f:
            image_bytes = f.read()
        
        if not await validate_with_external("validate_fingerprint", image_bytes, is_json=False):
             raise HTTPException(status_code=400, detail="External validation failed for fingerprint")

        return {"status": "success", "message": "Fingerprint captured and validated", "path": saved_path}
    except HTTPException as he:
        raise he
    except Exception as e:
        # For demo purposes, if hardware is missing, we might want to return a mock response
        # But for now, let's return the error
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/camera")
async def get_camera_image():
    global latest_camera_image
    if not latest_camera_image:
        raise HTTPException(status_code=404, detail="No image received yet")
    
    # External Validation
    # We validate the *cached* image when the frontend requests it (or we could do it on upload)
    # Doing it here ensures the user sees "Success" only if external server approves.
    try:
        with open(latest_camera_image, "rb") as f:
            image_bytes = f.read()
            
        if not await validate_with_external("validate_camera", image_bytes, is_json=False):
             raise HTTPException(status_code=400, detail="External validation failed for camera")
             
    except Exception as e:
        print(f"[CAMERA VALIDATION] Error: {e}")
        # If file read fails or validation errors out (not just returns false), fail safe?
        # Let's fail if validation explicitly fails.
        if "External validation failed" in str(e):
            raise e
        # If file missing etc
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

    return {"status": "success", "message": "Camera captured", "path": latest_camera_image}

@app.get("/api/gps")
async def get_gps_location():
    global latest_gps_data
    
    # Validate GPS coordinates (reject 0.0, 0.0)
    try:
        lat = float(latest_gps_data.get("latitude", 0))
        lon = float(latest_gps_data.get("longitude", 0))
        if lat == 0.0 and lon == 0.0:
            raise HTTPException(
                status_code=400, 
                detail="Invalid GPS coordinates: location is 0.0, 0.0"
            )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid GPS data format")
    
    # External Validation
    if not await validate_with_external("validate_gps", latest_gps_data, is_json=True):
         raise HTTPException(status_code=400, detail="External validation failed for GPS")

    return {"status": "success", "data": latest_gps_data}

class SignatureRequest(BaseModel):
    image: str # Base64 encoded image

def _launch_kiosk_browser():
    """Launch chromium in kiosk mode for fullscreen display."""
    # Try chromium-browser first, then chromium
    browser_cmd = None
    for cmd in ["chromium-browser", "chromium"]:
        if shutil.which(cmd):
            browser_cmd = cmd
            break
    
    if not browser_cmd:
        print("[KIOSK] chromium not found in PATH; skipping auto-launch.")
        print("[KIOSK] Install with: sudo apt-get install chromium-browser")
        return
    
    # Small delay to let uvicorn start accepting requests
    time.sleep(0.8)
    
    try:
        subprocess.Popen(
            [
                browser_cmd,
                "--kiosk",
                "--disable-infobars",
                "--noerrdialogs",
                "--disable-session-crashed-bubble",
                "--disable-restore-session-state",
                KIOSK_URL
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"[KIOSK] Launched {browser_cmd} in kiosk mode pointing to {KIOSK_URL}")
    except Exception as e:
        print(f"[KIOSK] Failed to launch browser: {e}")

@app.on_event("startup")
async def start_kiosk():
    """Auto-open the frontend in kiosk browser when the server starts."""
    if not AUTO_LAUNCH_KIOSK:
        print("[KIOSK] Auto-launch disabled via AUTO_LAUNCH_KIOSK.")
        return
    threading.Thread(target=_launch_kiosk_browser, daemon=True).start()

@app.post("/api/signature")
async def upload_signature(request: SignatureRequest):
    try:
        import base64
        from PIL import Image
        import io
        
        signature_dir = Path("data/signatures")
        signature_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp, _ = rtc.get_current_time(verbose=False)
        filename = f"signature_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        image_path = signature_dir / filename
        
        # Remove header if present (e.g., "data:image/png;base64,")
        image_data = request.image
        if "," in image_data:
            image_data = image_data.split(",")[1]
            
        decoded_image = base64.b64decode(image_data)
        
        # Check if signature is blank
        try:
            img = Image.open(io.BytesIO(decoded_image))
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            pixels = list(img.getdata())
            # Count non-white pixels (allowing for slight variations from pure white)
            non_white = sum(1 for p in pixels if sum(p) < 750)  # 750 = 255*3 - tolerance
            
            # Require at least 100 non-white pixels for a valid signature
            if non_white < 100:
                raise HTTPException(
                    status_code=400,
                    detail="Signature is blank or contains insufficient data"
                )
        except HTTPException:
            raise
        except Exception as e:
            print(f"[SIGNATURE] Warning: Could not validate signature content: {e}")
            # Continue even if validation fails (PIL might not be available)
        
        with open(image_path, "wb") as f:
            f.write(decoded_image)
            
        # External Validation
        # Send raw bytes or base64? Let's send raw bytes for consistency with others
        if not await validate_with_external("validate_signature", decoded_image, is_json=False):
             raise HTTPException(status_code=400, detail="External validation failed for signature")
        
        return {"status": "success", "message": "Signature captured", "path": str(image_path)}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve frontend static files (auto-build if configured)
ensure_frontend_assets()

if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces, port 5000 (or 10001 if you want to match ESP32 default)
    # User can configure ESP32 to point to this server IP:5000
    print(f"Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=5000)
