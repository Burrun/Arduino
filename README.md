# 프로젝트 설정 및 사용 가이드

## 1. 환경 설정 (Environment Setup)

이 프로젝트를 실행하기 위해서는 Python 가상환경을 설정하고 필요한 패키지들을 설치해야 합니다.

### 시스템 요구사항

이 프로젝트는 다음 시스템 패키지가 필요합니다:

**Chromium Browser (키오스크 모드)**
- 서버 시작 시 자동으로 fullscreen 키오스크 모드로 프론트엔드를 실행합니다.
- 설치 방법 (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install -y chromium-browser
cd frontend && npm install 
```

**자동 실행 설정**
- 기본적으로 `python server.py` 실행 시 chromium이 자동 실행됩니다.
- 비활성화하려면: `export AUTO_LAUNCH_KIOSK=0`
- URL 변경: `export KIOSK_URL=http://localhost:5000`

### 가상환경 생성 및 활성화

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 의존성 패키지 설치
가상환경이 활성화된 상태에서 아래 명령어로 필요한 패키지를 설치합니다:
```bash
pip install -r requirements.txt
```

## 2. 서버 API 문서 (개발자용)

백엔드는 FastAPI로 작성되었으며 `http://localhost:5000`에서 실행됩니다.

### 서버 실행 방법
백엔드 서버를 시작하려면 다음 명령어를 실행하세요:
```bash
# 가상환경(venv)이 켜져 있는지 확인하세요
python server.py
```

### API 엔드포인트 목록

| Method | Endpoint | 설명 |
|--------|----------|-------------|
| `GET` | `/api/rtc` | RTC 모듈 또는 시스템 시간 조회 |
| `POST` | `/api/fingerprint` | 지문 인식 및 이미지 캡처 |
| `POST` | `/api/camera` | ESP32-CAM으로 사진 촬영 |
| `GET` | `/api/gps` | 현재 GPS 위치 조회 |
| `POST` | `/api/signature` | 서명 입력 받기 |

프론트엔드가 빌드되어 있다면, 루트 URL `/`로 접속 시 정적 파일(`frontend/dist`)이 제공됩니다.

## 3. 프론트엔드 개발 가이드

프론트엔드 코드는 `frontend` 디렉토리에 위치해 있습니다.

### 설치 및 개발 서버 실행
```bash
cd frontend
npm install
npm run dev
```
위 명령어를 실행하면 개발 서버가 시작됩니다 (보통 `http://localhost:5173`).

### 배포용 빌드 (Production Build)
Python 서버에서 프론트엔드를 서빙할 수 있도록 빌드하려면 아래 명령어를 사용하세요:
```bash
cd frontend
npm run build
```
이 명령어는 `dist` 폴더를 생성하며, `server.py`는 이 폴더의 내용을 웹페이지로 보여줍니다.


## 4. 시스템 검증 및 운영 매뉴얼

이 문서는 시스템 구성 요소의 작동 방식, 통신 방법 및 검증 절차를 설명합니다.

### 4.1. 로컬 센서 및 입력 (서명, RTC, 지문)

이 구성 요소들은 로컬 서버(`server.py`) 또는 프론트엔드에서 직접 처리합니다.

#### **서명 (Signature)**
-   **작동 원리**:
    1.  사용자가 **프론트엔드** (Svelte) 캔버스(`SignaturePad.svelte`)에 서명합니다.
    2.  프론트엔드가 이미지 데이터(Base64 PNG)를 `POST /api/signature`를 통해 **백엔드**로 전송합니다.
    3.  백엔드는 이미지를 `data/signatures/`에 저장합니다.
-   **검증 방법**:
    -   **동작**: 웹 앱의 서명 패드에 그림을 그리고 "Save" 버튼을 클릭합니다.
    -   **확인**: `data/signatures/` 폴더에 새로운 `.png` 파일이 생성되었는지 확인합니다.

#### **RTC (Real-Time Clock)**
-   **작동 원리**:
    1.  프론트엔드가 `GET /api/rtc`로 시간을 요청합니다.
    2.  백엔드가 `modules.sensors.rtc.get_current_time()`을 호출합니다.
    3.  현재 시간(하드웨어 RTC 또는 시스템 시간)을 반환합니다.
-   **검증 방법**:
    -   **동작**: 웹 앱을 엽니다. 로그나 화면에 시간이 표시되어야 합니다.
    -   **확인**: 브라우저에서 `http://localhost:5000/api/rtc`에 접속하여 `timestamp`가 포함된 JSON이 반환되는지 확인합니다.

#### **지문 (Fingerprint)**
-   **작동 원리**:
    1.  프론트엔드가 `POST /api/fingerprint`로 스캔을 요청합니다.
    2.  백엔드가 `modules.sensors.fingerprint`를 호출하여 센서와 통신합니다.
    3.  이미지를 캡처하고 `data/fingerprints/`에 저장합니다.
-   **검증 방법**:
    -   **동작**: 웹 앱에서 "Scan Fingerprint"를 클릭합니다.
    -   **확인**: `data/fingerprints/` 폴더에 새로운 `.pgm` 파일이 생성되었는지 확인합니다.

---

### 4.2. 원격 센서 (GPS, 카메라) - ESP32 연동

이 구성 요소들은 **PUSH** 모델을 사용합니다. ESP32-CAM이 로컬 서버로 데이터를 능동적으로 전송합니다.

#### **통신 프로토콜 (ESP32 <-> 서버)**
`esp32-cam.cpp`에 따르면, ESP32는 HTTP 클라이언트 역할을 합니다:
-   **카메라**: 이미지를 캡처하고 `http://<SERVER_IP>:5000/upload_image`로 `POST` 요청을 보냅니다.
-   **GPS**: NMEA 데이터를 읽고 `http://<SERVER_IP>:5000/upload_gps`로 `POST` 요청을 보냅니다.

#### **데이터 흐름**
1.  **ESP32**가 데이터(이미지 또는 GPS 좌표)를 캡처합니다.
2.  **ESP32**가 서버(`upload_image` 또는 `/upload_gps`)로 데이터를 전송합니다.
3.  **서버**는 이미지를 디스크에 저장하고, 최신 GPS 좌표를 메모리에 캐시합니다.
4.  **프론트엔드**가 서버(`GET /api/camera` 또는 `GET /api/gps`)를 폴링하여 최신 데이터를 표시합니다.

#### **검증 방법**
-   **카메라**:
    -   **동작**: ESP32가 켜져 있고 서버를 향해 데이터를 보내고 있는지 확인합니다.
    -   **확인**: `http://localhost:5000/api/camera`에 접속하여 최신 이미지 경로가 반환되는지 확인합니다.
-   **GPS**:
    -   **동작**: ESP32가 GPS 신호를 수신하고 데이터를 보내고 있는지 확인합니다.
    -   **확인**: `http://localhost:5000/api/gps`에 접속하여 `latitude`와 `longitude`가 포함된 JSON이 반환되는지 확인합니다.

---

### 4.3. 로컬 서버 통신 확인

로컬 서버(`server.py`)는 하드웨어(ESP32, 센서)와 사용자 인터페이스(프론트엔드) 사이의 다리 역할을 합니다.

#### **검증 스크립트**
포함된 스크립트를 실행하여 모든 상호작용을 시뮬레이션하고 서버가 정상 작동하는지 확인할 수 있습니다:

```bash
# 먼저 서버가 실행 중이어야 합니다 (python server.py)
./venv/bin/python3 verify_integration.py
```

**예상 출력:**
```text
Testing ESP32 Integration...
   Upload Image OK
   Get Camera OK: ...
   Upload GPS OK
   Get GPS OK: ...

Testing Signature Integration...
   Upload Signature OK: ...
```


---

### 4.4. 외부 서버 검증 (External Server Validation)

이 시스템은 수집된 데이터를 외부 서버로 전송하여 유효성을 검증하는 기능을 지원합니다.

#### **기능 동작**
-   **EXTERNAL_SERVER_URL 설정 시**:
    -   지문, 카메라, GPS, 서명 데이터를 해당 URL로 전송합니다.
    -   외부 서버로부터 **200 OK** 응답을 받아야만 프론트엔드에 성공을 반환합니다.
    -   응답이 200이 아니면 에러(400/500)를 반환하여 다음 단계로 넘어가지 못하게 합니다.
-   **설정되지 않음 (기본값)**:
    -   기존처럼 로컬 저장 후 즉시 성공 처리합니다. (테스트 및 개발용)

#### **설정 방법**
서버 실행 전 환경변수를 설정합니다:
```bash
export EXTERNAL_SERVER_URL="http://your-external-server.com"
python server.py
```

#### **검증 방법**
`verify_external.py` 스크립트를 사용하여 두 가지 모드(로컬/외부)가 모두 정상 작동하는지 확인할 수 있습니다.
```bash
./venv/bin/python3 verify_external.py
```
이 스크립트는 다음을 수행합니다:
1.  **로컬 모드 테스트**: 외부 URL 없이 실행하여 데이터가 정상 처리되는지 확인.
2.  **외부 모드 테스트**: 내부적으로 Mock 서버(포트 6000)를 띄우고, `EXTERNAL_SERVER_URL`을 설정하여 데이터가 Mock 서버로 전송되고 검증되는지 확인.


