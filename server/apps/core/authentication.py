"""自定义认证。

解决的问题：DRF 的认证发生在视图内部，而审计中间件运行在更外层，
因此中间件拿到的 `request.user` 永远是匿名用户，导致所有 JWT 请求
在审计日志里都记不到操作人。

这里在认证成功后把用户"回填"到外层 Django 请求上，供中间件读取。
"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework_simplejwt.authentication import JWTAuthentication

# 回填到 Django HttpRequest 上的属性名
AUDIT_USER_ATTR = "audit_user"


def set_audit_user(request, user) -> None:
    """把当前用户登记到外层请求上（登录等无认证类的接口需要手动调用）。"""
    target = getattr(request, "_request", request)
    setattr(target, AUDIT_USER_ATTR, user)


def get_audit_user(request):
    """从外层请求读取当前用户，取不到则回退到 request.user。"""
    user = getattr(request, AUDIT_USER_ATTR, None)
    if user is not None:
        return user
    candidate = getattr(request, "user", None)
    if candidate is not None and getattr(candidate, "is_authenticated", False):
        return candidate
    return None


class PortalJWTAuthentication(JWTAuthentication):
    """在标准 JWT 认证的基础上回填用户，使审计中间件能记录操作人。"""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user, _token = result
            set_audit_user(request, user)
        return result


class PortalJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """让接口文档能正确显示 Bearer 认证。

    自定义认证类必须注册这个扩展，否则 drf-spectacular 生成 schema 时会告警。
    """

    target_class = "apps.core.authentication.PortalJWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
