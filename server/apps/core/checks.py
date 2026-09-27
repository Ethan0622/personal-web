"""启动时检查：防止重演老系统"忘了给接口加权限"的问题。

Django 的 check 框架会在 runserver / migrate / check 时自动执行，
发现未声明权限的接口会给出警告（不阻断启动，便于开发期发现并补全）。
"""

import importlib
import inspect
import logging

from django.apps import apps
from django.core.checks import Tags, Warning, register
from rest_framework.views import APIView

logger = logging.getLogger("apps.core.checks")


@register(Tags.security, deploy=False)
def check_api_views_declare_perms(app_configs, **kwargs):
    """检查业务模块中的 APIView 是否声明了权限。

    合格标准（满足其一）：
      1. allow_any = True          → 明确的公开接口
      2. required_perms = [...]    → 声明了所需权限码
      3. permission_classes 显式包含自定义权限类
    """
    warnings = []
    if app_configs is None:
        app_configs = apps.get_app_configs()

    for app_config in app_configs:
        if not app_config.name.startswith("apps."):
            continue
        views_module_name = f"{app_config.name}.views"
        try:
            module = importlib.import_module(views_module_name)
        except ModuleNotFoundError:
            continue

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if not issubclass(obj, APIView) or obj is APIView:
                continue
            if obj.__module__ != views_module_name:
                continue
            if getattr(obj, "allow_any", False):
                continue
            if getattr(obj, "required_perms", None):
                continue
            # ViewSet 用 PERMS_BY_ACTION 按动作声明权限，同样视为合格
            if getattr(obj, "PERMS_BY_ACTION", None):
                continue

            declared = getattr(obj, "permission_classes", None)
            if declared:
                # 显式声明了权限类（含自定义的）视为合格
                from .permissions import PortalAccessPermission
                from rest_framework.permissions import IsAuthenticated

                if any(p not in (PortalAccessPermission, IsAuthenticated) for p in declared):
                    continue

            warnings.append(
                Warning(
                    f"{app_config.name}.views.{name} 未声明权限。",
                    hint=(
                        "请设置 required_perms = ['模块.资源.动作']（需特定权限），"
                        "或设置 allow_any = True（公开接口）。"
                        "默认拒绝是本项目的安全基线。"
                    ),
                    obj=obj,
                    id="core.W001",
                )
            )
    return warnings
