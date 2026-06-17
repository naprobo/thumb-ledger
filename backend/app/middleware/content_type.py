"""
请求 Content-Type 校验中间件。
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse

BODY_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SUPPORTED_CONTENT_TYPES = {
    "application/json",
    "multipart/form-data",
    "application/x-www-form-urlencoded",
}


def request_declares_body(request: Request) -> bool:
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            return int(content_length) > 0
        except ValueError:
            return True
    return "transfer-encoding" in request.headers


def is_supported_content_type(content_type: str | None) -> bool:
    if not content_type:
        return False
    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type in SUPPORTED_CONTENT_TYPES


async def reject_unexpected_content_type(request: Request, call_next):
    if request.method in BODY_METHODS and request_declares_body(request):
        if not is_supported_content_type(request.headers.get("content-type")):
            return JSONResponse(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                content={
                    "detail": "Unsupported Content-Type",
                    "code": "UNSUPPORTED_CONTENT_TYPE",
                },
            )
    return await call_next(request)
