# 프로젝트 설정 및 사용 가이드

## 1. 환경 설정 (Environment Setup)

이 프로젝트를 실행하기 위해서는 Python 가상환경을 설정하고 필요한 패키지들을 설치해야 합니다.

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
(Linux/Mac 사용자는 `python3 server.py`를 사용해야 할 수도 있습니다.)

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
