# AuthBox Frontend Guide

이 디렉터리는 AuthBox(=아두이노센트) 인증 키트의 터치 UI를 담당하는 Svelte + Vite 프로젝트입니다. `npm create vite@latest -- --template svelte` 템플릿을 기반으로 하며, `appendix/기획서.pdf`, `appendix/Project 부품 명세서_팀별.pdf`, `appendix/창의적 공학설계 - 2주차_part1_SRS.pdf` 의 요구사항을 반영해 기본 진행 순서 및 해상도를 정리합니다.

## 프로젝트 요약

- 목표: 수취인이 직접 지문, 위치, 서명, 영상, 실시간 퀴즈 등 다중 인증을 수행해 사전 합의된 송금 시점을 증명 (`appendix/기획서.pdf` 3–4p).
- 백엔드: 인증 데이터를 `main.py`가 센서에서 수집해 서버로 전송.
- 프론트엔드 역할: 라즈베리파이 + 5인치 800×480 터치스크린에서 인증 흐름을 안내하고 각 센서 스크립트를 순서대로 구동할 사용자 인터페이스를 제공.

## 하드웨어·해상도 기준

- 디스플레이: SunFounder 5″ HDMI 터치 모듈, 800×480 고정 해상도 (`appendix/Project 부품 명세서_팀별.pdf` 7번 항목).
- 메인 컨트롤러: Raspberry Pi 3 Model B+ (`appendix/Project 부품 명세서_팀별.pdf` 8번 항목).
- 센서 모듈: ESP32-CAM(영상), AS608 지문 센서, 0.96″ OLED, Grove RTC, micro SD shield, NEO-6M GPS 등 (항목 1–6).

프론트엔드는 480px 세로 공간을 기준으로 화면을 설계하고, 10mm 이상 터치 목표, 대비 높은 폰트(최소 18px 이상)를 유지합니다. 인증 중 필요한 하드웨어 상태(센서 연결, GPS 수신 등)를 시각적으로 노출해 IoT 상태를 즉시 확인할 수 있게 합니다.

## 주요 화면 순서

문서의 인증 플로(`기획서.pdf` 4p)와 하드웨어 구성을 기반으로 다음 6단계 기본 화면을 권장합니다.

1. **대기/세션 선택** – 사전 합의된 송금 시간 및 세션 ID 확인, 네트워크/배터리 표시.
2. **인증 준비 체크리스트** – 센서 연결상태(지문, 카메라, GPS, RTC, 서명 패드, OLED 메시지)를 표시하고 `main.py` 사전 진단 실행.
3. **다중 인증 단계** – 탭 또는 순차 진행:
   - 3-1 지문 캡처
   - 3-2 실시간 영상/사진 (ESP32-CAM)
   - 3-3 뉴스/시각 퀴즈 응답
   - 3-4 GPS 위치 확인
   - 3-5 서명 작성
4. **데이터 검토 & 동의** – 캡처된 썸네일, 위치, 타임스탬프, 사용자 동의 체크박스.
5. **서버 전송** – 전송 진행 상태 + 백엔드 응답 로그.
6. **송금자 알림 안내** – 성공 여부, 재시도 옵션, 송금 수행 안내.

각 단계는 800×480의 세로 스크롤 없이 한 화면에서 완료되도록 레이아웃을 구성하고, 단계 상단에 진행률(예: “3/6”)을 노출합니다.

## 센서 연동 및 `main.py` 실행 시점

프론트엔드는 센서 제어를 직접 수행하지 않고, 루트 디렉터리의 `main.py`를 단계별로 호출합니다. Vite 앱에서 IPC(예: Python REST, gRPC, 혹은 로컬 HTTP 브릿지)를 열어 아래 명령을 실행하도록 연결하세요.

| UI 단계 | 호출 모듈 | 예시 명령 | 설명 |
| --- | --- | --- | --- |
| 준비 체크리스트 | `rtc` | `python3 main.py rtc --auto-backend --base-url <URL>` | RTC 동기화, 서버와 연결 확인 |
| 지문 캡처 | `fingerprint` | `python3 main.py fingerprint --image-dir /data/fingerprints --timeout 15 --auto-backend` | 이미지 저장 후 백엔드 전송 |
| 서명 입력 | `signature` | `python3 main.py signature --signature-dir /data/signatures --auto-backend` | 디지타이저 입력 완료 후 전송 |

추가 센서(카메라, GPS 등)는 모듈이 준비되는 대로 `main.py`에 새로운 `module` 인자를 확장하고, 프론트엔드에서 동일한 방식으로 호출합니다. 전송에 필요한 `--api-key`, `--metadata-endpoint`, `--file-endpoint`는 UI에서 설정 화면을 통해 주입하면 됩니다.

## 개발 환경

```bash
cd frontend
npm install
npm run dev -- --host   # http://localhost:5173에서 터미널 로그 확인
```

프로덕션 빌드는 아래 명령으로 생성합니다.

```bash
npm run build
npm run preview         # 라즈베리파이 배포 전에 확인
```

라즈베리파이에 배포할 때는 `dist/`를 copy하고 `npm ci && npm run build`를 선호합니다. 5″ 화면에 맞는 뷰포트 강제 설정(`meta viewport width=800`)과 Kiosk 모드 브라우저(Chromium --kiosk)를 함께 설정하세요.

## 요구사항 체크리스트

`창의적 공학설계 - 2주차_part1_SRS.pdf`에 따라 기능/비기능 요구사항을 명확히 정의하고, 팀 공통 어휘를 README 상단에 유지합니다. 권장 체크 목록:

- 기능 요구사항: 각 인증 단계에서 입력/출력 데이터와 예외 처리 명세.
- 비기능 요구사항: 응답 시간(센서 호출 후 3초 내 피드백), 사용성(지문 센서 재시도 안내), 신뢰성(백엔드 오류 시 로컬 캐시).
- 명세서 정합성: 프론트엔드와 `main.py` 사이의 인터페이스 버전, 데이터 스키마(JSON 키 이름 등)를 버전 관리.

## 참고 문서

- `appendix/기획서.pdf` – 프로젝트 배경과 인증 흐름
- `appendix/Project 부품 명세서_팀별.pdf` – 하드웨어/해상도/센서 명세
- `appendix/창의적 공학설계 - 2주차_part1_SRS.pdf` – 요구사항 수립 가이드
