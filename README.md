# 회상 다이어리

회상 다이어리는 일상을 기록하고 회상할 수 있는 웹 애플리케이션입니다.

## 주요 기능

- 카카오 로그인
- 일기 작성 및 관리
- 프로필 관리

## 기술 스택

- Backend: Django
- Frontend: HTML, CSS, JavaScript
- Database: MySQL
- Authentication: Django REST framework, JWT

## 설치 방법

1. 저장소 클론

```bash
git clone [repository-url]
cd [repository-name]
```

2. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate      # Linux/Mac
```

3. 의존성 설치

```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
   `.env` 파일을 생성하고 다음 변수들을 설정:

```
MYSQL_DB=your_db_name
MYSQL_USER=your_db_user
MYSQL_PASSWORD=your_db_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
```

5. 데이터베이스 마이그레이션

```bash
python manage.py migrate
```

6. 서버 실행

```bash
python manage.py runserver
```

## 개발 환경 설정

1. SSL 인증서 생성

```bash
./generate-certificates.sh
```

2. HTTPS 서버 실행

```bash
python manage.py runsslserver --certificate certificates/cert.pem --key certificates/key.pem
```

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.
