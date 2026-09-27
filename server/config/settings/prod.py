"""生产环境配置。使用方法：

    DJANGO_SETTINGS_MODULE=config.settings.prod gunicorn config.wsgi:application
"""

from .base import *  # noqa: F401,F403

DEBUG = False

# 生产环境的安全基线：老项目这些一项都没有配置
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# 用 IP + HTTP 访问时以下两项必须保持关闭（否则浏览器会拒绝 Cookie / 强制跳 HTTPS）。
# 将来备案完成、上了域名和 HTTPS 后，把这两个环境变量置为 True 即可。
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)  # noqa: F405
SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=False)  # noqa: F405
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=False)  # noqa: F405

# 反向代理后取真实客户端 IP（Nginx 转发时用得到）
USE_X_FORWARDED_HOST = True
if env.bool("DJANGO_BEHIND_TLS_PROXY", default=False):  # noqa: F405
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
