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

# AuthBox Backend Server URL (AWS EC2)
AUTHBOX_SERVER_URL = os.getenv("AUTHBOX_SERVER_URL", "http://35.175.180.106:8080")

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "20"))

# External Server URL for validation (Optional - Legacy, kept for backward compatibility)
EXTERNAL_SERVER_URL = os.getenv("EXTERNAL_SERVER_URL", "")

# Kiosk browser auto-launch configuration
AUTO_LAUNCH_KIOSK = os.getenv("AUTO_LAUNCH_KIOSK", "1").lower() not in {"0", "false", "no"}
KIOSK_URL = os.getenv("KIOSK_URL", "http://localhost:8000")

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

# ============================================================
# AuthBox API - Request/Response Models
# ============================================================

class LoginRequest(BaseModel):
    id: str          # 사용자 아이디 (API 명세: id)
    password: str    # 사용자 비밀번호

class VerificationStartRequest(BaseModel):
    userId: str      # 인증을 요청하는 수취인의 id

class GPSRequest(BaseModel):
    latitude: float   # GPS 위도
    longitude: float  # GPS 경도

class OTPRequest(BaseModel):
    userReporter: str  # 사용자가 입력한 기자 이름

class MailRequest(BaseModel):
    senderEmail: str   # 송금 예정자의 이메일 주소 (API 명세: senderEmail)

# ============================================================
# Session Management for AuthBox
# ============================================================

class SessionManager:
    """Manages user sessions and logId with 20-minute timeout."""
    
    def __init__(self, timeout_minutes: int = 20):
        self.timeout_minutes = timeout_minutes
        self.sessions = {}  # {logId: {"user": ..., "created_at": ..., "login_token": ...}}
        self.current_user = None
        self.login_time = None
        self.current_log_id = None
        
    def set_login(self, user_data: dict):
        """Store login session."""
        self.current_user = user_data
        self.login_time = time.time()
        print(f"[SESSION] User logged in: {user_data.get('username', 'unknown')}")
        
    def requires_login(self):
        """Check if user is logged in and session is valid."""
        if not self.current_user or not self.login_time:
            raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
            
        elapsed = (time.time() - self.login_time) / 60
        if elapsed > self.timeout_minutes:
            print(f"[SESSION] Login session expired (elapsed: {elapsed:.1f} min)")
            self.current_user = None
            self.login_time = None
            raise HTTPException(status_code=401, detail="로그인 세션이 만료되었습니다. 다시 로그인해주세요.")
            
    def set_log_id(self, log_id: int):
        """Store logId from verification start."""
        self.current_log_id = log_id
        self.sessions[log_id] = {
            "created_at": time.time(),
            "user": self.current_user
        }
        print(f"[SESSION] LogId created: {log_id}")
        
    def validate_session(self, log_id: int) -> bool:
        """Check if session is valid and not expired."""
        if log_id not in self.sessions:
            print(f"[SESSION] LogId {log_id} not found")
            return False
            
        session = self.sessions[log_id]
        elapsed = (time.time() - session["created_at"]) / 60
        
        if elapsed > self.timeout_minutes:
            print(f"[SESSION] LogId {log_id} expired (elapsed: {elapsed:.1f} min)")
            del self.sessions[log_id]
            return False
            
        return True
        
    def clear_session(self, log_id: int = None):
        """Clear session data."""
        if log_id and log_id in self.sessions:
            del self.sessions[log_id]
        self.current_user = None
        self.login_time = None
        self.current_log_id = None
        print("[SESSION] Session cleared")
        
    def is_logged_in(self) -> bool:
        """Check if user is logged in and session not expired."""
        if not self.current_user or not self.login_time:
            return False
        elapsed = (time.time() - self.login_time) / 60
        return elapsed <= self.timeout_minutes

# Global session manager
session_manager = SessionManager(timeout_minutes=SESSION_TIMEOUT_MINUTES)

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
        
        # RTC 또는 시스템 시간 사용
        try:
            timestamp, _ = rtc.get_current_time(verbose=False)
        except Exception:
            from datetime import datetime
            timestamp = datetime.now()
        
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
            if non_white < 10:
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

# ============================================================
# AuthBox API Endpoints (Proxy to AuthBox Server)
# ============================================================

@app.post("/api/user/login")
async def authbox_login(request: LoginRequest):
    """
    Step 1: 사용자 로그인
    AuthBox 서버로 로그인 요청을 전달합니다.
    요청: {"id": "사용자ID", "password": "비밀번호"}
    """
    try:
        response = requests.post(
            f"{AUTHBOX_SERVER_URL}/api/user/login",
            json={"id": request.id, "password": request.password},
            timeout=10
        )
        
        if response.status_code == 200:
            # AuthBox 서버가 JSON 또는 text/plain으로 응답할 수 있음
            try:
                data = response.json()
            except:
                # text/plain 응답인 경우 (예: "로그인 성공")
                data = {"message": response.text.strip()}
            
            session_manager.set_login({"userId": request.id, **data})
            print(f"[AUTHBOX] Login successful for {request.id}")
            return {"message": "로그인 성공", "userId": request.id, **data}
        else:
            print(f"[AUTHBOX] Login failed: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"[AUTHBOX] Login request error: {e}")
        raise HTTPException(status_code=500, detail=f"AuthBox 서버 연결 실패: {str(e)}")


@app.post("/api/verification/start")
async def authbox_start_verification(request: VerificationStartRequest = None):
    """
    Step 2: 인증 세션 시작
    AuthBox 서버에서 logId를 발급받습니다.
    요청: {"userId": "사용자ID"}
    """
    if not session_manager.current_user:
        # Fallback if requires_login raises exception directly, but we want to use the method
        pass 
    
    # Check login validity (existence + expiration)
    session_manager.requires_login()
    
    # userId는 요청에서 받거나, 로그인 세션에서 가져옴
    user_id = request.userId if request else session_manager.current_user.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="userId가 필요합니다.")
        
    try:
        response = requests.post(
            f"{AUTHBOX_SERVER_URL}/api/verification/start",
            json={"userId": user_id},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            log_id = data.get("logId")
            if log_id:
                session_manager.set_log_id(log_id)
                print(f"[AUTHBOX] Verification started with logId: {log_id}")
            return data
        else:
            print(f"[AUTHBOX] Start verification failed: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"[AUTHBOX] Start verification error: {e}")
        raise HTTPException(status_code=500, detail=f"AuthBox 서버 연결 실패: {str(e)}")


@app.post("/api/verification/{log_id}/gps")
async def authbox_verify_gps(log_id: int, request: GPSRequest = None):
    """
    Step 3-1: GPS 위치 인증
    ESP32에서 수집된 GPS 데이터 또는 요청 데이터를 AuthBox 서버로 전송합니다.
    """
    if not session_manager.validate_session(log_id):
        raise HTTPException(status_code=401, detail="세션이 만료되었거나 유효하지 않습니다.")
    
    # 요청 데이터가 있으면 사용, 없으면 ESP32에서 수집된 데이터 사용
    if request:
        lat = request.latitude
        lon = request.longitude
    else:
        lat = float(latest_gps_data.get("latitude", 0))
        lon = float(latest_gps_data.get("longitude", 0))
    
    if lat == 0.0 and lon == 0.0:
        raise HTTPException(status_code=400, detail="유효한 GPS 데이터가 없습니다.")
        
    try:
        response = requests.post(
            f"{AUTHBOX_SERVER_URL}/api/verification/{log_id}/gps",
            json={"latitude": lat, "longitude": lon},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"[AUTHBOX] GPS verification success for logId: {log_id}")
            return response.json()
        else:
            print(f"[AUTHBOX] GPS verification failed: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"[AUTHBOX] GPS verification error: {e}")
        raise HTTPException(status_code=500, detail=f"AuthBox 서버 연결 실패: {str(e)}")


@app.post("/api/verification/{log_id}/otp")
async def authbox_verify_otp(log_id: int, request: OTPRequest):
    """
    Step 3-2: 뉴스 OTP 인증
    사용자가 입력한 기자 이름을 AuthBox 서버로 전송합니다.
    """
    if not session_manager.validate_session(log_id):
        raise HTTPException(status_code=401, detail="세션이 만료되었거나 유효하지 않습니다.")
        
    try:
        response = requests.post(
            f"{AUTHBOX_SERVER_URL}/api/verification/{log_id}/otp",
            json={"userReporter": request.userReporter},
            timeout=60
        )
        
        if response.status_code == 200:
            print(f"[AUTHBOX] OTP verification success for logId: {log_id}")
            return response.json()
        else:
            print(f"[AUTHBOX] OTP verification failed: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"[AUTHBOX] OTP verification error: {e}")
        raise HTTPException(status_code=500, detail=f"AuthBox 서버 연결 실패: {str(e)}")


@app.post("/api/verification/{log_id}/face")
async def authbox_verify_face(log_id: int):
    """
    Step 3-3: 얼굴 인증
    ESP32-CAM으로 촬영된 이미지를 AuthBox 서버로 전송합니다.
    """
    if not session_manager.validate_session(log_id):
        raise HTTPException(status_code=401, detail="세션이 만료되었거나 유효하지 않습니다.")
    
    if not latest_camera_image:
        raise HTTPException(status_code=400, detail="카메라 이미지가 없습니다. 먼저 촬영해주세요.")
        
    try:
        with open(latest_camera_image, "rb") as f:
            image_bytes = f.read()
            
        response = requests.post(
            f"{AUTHBOX_SERVER_URL}/api/verification/{log_id}/face",
            files={"image": ("face.jpg", image_bytes, "image/jpeg")},
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"[AUTHBOX] Face verification success for logId: {log_id}")
            return response.json()
        else:
            print(f"[AUTHBOX] Face verification failed: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="카메라 이미지 파일을 찾을 수 없습니다.")
    except requests.exceptions.RequestException as e:
        print(f"[AUTHBOX] Face verification error: {e}")
        raise HTTPException(status_code=500, detail=f"AuthBox 서버 연결 실패: {str(e)}")


@app.post("/api/verification/{log_id}/fingerprint")
async def authbox_verify_fingerprint(log_id: int):
    """
    Step 3-4: 지문 인증
    지문 센서에서 스캔한 이미지를 AuthBox 서버로 전송합니다.
    """
    if not session_manager.validate_session(log_id):
        raise HTTPException(status_code=401, detail="세션이 만료되었거나 유효하지 않습니다.")
        
    try:
        # 지문 스캔
        image_dir = Path("data/fingerprints")
        image_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp, _ = rtc.get_current_time(verbose=False)
        filename = f"fingerprint_{timestamp.strftime('%Y%m%d_%H%M%S')}.pgm"
        image_path = image_dir / filename

        finger = fingerprint.connect_fingerprint_sensor()
        saved_path = fingerprint.capture_fingerprint_image(
            finger, save_path=str(image_path), timeout_sec=15
        )
        
        with open(saved_path, "rb") as f:
            image_bytes = f.read()
            
        response = requests.post(
            f"{AUTHBOX_SERVER_URL}/api/verification/{log_id}/fingerprint",
            files={"image": ("fingerprint.png", image_bytes, "image/png")},
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"[AUTHBOX] Fingerprint verification success for logId: {log_id}")
            return response.json()
        else:
            print(f"[AUTHBOX] Fingerprint verification failed: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"[AUTHBOX] Fingerprint verification error: {e}")
        raise HTTPException(status_code=500, detail=f"AuthBox 서버 연결 실패: {str(e)}")
    except Exception as e:
        print(f"[AUTHBOX] Fingerprint scan error: {e}")
        raise HTTPException(status_code=500, detail=f"지문 스캔 실패: {str(e)}")


@app.post("/api/verification/{log_id}/signature")
async def authbox_verify_signature(log_id: int, request: SignatureRequest):
    """
    Step 3-5: 서명 인증
    서명 패드에서 입력받은 이미지를 AuthBox 서버로 전송합니다.
    """
    if not session_manager.validate_session(log_id):
        raise HTTPException(status_code=401, detail="세션이 만료되었거나 유효하지 않습니다.")
        
    try:
        import base64
        
        # 서명 이미지 디코딩
        image_data = request.image
        if "," in image_data:
            image_data = image_data.split(",")[1]
        decoded_image = base64.b64decode(image_data)
        
        # 로컬 저장
        signature_dir = Path("data/signatures")
        signature_dir.mkdir(parents=True, exist_ok=True)
        
        # RTC 또는 시스템 시간 사용
        try:
            timestamp, _ = rtc.get_current_time(verbose=False)
        except Exception:
            from datetime import datetime
            timestamp = datetime.now()
        
        filename = f"signature_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        image_path = signature_dir / filename
        
        with open(image_path, "wb") as f:
            f.write(decoded_image)
            
        # AuthBox 서버로 전송
        response = requests.post(
            f"{AUTHBOX_SERVER_URL}/api/verification/{log_id}/signature",
            files={"image": ("signature.png", decoded_image, "image/png")},
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"[AUTHBOX] Signature verification success for logId: {log_id}")
            return response.json()
        else:
            print(f"[AUTHBOX] Signature verification failed: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"[AUTHBOX] Signature verification error: {e}")
        raise HTTPException(status_code=500, detail=f"AuthBox 서버 연결 실패: {str(e)}")
    except Exception as e:
        print(f"[AUTHBOX] Signature processing error: {e}")
        raise HTTPException(status_code=500, detail=f"서명 처리 실패: {str(e)}")


@app.post("/api/verification/{log_id}/mail")
async def authbox_send_mail(log_id: int, request: MailRequest):
    """
    Step 4: 결과 이메일 전송 및 세션 종료
    송금인 이메일로 결과를 전송하고 세션을 초기화합니다.
    """
    if not session_manager.validate_session(log_id):
        raise HTTPException(status_code=401, detail="세션이 만료되었거나 유효하지 않습니다.")
        
    try:
        response = requests.post(
            f"{AUTHBOX_SERVER_URL}/api/verification/{log_id}/mail",
            json={"senderEmail": request.senderEmail},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"[AUTHBOX] Mail sent success for logId: {log_id}")
            # 세션 초기화
            session_manager.clear_session(log_id)
            return response.json()
        else:
            print(f"[AUTHBOX] Mail send failed: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"[AUTHBOX] Mail send error: {e}")
        raise HTTPException(status_code=500, detail=f"AuthBox 서버 연결 실패: {str(e)}")


# ============================================================
# Session Status Endpoint (for frontend to check session)
# ============================================================

@app.get("/api/session/status")
async def get_session_status():
    """현재 세션 상태를 확인합니다."""
    return {
        "logged_in": session_manager.is_logged_in(),
        "current_log_id": session_manager.current_log_id,
        "username": session_manager.current_user.get("username") if session_manager.current_user else None
    }


# Serve frontend static files (auto-build if configured)
ensure_frontend_assets()

if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces, port 5000 (or 10001 if you want to match ESP32 default)
    # User can configure ESP32 to point to this server IP:5000
    print(f"Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
