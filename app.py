from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
import httpx
from httpx import Limits, Timeout

# 환경변수 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
# OpenAI 클라이언트 설정
# client = AsyncOpenAI(api_key=api_key)

http_client = httpx.AsyncClient(
    http2=True,
    timeout=httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0),
    limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
)

client = AsyncOpenAI(api_key=api_key, http_client=http_client)

# FastAPI 앱 생성
app = FastAPI(title="Korean Words Learning API", version="1.0.0")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

# 정적 파일 서빙 (CSS, JS, 이미지 등)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    # static 디렉토리가 없는 경우 무시
    pass


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generation", response_class=HTMLResponse)
async def generation(request: Request, sentence: str = Form(...)):
    import time
    import uuid

    request_id = str(uuid.uuid4())[:8]
    print(f"[{request_id}] 요청 시작 - 받은 문장: {sentence}")

    if not sentence or sentence.strip() == "":
        print(f"[{request_id}] 빈 문장으로 인한 에러")
        return templates.TemplateResponse(
            "index.html", {"request": request, "error": "문장을 입력해주세요."}
        )

    try:
        print(f"[{request_id}] OpenAI API 호출 시작")
        start_time = time.time()

        # 비동기 OpenAI API 호출
        # 비동기 응답 뒤에 로깅 추가
        response = await client.responses.create(
            model="gpt-5-mini-2025-08-07",  # ↓ 아래 2번에서 더 경량/신형 모델로 교체 권장
            input=f"""아래 형식으로만 쓰세요.
- 한국어 단어 10개, 표 형식(머리글 포함 11행)
- 각 뜻은 10자 이내, 예문 금지
- 추가 설명 금지

문장: {sentence}""",
        )
        usage = getattr(response, "usage", None)
        if usage:
            # 출력/입력 토큰 수 확인
            print(
                f"[{request_id}] tokens in/out: {usage.input_tokens}/{usage.output_tokens}"
            )

        end_time = time.time()
        result = response.output_text
        print(f"[{request_id}] API 호출 완료 - 소요시간: {end_time - start_time:.2f}초")
        print(f"[{request_id}] 생성된 결과: {result[:100]}...")

        return templates.TemplateResponse(
            "result.html",
            {"request": request, "original_sentence": sentence, "result": result},
        )

    except Exception as e:
        print(f"[{request_id}] OpenAI API 오류: {e}")
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "original_sentence": sentence,
                "result": f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
            },
        )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5001, reload=True)
