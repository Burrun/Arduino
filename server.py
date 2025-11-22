from fastapi import FastAPI, HTTPException
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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
# Ensure the frontend is built first (npm run build)
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
else:
    print("Warning: frontend/dist not found. Please run 'npm run build' in the frontend directory.")

class CamRequest(BaseModel):
    command: str

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
        # Create directory if it doesn't exist
        image_dir = Path("data/fingerprints")
        image_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp, _ = rtc.get_current_time()
        filename = f"fingerprint_{timestamp.strftime('%Y%m%d_%H%M%S')}.pgm"
        image_path = image_dir / filename

        finger = fingerprint.connect_fingerprint_sensor()
        saved_path = fingerprint.capture_fingerprint_image(
            finger, save_path=str(image_path), timeout_sec=15
        )
        
        return {"status": "success", "message": "Fingerprint captured", "path": saved_path}
    except Exception as e:
        # For demo purposes, if hardware is missing, we might want to return a mock response
        # But for now, let's return the error
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/camera")
async def trigger_camera():
    try:
        image_dir = Path("data/camera")
        image_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp, _ = rtc.get_current_time()
        filename = f"camera_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        image_path = image_dir / filename
        
        # Use default ESP32 URL or from env
        saved_path = camera.capture_image(save_path=str(image_path), timeout=10)
        
        return {"status": "success", "message": "Camera captured", "path": saved_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gps")
async def get_gps_location():
    try:
        location = gps.get_current_location(timeout=10)
        return {"status": "success", "data": location}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/signature")
async def trigger_signature():
    try:
        signature_dir = Path("data/signatures")
        signature_dir.mkdir(parents=True, exist_ok=True)
        
        # Assuming signature module has a capture function similar to others
        # If not, we might need to check signature.py content.
        # Based on main.py: saved_path = signature.capture_signature()
        saved_path = signature.capture_signature()
        
        # Move/Rename if needed, or just return the path
        return {"status": "success", "message": "Signature captured", "path": saved_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
