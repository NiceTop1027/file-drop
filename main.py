"""
간단한 파일 업로드 · 공유 서비스
실행: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
META_PATH = UPLOAD_DIR / "meta.json"
STATIC_DIR = BASE_DIR / "static"

MAX_BYTES = 50 * 1024 * 1024  # 50MB
ID_LEN = 8

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="File Share", version="1.0.0")


def load_meta() -> dict:
    if META_PATH.exists():
        try:
            return json.loads(META_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_meta(meta: dict) -> None:
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def new_id() -> str:
    meta = load_meta()
    while True:
        fid = secrets.token_urlsafe(6)[:ID_LEN]
        fid = re.sub(r"[^A-Za-z0-9]", "x", fid)
        if fid not in meta:
            return fid


def safe_name(name: str) -> str:
    name = os.path.basename(name or "file")
    name = re.sub(r"[^\w.\-가-힣 ]+", "_", name).strip() or "file"
    return name[:180]


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "파일명이 없습니다.")

    data = await file.read()
    if not data:
        raise HTTPException(400, "빈 파일입니다.")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "파일 크기 제한(50MB)을 초과했습니다.")

    fid = new_id()
    orig = safe_name(file.filename)
    dest = UPLOAD_DIR / f"{fid}__{orig}"
    dest.write_bytes(data)

    meta = load_meta()
    meta[fid] = {
        "id": fid,
        "filename": orig,
        "stored": dest.name,
        "size": len(data),
        "content_type": file.content_type or "application/octet-stream",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    save_meta(meta)

    return {
        "id": fid,
        "filename": orig,
        "size": len(data),
        "url": f"/s/{fid}",
        "download": f"/api/download/{fid}",
    }


@app.get("/api/info/{fid}")
async def info(fid: str):
    meta = load_meta().get(fid)
    if not meta:
        raise HTTPException(404, "파일을 찾을 수 없습니다.")
    return {
        "id": fid,
        "filename": meta["filename"],
        "size": meta["size"],
        "content_type": meta.get("content_type"),
        "created_at": meta.get("created_at"),
        "download": f"/api/download/{fid}",
    }


@app.get("/api/download/{fid}")
async def download(fid: str):
    meta = load_meta().get(fid)
    if not meta:
        raise HTTPException(404, "파일을 찾을 수 없습니다.")
    path = UPLOAD_DIR / meta["stored"]
    if not path.exists():
        raise HTTPException(404, "파일이 삭제되었습니다.")
    return FileResponse(
        path,
        filename=meta["filename"],
        media_type=meta.get("content_type") or "application/octet-stream",
    )


@app.get("/s/{fid}", response_class=HTMLResponse)
async def share_page(fid: str):
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health():
    return {"ok": True, "files": len(load_meta())}


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
