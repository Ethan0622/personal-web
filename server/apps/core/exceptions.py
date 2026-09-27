"""统一异常响应格式。

前端只需按 { code, message, errors } 三个字段处理，
不必再针对不同接口写不同的错误解析逻辑。
"""

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("apps.core")

# HTTP 状态码 → 语义化 code
CODE_BY_STATUS = {
    400: "bad_request",
    401: "unauthorized",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    429: "too_many_requests",
    500: "server_error",
}


def _first_message(data) -> str:
    """从 DRF 的嵌套错误结构中提取第一条可读消息。"""
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        for item in data:
            msg = _first_message(item)
            if msg:
                return msg
        return ""
    if isinstance(data, dict):
        for value in data.values():
            msg = _first_message(value)
            if msg:
                return msg
        return ""
    return str(data)


def portal_exception_handler(exc, context):
    """在 DRF 默认处理的基础上，统一响应结构。"""
    # Django 原生校验异常转成 DRF 的，以便统一处理
    if isinstance(exc, DjangoValidationError):
        exc = DRFValidationError(getattr(exc, "messages", [str(exc)]))

    response = drf_exception_handler(exc, context)

    if response is None:
        # 未捕获异常：记录完整堆栈，交给 Django 返回 500，不向客户端泄露细节
        view = context.get("view")
        logger.exception("未处理异常 view=%s", view.__class__.__name__ if view else "?")
        return None

    if isinstance(exc, Http404):
        code, message = "not_found", "资源不存在"
    else:
        status_code = getattr(response, "status_code", None)
        code = getattr(exc, "default_code", None) or CODE_BY_STATUS.get(status_code, "error")
        # detail 是字符串时优先用它，否则从嵌套结构中提取
        raw = response.data
        if isinstance(raw, str):
            message = raw
        elif isinstance(raw, dict) and len(raw) == 1 and "detail" in raw:
            message = str(raw["detail"])
        else:
            message = _first_message(raw)

        if not message:
            message = "请求处理失败"
        if isinstance(exc, PermissionDenied) and message == "请求处理失败":
            message = "你没有执行该操作的权限"

    errors = response.data if isinstance(response.data, (dict, list)) else {"detail": response.data}
    response.data = {"code": code, "message": message, "errors": errors}
    return response
