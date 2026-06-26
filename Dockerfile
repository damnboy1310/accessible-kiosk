# 버거킹 접근성 키오스크 — 웹 빌드 (Flask + gunicorn)
FROM python:3.12-slim

WORKDIR /app

# 의존성 먼저 설치 (레이어 캐시)
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

# 앱 소스 (재사용 코어 + 웹 레이어 + 데이터)
COPY src/ ./src/
COPY web/ ./web/
COPY data/ ./data/

EXPOSE 8000

# 무상태 앱이므로 멀티 워커 OK
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "web.app:app"]
