# Defense-in-depth security response headers for the FastAPI backend.
#
# Pure-ASGI (not BaseHTTPMiddleware) so headers are appended on the
# http.response.start event without ever touching or buffering the response
# body — SSE (text/event-stream) responses such as /chat/stream stream through
# untouched. The backend is also reachable directly at /backend/ through nginx,
# so these headers are set at the app layer as well, not only at the edge.
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                # setdefault: never clobber a header a handler set deliberately.
                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("X-Frame-Options", "DENY")
                headers.setdefault("Referrer-Policy", "no-referrer")
                # SEC-01 fix: this backend is directly reachable at /backend/
                # (see nginx config), bypassing the Next.js layer entirely, so
                # the CSP set in next.config.mjs never applies to those
                # requests. This API only ever returns JSON/SSE — it never
                # serves HTML/JS/CSS itself — so the policy can be maximally
                # strict: no script/style/frame sources of any kind.
                headers.setdefault(
                    "Content-Security-Policy",
                    "default-src 'none'; "
                    "base-uri 'none'; "
                    "frame-ancestors 'none'; "
                    "form-action 'none'"
                )
            await send(message)

        await self.app(scope, receive, send_with_headers)
