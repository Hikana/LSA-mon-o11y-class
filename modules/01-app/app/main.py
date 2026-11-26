"""加選系統（教學用）

模擬「選課開放的 9:00」：
  加選一次 = 查課程 → 檢查衝堂 → 寫入選課紀錄
其中「檢查衝堂」要向資料庫借連線，連線池只有 DB_POOL_SIZE 條。
平常流量小時很快；流量一衝上來，大家排隊等連線，延遲就出現長尾，
等太久（> DB_WAIT_TIMEOUT 秒）就直接回 503。

METRICS_ENABLED=false（模組 01）時，只有 access log 這種「原始訊號」。
METRICS_ENABLED=true （模組 03）時，才會在 /metrics 吐出 Prometheus 格式的指標。
"""

import asyncio
import logging
import os
import random
import sys
import time

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response

METRICS_ENABLED = os.getenv("METRICS_ENABLED", "false").lower() == "true"
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "3"))
DB_WAIT_TIMEOUT = float(os.getenv("DB_WAIT_TIMEOUT", "3"))

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
access_log = logging.getLogger("access")

app = FastAPI(title="加選系統")
db_pool = asyncio.Semaphore(DB_POOL_SIZE)

COURSES = {
    "IM1001": "資料庫系統",
    "IM2002": "系統分析與設計",
    "IM3003": "網路程式設計",
    "IM4004": "資訊安全",
}

# 只有路徑本身決定 page 標籤，避免把使用者輸入放進 label（label 爆炸）
PAGES = {"/": "首頁", "/courses": "查課", "/enroll": "加選"}

if METRICS_ENABLED:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    # Traffic + Errors：每個請求 +1，用 status 區分成功／失敗
    HTTP_REQUESTS = Counter(
        "http_requests_total",
        "HTTP 請求總數",
        ["page", "status"],
    )
    # Latency：用 histogram 記錄分佈，之後才能算 p99，而不是只有平均
    HTTP_DURATION = Histogram(
        "http_request_duration_seconds",
        "HTTP 請求處理時間（秒）",
        ["page", "status"],
        buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 3, 5),
    )
    # Saturation：現在有多少請求正在處理中
    INFLIGHT = Gauge("app_inflight_requests", "正在處理中的請求數")


async def query_course(course_id: str) -> None:
    await asyncio.sleep(random.uniform(0.005, 0.02))


async def check_conflict(course_id: str) -> None:
    # 要先拿到一條 DB 連線；拿不到就排隊
    await asyncio.wait_for(db_pool.acquire(), timeout=DB_WAIT_TIMEOUT)
    try:
        await asyncio.sleep(random.uniform(0.08, 0.15))
    finally:
        db_pool.release()


async def write_enrollment(course_id: str) -> None:
    await asyncio.sleep(random.uniform(0.01, 0.03))


@app.middleware("http")
async def observe(request: Request, call_next):
    path = request.url.path
    page = PAGES.get(path)
    start = time.perf_counter()
    if METRICS_ENABLED and page:
        INFLIGHT.inc()
    try:
        response = await call_next(request)
        code = response.status_code
    except Exception:
        code = 500
        response = PlainTextResponse("internal error", status_code=500)
    finally:
        if METRICS_ENABLED and page:
            INFLIGHT.dec()
    elapsed = time.perf_counter() - start

    if page:
        # 原始訊號：一行一筆 access log（模組 01 學生用 awk 分析這個）
        access_log.info(
            "%s %s %s %d %.3f",
            time.strftime("%Y-%m-%dT%H:%M:%S"),
            request.method,
            path,
            code,
            elapsed,
        )
        if METRICS_ENABLED:
            status = "成功" if code < 400 else "失敗"
            HTTP_REQUESTS.labels(page=page, status=status).inc()
            HTTP_DURATION.labels(page=page, status=status).observe(elapsed)
    return response


@app.get("/", response_class=HTMLResponse)
async def index():
    rows = "".join(f"<li>{cid} {name}</li>" for cid, name in COURSES.items())
    return f"<h1>加選系統</h1><ul>{rows}</ul><p>POST /enroll?course=IM1001</p>"


@app.get("/courses")
async def courses():
    await query_course("*")
    return COURSES


@app.post("/enroll")
async def enroll(course: str = "IM1001"):
    if course not in COURSES:
        return JSONResponse({"ok": False, "error": "沒有這門課"}, status_code=404)
    await query_course(course)
    try:
        await check_conflict(course)
    except asyncio.TimeoutError:
        return JSONResponse({"ok": False, "error": "系統忙碌，請稍後再試"}, status_code=503)
    await write_enrollment(course)
    return {"ok": True, "course": course, "name": COURSES[course]}


@app.get("/metrics")
async def metrics():
    if not METRICS_ENABLED:
        return PlainTextResponse("metrics 尚未開啟（模組 03 才會打開）\n", status_code=404)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
