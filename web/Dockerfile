FROM python:3.12-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1) 시스템 의존성 설치 (nc 포함)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    libssl-dev \
    netcat \
    default-mysql-client \
    nginx \
  && rm -rf /var/lib/apt/lists/*

# 2) 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) 애플리케이션 코드 복사
COPY . .

# 4) collectstatic으로 STATIC_ROOT에 모으기
RUN python manage.py collectstatic --noinput

# 6) Nginx 설정 복사 (alias 경로가 /app/collected_static/)
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

# 7) 엔트리포인트 스크립트 복사 및 권한 설정
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 8) 컨테이너 시작 시 실행될 명령 지정
ENTRYPOINT ["entrypoint.sh"]
CMD ["gunicorn", "petmind.wsgi:application", "--config", "gunicorn.conf.py"]