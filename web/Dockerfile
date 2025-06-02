# 1. 파이썬 이미지
FROM python:3.12-bullseye

# 2. 기본 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# ✅ 3. mysqlclient 설치에 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
  gcc \
  default-libmysqlclient-dev \
  libssl-dev \
  && rm -rf /var/lib/apt/lists/*

# 4. requirements.txt 복사 후 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 전체 프로젝트 복사
COPY . .

# 6. collectstatic 등 필요 작업
RUN python manage.py collectstatic --noinput

# 7. 실행
CMD ["gunicorn", "petmind.wsgi:application", "--config", "gunicorn.conf.py"]