"""DRF 权限类。

**默认拒绝**是本模块的核心纪律：
- 视图要么声明 `allow_any = True`（公开接口）
- 要么声明 `required_perms = [...]`（需要特定权限码）
- 两者都没有时，仅要求登录 —— 且 `checks.py` 会在启动时给出警告

老系统的根因就是「教师专属接口忘了加权限类」，这里把这条规则变成了
「不写就报警」的机制，而不是靠人记得。
"""

from rest_framework.permissions import BasePermission

from .perms import PermCode


class PortalAccessPermission(BasePermission):
    """门户统一权限校验。已设为 DRF 的默认权限类。"""

    message = "你没有执行该操作的权限"

    def has_permission(self, request, view):
        # 1) 显式标记为公开接口
        if getattr(view, "allow_any", False):
            return True

        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated or not user.is_active:
            return False

        # 2) 声明的权限码必须全部持有
        required = getattr(view, "required_perms", None)
        if required:
            return all(user.has_perm_code(code) for code in required)

        # 3) 未声明 → 仅要求登录。这种情况会被系统检查提示，便于补全
        return True


class IsSuperAdmin(BasePermission):
    """仅超级管理员。"""

    message = "仅超级管理员可执行该操作"

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.has_perm_code("*")
        )


class HasPerms(BasePermission):
    """在视图上声明 `required_perms` 即可使用的通用权限类。

    用于显式写法：permission_classes = [IsAuthenticated, HasPerms]
    """

    def has_permission(self, request, view):
        required = getattr(view, "required_perms", None)
        user = getattr(request, "user", None)
        if not required:
            return False  # 未声明权限码 → 拒绝
        if user is None or not user.is_authenticated or not user.is_active:
            return False
        return all(user.has_perm_code(code) for code in required)


class ActionPermsMixin:
    """按 action 声明权限码的 Mixin（供 ViewSet 使用）。

    用法：
        class FooViewSet(ActionPermsMixin, viewsets.ModelViewSet):
            PERMS_BY_ACTION = {
                "list": ["foo.view"],
                "create": ["foo.manage"],
            }
            default_perms = ["foo.view"]
    """

    PERMS_BY_ACTION: dict[str, list[str]] = {}
    default_perms: list[str] = []

    def initial(self, request, *args, **kwargs):
        # ViewSetMixin 在调用 initial() 之前已设置好 self.action
        try:
            action = self.action
        except AttributeError:
            action = ""
        self.required_perms = list(
            self.PERMS_BY_ACTION.get(action, self.default_perms)
        )
        super().initial(request, *args, **kwargs)


class IsObjectOwner(BasePermission):
    """对象级归属校验（供业务模块复用）。

    用法：视图设置 owner_field = "user"（支持点号路径，如 "test.user"），
    非门户管理员只能操作属于自己的对象。

    这是老系统最严重的漏洞类型（任何学生可查看/篡改他人考试记录），
    这里提供一个开箱即用的基类，避免业务模块再漏掉。
    """

    message = "你只能操作属于自己的数据"
    owner_field = "user"

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.has_perm_code(PermCode.PORTAL_USER_MANAGE):
            return True
        field = getattr(view, "owner_field", self.owner_field)
        target = obj
        for part in field.split("."):
            target = getattr(target, part, None)
            if target is None:
                return False
        return target == user
