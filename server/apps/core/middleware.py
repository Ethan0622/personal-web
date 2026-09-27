"""审计日志中间件：记录所有对 /api/ 的写操作。

老系统没有任何日志，出问题无法追溯谁改了什么。这里以最小侵入的方式补上。
日志写入失败绝不影响正常请求。
"""

import logging

logger = logging.getLogger("apps.core.audit")

ACTION_BY_METHOD = {
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}


def get_client_ip(request) -> str | None:
    """从代理头或 REMOTE_ADDR 取真实客户端 IP。"""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class AuditLogMiddleware:
    WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    # 刷新 token 太频繁，不值得记录
    SKIP_PATHS = {"/api/core/auth/refresh/"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            self._record(request, response)
        except Exception:  # pragma: no cover - 审计失败不能影响业务
            logger.exception("写入审计日志失败 path=%s", request.path)
        return response

    def _record(self, request, response) -> None:
        if request.method not in self.WRITE_METHODS:
            return
        path = request.path
        if not path.startswith("/api/") or path in self.SKIP_PATHS:
            return

        from .authentication import get_audit_user
        from .models import AuditLog

        if path.endswith("/auth/login/"):
            action = "login"
        elif path.endswith("/auth/logout/"):
            action = "logout"
        else:
            action = ACTION_BY_METHOD.get(request.method, "update")

        user = get_audit_user(request)

        AuditLog.objects.create(
            user=user,
            username=getattr(user, "username", "") if user else "",
            action=action,
            method=request.method,
            path=path[:255],
            status_code=getattr(response, "status_code", None),
            ip=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
        )
