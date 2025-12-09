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

# External API Server URL for verification
# This is the public IP server that handles authentication
# Example: "http://123.45.67.89:8080"
EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL", "")

# Legacy: Keep for backward compatibility
EXTERNAL_SERVER_URL = os.getenv("EXTERNAL_SERVER_URL", "")

# Session management: stores the current verification log ID
current_log_id: int | None = None

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

class StartVerificationRequest(BaseModel):
    userId: str

class OTPSubmitRequest(BaseModel):
    answer: str

class MailRequest(BaseModel):
    senderEmail: str

# Global storage for latest data
latest_gps_data = {"latitude": "0.0", "longitude": "0.0", "timestamp": ""}
latest_camera_image = ""
cached_otp_question = None  # Cache for OTP question from external server

# ============================================================
# External API Integration Functions
# ============================================================

def get_external_api_url() -> str:
    """Get the external API URL, preferring EXTERNAL_API_URL over legacy."""
    return EXTERNAL_API_URL or EXTERNAL_SERVER_URL

async def call_external_api(
    endpoint: str, 
    method: str = "POST",
    json_data: dict | None = None,
    files: dict | None = None,
    timeout: int = 10
) -> dict | None:
    """Call external API server and return response data."""
    base_url = get_external_api_url()
    if not base_url:
        print(f"[EXTERNAL API] URL not set. Skipping {endpoint}.")
        return None
    
    target_url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    print(f"[EXTERNAL API] {method} {target_url}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(target_url, timeout=timeout)
        elif files:
            response = requests.post(target_url, files=files, timeout=timeout)
        else:
            response = requests.post(target_url, json=json_data, timeout=timeout)
        
        print(f"[EXTERNAL API] Response: {response.status_code}")
        
        if response.status_code == 200:
            try:
                return response.json()
            except:
                return {"raw": response.text}
        else:
            print(f"[EXTERNAL API] Error: {response.text}")
            return None
    except Exception as e:
        print(f"[EXTERNAL API] Exception: {e}")
        return None

# ============================================================
# Verification Session Management
# ============================================================

@app.post("/api/start")
async def start_verification(request: StartVerificationRequest):
    """Start a new verification session and get logId from external server."""
    global current_log_id
    
    print(f"[START] Starting verification for userId: {request.userId}")
    
    # Call external server to start verification
    result = await call_external_api(
        "api/verification/start",
        json_data={"userId": request.userId}
    )
    
    if result and "logId" in result:
        current_log_id = result["logId"]
        print(f"[START] Got logId: {current_log_id}")
        return {
            "status": "success",
            "logId": current_log_id,
            "message": "Verification session started"
        }
    elif not get_external_api_url():
        # Local mode: generate a mock logId
        import random
        current_log_id = random.randint(1000, 9999)
        print(f"[START] Local mode - generated logId: {current_log_id}")
        return {
            "status": "success",
            "logId": current_log_id,
            "message": "Local verification session started"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to start verification session with external server"
        )

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
    """Capture fingerprint and send to external server for verification."""
    global current_log_id
    
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
        
        # Read the captured fingerprint image
        with open(saved_path, "rb") as f:
            image_bytes = f.read()
        
        # Send to external API if configured
        if get_external_api_url() and current_log_id:
            result = await call_external_api(
                f"api/verification/{current_log_id}/fingerprint",
                files={"image": (filename, image_bytes, "image/x-portable-graymap")}
            )
            if result:
                return {
                    "status": "success",
                    "message": result.get("message", "Fingerprint verified"),
                    "similarity": result.get("similarity", 0),
                    "isSuccess": result.get("isSuccess", True),
                    "path": saved_path
                }
            else:
                raise HTTPException(status_code=400, detail="External fingerprint verification failed")
        
        # Legacy external validation (backward compatibility)
        if not await validate_with_external("validate_fingerprint", image_bytes, is_json=False):
            raise HTTPException(status_code=400, detail="External validation failed for fingerprint")

        return {"status": "success", "message": "Fingerprint captured and validated", "path": saved_path}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/camera")
async def get_camera_image():
    """Get cached camera image and send to external server for face verification."""
    global latest_camera_image, current_log_id
    
    if not latest_camera_image:
        raise HTTPException(status_code=404, detail="No image received yet")
    
    try:
        with open(latest_camera_image, "rb") as f:
            image_bytes = f.read()
        
        # Determine filename from path
        filename = Path(latest_camera_image).name
        
        # Send to external API for face verification if configured
        if get_external_api_url() and current_log_id:
            result = await call_external_api(
                f"api/verification/{current_log_id}/face",
                files={"image": (filename, image_bytes, "image/jpeg")}
            )
            if result:
                return {
                    "status": "success",
                    "message": result.get("message", "Face verified"),
                    "faceDistance": result.get("faceDistance", 0),
                    "score": result.get("score", 100),
                    "isSuccess": result.get("isSuccess", True),
                    "path": latest_camera_image
                }
            else:
                raise HTTPException(status_code=400, detail="External face verification failed")
        
        # Legacy external validation (backward compatibility)
        if not await validate_with_external("validate_camera", image_bytes, is_json=False):
            raise HTTPException(status_code=400, detail="External validation failed for camera")
             
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CAMERA VALIDATION] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

    return {"status": "success", "message": "Camera captured", "path": latest_camera_image}

@app.get("/api/gps")
async def get_gps_location():
    """Get GPS location and send to external server for verification."""
    global latest_gps_data, current_log_id
    
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
    
    # Send to external API for GPS verification if configured
    if get_external_api_url() and current_log_id:
        result = await call_external_api(
            f"api/verification/{current_log_id}/gps",
            json_data={"latitude": lat, "longitude": lon}
        )
        if result:
            return {
                "status": "success",
                "data": latest_gps_data,
                "gpsLocation": result.get("gpsLocation", ""),
                "ipLocation": result.get("ipLocation", ""),
                "isSuccess": result.get("isSuccess", True)
            }
        else:
            raise HTTPException(status_code=400, detail="External GPS verification failed")
    
    # Legacy external validation (backward compatibility)
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
    """Upload signature and send to external server for verification."""
    global current_log_id
    
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
        
        # Send to external API for signature verification if configured
        if get_external_api_url() and current_log_id:
            result = await call_external_api(
                f"api/verification/{current_log_id}/signature",
                files={"image": (filename, decoded_image, "image/png")}
            )
            if result:
                return {
                    "status": "success",
                    "message": result.get("message", "Signature saved"),
                    "isSuccess": result.get("isSuccess", True),
                    "path": str(image_path)
                }
            else:
                raise HTTPException(status_code=400, detail="External signature verification failed")
            
        # Legacy external validation (backward compatibility)
        if not await validate_with_external("validate_signature", decoded_image, is_json=False):
            raise HTTPException(status_code=400, detail="External validation failed for signature")
        
        return {"status": "success", "message": "Signature captured", "path": str(image_path)}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# OTP (News-based Quiz) Endpoints
# ============================================================

@app.get("/api/otp")
async def get_otp_question():
    """Get OTP question from external server (news-based quiz)."""
    global current_log_id, cached_otp_question
    
    if get_external_api_url() and current_log_id:
        result = await call_external_api(
            f"api/verification/{current_log_id}/otp",
            method="GET"
        )
        if result:
            cached_otp_question = result
            return {
                "status": "success",
                "question": result.get("question", ""),
                "options": result.get("options", []),
                "newsTitle": result.get("newsTitle", "")
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to get OTP question from server")
    
    # Local mode: return mock question
    return {
        "status": "success",
        "question": "What is the capital of South Korea?",
        "options": ["A. Busan", "B. Seoul", "C. Incheon", "D. Daegu"],
        "newsTitle": "(Local Mode - Mock Question)",
        "correctAnswer": "B"  # Only in local mode for testing
    }

@app.post("/api/otp")
async def submit_otp_answer(request: OTPSubmitRequest):
    """Submit OTP answer to external server."""
    global current_log_id
    
    if get_external_api_url() and current_log_id:
        result = await call_external_api(
            f"api/verification/{current_log_id}/otp",
            json_data={"answer": request.answer}
        )
        if result:
            return {
                "status": "success",
                "isCorrect": result.get("isCorrect", False),
                "message": result.get("message", "")
            }
        else:
            raise HTTPException(status_code=400, detail="OTP verification failed")
    
    # Local mode: check against mock answer
    is_correct = request.answer.upper() == "B"
    return {
        "status": "success",
        "isCorrect": is_correct,
        "message": "Correct!" if is_correct else "Incorrect answer"
    }

# ============================================================
# Mail Notification Endpoint
# ============================================================

@app.post("/api/mail")
async def send_verification_mail(request: MailRequest):
    """Send verification result email via external server."""
    global current_log_id
    
    if not request.senderEmail:
        raise HTTPException(status_code=400, detail="Email address is required")
    
    if get_external_api_url() and current_log_id:
        result = await call_external_api(
            f"api/verification/{current_log_id}/mail",
            json_data={"senderEmail": request.senderEmail}
        )
        if result:
            return {
                "status": "success",
                "message": result.get("message", "Mail sent successfully"),
                "targetMail": result.get("targetMail", request.senderEmail),
                "isSuccess": result.get("isSuccess", True)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send verification mail")
    
    # Local mode: simulate mail sending
    print(f"[MAIL] Local mode - would send to: {request.senderEmail}")
    return {
        "status": "success",
        "message": "Mail sent successfully (local mode)",
        "targetMail": request.senderEmail,
        "isSuccess": True
    }

# Serve frontend static files (auto-build if configured)
ensure_frontend_assets()

if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces, port 5000 (or 10001 if you want to match ESP32 default)
    # User can configure ESP32 to point to this server IP:5000
    print(f"Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=5000)
