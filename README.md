# STUDY CARE AI

Python Flask와 Scikit-learn으로 만든 AI 맞춤형 학습·건강 관리 웹앱 프로토타입입니다.

## 1. 실행 환경
- Python 3.10 이상 권장
- 인터넷 연결(최초 라이브러리 설치 및 Chart.js CDN 사용 시)

## 2. 설치 및 실행

### Windows
프로젝트 폴더에서 터미널(CMD 또는 PowerShell)을 열고 아래 명령어를 순서대로 실행하세요.

```bash
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py app.py
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

브라우저에서 아래 주소를 엽니다.

http://127.0.0.1:5000

서버를 종료하려면 터미널에서 Ctrl + C를 누릅니다.

## 3. 주요 기능
- 학습·건강 데이터 입력
- Scikit-learn RandomForestRegressor 분석
- 후보 학습 시간별 예측값 비교 후 개인별 학습 블록 추천
- 학습 타이머
- 집중도·피로도·자세 자가 체크와 피드백
- SQLite 학습 기록 저장
- 정답률 및 예측 점수 그래프

## 4. AI에 관한 중요한 안내
현재 모델은 동작 시연을 위해 생성한 합성 데이터로 학습됩니다. 따라서 실제 학생 집단에서 검증된 예측 모델이 아니며, 예측 점수는 실제 시험 점수나 집중력을 의미하지 않습니다. 과학적 타당성을 주장하려면 적절한 동의와 개인정보 보호 절차를 거쳐 수집한 실제 데이터를 확보하고, 별도의 검증 데이터로 성능을 평가해야 합니다.

현재 실시간 상태 확인은 웹캠·생체 센서가 아니라 사용자가 직접 입력하는 자가 체크 방식입니다. 의료 진단 용도로 사용하면 안 됩니다.

## 5. 개인정보
기록은 실행한 컴퓨터의 `study_care.db` 파일에 로컬 저장됩니다. 시연할 때는 실제 이름, 학교, 민감한 건강정보를 입력하지 않는 것을 권장합니다.
