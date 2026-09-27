"""开发环境配置。使用方法：

    DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py runserver
"""

from .base import *  # noqa: F401,F403

DEBUG = True

# 开发环境放宽：允许局域网内其他设备访问（手机真机调试会用到）
ALLOWED_HOSTS = ["*"]

# 开发时前端由 Vite 提供（默认 5173 端口）
CORS_ALLOWED_ORIGINS = env.list(  # noqa: F405
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
)
CORS_ALLOW_CREDENTIALS = True
