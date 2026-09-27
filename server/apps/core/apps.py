from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "门户外壳"

    def ready(self):
        # 注册系统检查（未声明权限的接口会报警）
        from . import checks  # noqa: F401
