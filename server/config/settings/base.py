"""Django settings - 公共配置。

敏感信息（SECRET_KEY、数据库密码等）一律从环境变量读取，
通过 server/.env 文件提供（该文件已在 .gitignore 中排除）。
"""

from datetime import timedelta
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

# server/ 目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
    CORS_ALLOWED_ORIGINS=(list, []),
    # 默认 SQLite：本地开发零配置，免去在 Windows 上编译 mysqlclient 的麻烦。
    # 生产环境在 .env 中把 DB_ENGINE 改成 django.db.backends.mysql 即可。
    DB_ENGINE=(str, "django.db.backends.sqlite3"),
    DB_NAME=(str, str(BASE_DIR / "db.sqlite3")),
    DB_USER=(str, ""),
    DB_PASSWORD=(str, ""),
    DB_HOST=(str, "127.0.0.1"),
    DB_PORT=(str, "3306"),
    ACCESS_TOKEN_MINUTES=(int, 120),
    REFRESH_TOKEN_DAYS=(int, 7),
    SITE_NAME=(str, "个人工作门户"),
)

# 读取 .env（不存在则跳过，便于用系统环境变量部署）
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(str(_env_file))

# ---------------------------------------------------------------- 基础

# SECRET_KEY 不再硬编码：必须由环境变量提供，否则直接启动失败。
SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env("DJANGO_DEBUG")

ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# 用 IP 访问，CSRF 信任来源也一并放开给配置项控制
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

SITE_NAME = env("SITE_NAME")

# ---------------------------------------------------------------- 应用

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
]

# 业务模块：新增模块时在这里追加一行即可
LOCAL_APPS = [
    "apps.core",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 审计日志：记录所有写操作，放在最后以便能拿到已认证用户
    "apps.core.middleware.AuditLogMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------- 数据库

# ─────────────────────────────────────────────── 数据库
_db_engine = env("DB_ENGINE")
_db_name = env("DB_NAME")

if not _db_name:
    if "sqlite" in _db_engine:
        # 本地开发：文件落在 server/db.sqlite3
        _db_name = str(BASE_DIR / "db.sqlite3")
    else:
        raise ImproperlyConfigured(
            "使用 MySQL 时必须配置 DB_NAME（数据库名）。请检查 server/.env 文件。"
        )

DATABASES = {
    "default": {
        "ENGINE": _db_engine,
        "NAME": _db_name,
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        "CONN_MAX_AGE": 60,
    }
}

# MySQL 需要显式指定字符集；SQLite 不接受该参数
if "mysql" in _db_engine:
    DATABASES["default"]["OPTIONS"] = {"charset": "utf8mb4"}

# ---------------------------------------------------------------- 认证

AUTH_USER_MODEL = "core.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    # 默认要求登录 + 默认拒绝（新接口不写权限类就不会对外开放）
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # 自定义实现：认证成功后把用户回填给审计中间件
        "apps.core.authentication.PortalJWTAuthentication",
    ),
    # 关键：默认权限类是门户自己的实现，而不是简单的 IsAuthenticated。
    # 它要求视图必须通过 allow_any 或 required_perms 显式声明权限，
    # 否则只能拿到"仅登录"的最低门槛 —— 且 checks.py 会就此报警。
    "DEFAULT_PERMISSION_CLASSES": ("apps.core.permissions.PortalAccessPermission",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S",
    "EXCEPTION_HANDLER": "apps.core.exceptions.portal_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.PortalPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env("ACCESS_TOKEN_MINUTES")),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env("REFRESH_TOKEN_DAYS")),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "个人工作门户 API",
    "DESCRIPTION": "模块化单体架构：门户外壳 + 各业务模块独立路由",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
}

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")

# ---------------------------------------------------------------- 国际化

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
# 老项目这里是 False，导致时间处理容易出错；统一改为 True（Django 5 推荐）
USE_TZ = True

# ---------------------------------------------------------------- 静态与媒体

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# 老项目把 collectstatic 产物提交进了仓库（8.3MB），现在改为运行时生成
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------- 日志

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
