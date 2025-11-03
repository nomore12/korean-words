#!/usr/bin/env python3
"""
FastAPI 서버 실행 스크립트
"""

import uvicorn
from app import app

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True, log_level="info")
