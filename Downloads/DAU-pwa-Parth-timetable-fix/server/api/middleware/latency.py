# Logs per-stage timings for /chat without blocking the response.
import logging
import time

from fastapi import FastAPI
from fastapi.background import BackgroundTasks

from db.connection import execute
from pipeline.latency_tracker import init_tracker, reset_tracker

logger = logging.getLogger(__name__)


def register_latency_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def log_latency_middleware(request, call_next):
        if request.url.path not in ("/chat", "/chat/stream"):
            return await call_next(request)

        data, token = init_tracker()
        t0 = time.time()
        try:
            response = await call_next(request)
            bg_tasks = BackgroundTasks()

            def _write_log():
                # Runs after the response body finishes sending, so total_time
                # covers the full stream for /chat/stream (measuring at
                # call_next return would only cover time-to-first-byte).
                total_time = time.time() - t0
                try:
                    execute(
                        "INSERT INTO latency_logs "
                        "(guardrail_time, retrieval_time, generation_time, total_time) "
                        "VALUES (%s, %s, %s, %s)",
                        (
                            data.get("guardrail_time", 0.0),
                            data.get("retrieval_time", 0.0),
                            data.get("generation_time", 0.0),
                            total_time,
                        ),
                    )
                except Exception as e:
                    logger.warning("[latency_middleware] Failed to log latency: %s", e)

            bg_tasks.add_task(_write_log)
            response.background = bg_tasks
            return response
        finally:
            reset_tracker(token)
