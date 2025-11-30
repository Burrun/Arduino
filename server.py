from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
from pathlib import Path
import requests

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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files will be configured at the end

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
                timestamp, _ = rtc.get_current_time()
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
        
        timestamp, _ = rtc.get_current_time()
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
        timestamp, source = rtc.get_current_time()
        return {"timestamp": timestamp.isoformat(), "source": source}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fingerprint")
async def scan_fingerprint():
    try:
        image_dir = Path("data/fingerprints")
        image_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp, _ = rtc.get_current_time()
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
    
    # External Validation
    if not await validate_with_external("validate_gps", latest_gps_data, is_json=True):
         raise HTTPException(status_code=400, detail="External validation failed for GPS")

    return {"status": "success", "data": latest_gps_data}

class SignatureRequest(BaseModel):
    image: str # Base64 encoded image

@app.post("/api/signature")
async def upload_signature(request: SignatureRequest):
    try:
        import base64
        
        signature_dir = Path("data/signatures")
        signature_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp, _ = rtc.get_current_time()
        filename = f"signature_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        image_path = signature_dir / filename
        
        # Remove header if present (e.g., "data:image/png;base64,")
        image_data = request.image
        if "," in image_data:
            image_data = image_data.split(",")[1]
            
        decoded_image = base64.b64decode(image_data)
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

# Serve frontend static files
# Ensure the frontend is built first (npm run build)
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
else:
    print("Warning: frontend/dist not found. Please run 'npm run build' in the frontend directory.")

if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces, port 5000 (or 10001 if you want to match ESP32 default)
    # User can configure ESP32 to point to this server IP:5000
    print(f"Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=5000)
