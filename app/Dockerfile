# syntax=docker/dockerfile:1.7
# Dockerfile syntax 1.7 사용

# Multi-stage build를 활용한 최적화된 Dockerfile
# ---- Build stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# 이미지 용량과 빌드 속도를 단축시킬수 있는 환경변수 추가
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

# 의존성 파일 복사
COPY requirements.txt .

# venv에만 의존성 설치 (wheel 빌드, 런타임엔 pip 불필요)
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --no-compile --prefer-binary -r requirements.txt \
    && python -B -m pip uninstall -y pip setuptools wheel


# ---- Runtime stage ----
FROM python:3.11-slim

# 보안을 위한 non-root 유저 생성
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

WORKDIR /app

# venv만 복사
COPY --from=builder /opt/venv /opt/venv

# 애플리케이션 코드 복사
COPY --chown=appuser:appuser main.py .

# 런타임 환경변수 설정
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 애플리케이션 포트
EXPOSE 8000

# non-root 유저로 전환
USER appuser

# 헬스체크 설정 (curl 대신 python 사용)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
