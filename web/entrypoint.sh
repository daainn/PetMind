#!/usr/bin/env bash
set -e

# 1) DB 준비 대기 (wait-for-it, nc 등)
until nc -z $DB_HOST $DB_PORT; do
  echo "Waiting for database..."
  sleep 2
done

# 2) 마이그레이션
python manage.py migrate --noinput

# 3) 정적 파일 수집
python manage.py collectstatic --noinput

# 4) 애플리케이션 실행
exec "$@"