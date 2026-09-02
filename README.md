# File Drop — 파일 업로드 · 공유 서비스

브라우저에서 파일을 올리면 짧은 공유 링크가 생성됩니다.

## 기능

- 드래그 앤 드롭 / 클릭 업로드
- 파일당 고유 ID (`/s/{id}`) 공유 링크
- 링크를 아는 사람만 다운로드
- 최대 50MB
- 별도 DB 없이 `uploads/meta.json`에 메타데이터 저장

## 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

브라우저에서 http://127.0.0.1:8000 을 엽니다.

## API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 업로드 UI |
| POST | `/api/upload` | multipart `file` 업로드 |
| GET | `/api/info/{id}` | 파일 메타 |
| GET | `/api/download/{id}` | 다운로드 |
| GET | `/s/{id}` | 공유 페이지 |

## 주의

로컬/개인 프로토타입니다. 인증·만료·바이러스 검사는 없습니다. 공개 배포 시 인증, HTTPS, 용량/만료 정책, 스토리지(S3 등)를 추가하세요.
