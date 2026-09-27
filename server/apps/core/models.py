"""门户外壳的数据模型：统一用户、权限、外链入口、审计日志。"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from .perms import ROLE_CHOICES, ROLE_DEFAULT_PERMS, WILDCARD, PermCode, Role


class ModulePermission(models.Model):
    """权限项。由数据迁移按 perms.PERMISSION_CATALOG 自动同步。"""

    code = models.CharField("权限码", max_length=64, unique=True)
    name = models.CharField("显示名", max_length=64)
    module = models.CharField("所属模块", max_length=64, default="门户外壳")
    order = models.IntegerField("排序", default=100)

    class Meta:
        verbose_name = "权限项"
        verbose_name_plural = "权限项"
        ordering = ["order", "code"]

    def __str__(self) -> str:
        return f"{self.name}（{self.code}）"


class UserManager(BaseUserManager):
    """自定义用户管理器。

    注意：与老系统的关键差异 —— `role` 只能由服务端代码指定，
    绝不接受客户端传参（老系统正是因为可传 type=1 而能注册成管理员）。
    """

    use_in_migrations = True

    def _create_user(self, username: str, password: str | None, **extra_fields):
        if not username:
            raise ValueError("必须提供账号")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.STAFF)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields["role"] = Role.SUPERADMIN
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True
        return self._create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """统一用户。整个门户只有这一张用户表，所有模块共用。"""

    username = models.CharField("账号", max_length=64, unique=True)
    real_name = models.CharField("姓名", max_length=64, blank=True, default="")
    email = models.EmailField("邮箱", max_length=254, blank=True, default="")
    phone = models.CharField("手机号", max_length=20, blank=True, default="")

    role = models.CharField("角色", max_length=16, choices=ROLE_CHOICES, default=Role.STAFF)

    # 角色默认权限之外的额外授权，用于精细放权
    extra_perms = models.ManyToManyField(
        ModulePermission,
        blank=True,
        related_name="users",
        verbose_name="额外权限",
    )

    is_active = models.BooleanField("账号启用", default=True)
    is_staff = models.BooleanField("可登录后台", default=False)
    date_joined = models.DateTimeField("创建时间", default=timezone.now)
    last_login_ip = models.GenericIPAddressField("最后登录IP", null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.real_name or self.username

    # ---------------------------------------------------------- 权限

    @property
    def effective_perms(self) -> set[str]:
        """角色默认权限 ∪ 额外授权。"""
        perms = set(ROLE_DEFAULT_PERMS.get(self.role, set()))
        perms.update(self.extra_perms.values_list("code", flat=True))
        return perms

    def has_perm_code(self, code: str) -> bool:
        """判断是否持有某个权限码。superadmin 持有通配符，恒为真。"""
        if not self.is_active:
            return False
        perms = self.effective_perms
        return WILDCARD in perms or code in perms

    def has_any_perm(self, codes) -> bool:
        return any(self.has_perm_code(c) for c in codes)

    @property
    def is_portal_admin(self) -> bool:
        """是否具备门户管理能力（可管理用户与外链）。"""
        return self.has_perm_code(PermCode.PORTAL_USER_MANAGE)


class ExternalLink(models.Model):
    """外链入口。

    这就是用户说的"留个口子"——新增一个外部平台入口不需要改前端代码，
    在后台添加一条记录即可。前端只负责渲染卡片。
    """

    title = models.CharField("名称", max_length=64)
    url = models.CharField("地址", max_length=512)
    icon = models.CharField(
        "图标", max_length=64, default="link",
        help_text="Quasar 图标名，如 open_in_new、school、restaurant",
    )
    description = models.CharField("说明", max_length=255, blank=True, default="")
    category = models.CharField("分组", max_length=32, blank=True, default="常用入口")
    order = models.IntegerField("排序", default=100)
    is_active = models.BooleanField("启用", default=True)
    open_in_new_tab = models.BooleanField("新标签页打开", default=True)
    required_perm = models.CharField(
        "所需权限码", max_length=64, default=PermCode.PORTAL_LINKS_VIEW,
        help_text="持有该权限的用户才能看到此入口",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "外链入口"
        verbose_name_plural = "外链入口"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title


class AuditLog(models.Model):
    """审计日志。老系统完全没有这一层，出问题时无法追溯。"""

    ACTION_CHOICES = [
        ("create", "新增"),
        ("update", "修改"),
        ("delete", "删除"),
        ("login", "登录"),
        ("logout", "登出"),
    ]

    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="audit_logs", verbose_name="操作人",
    )
    # 冗余保存账号名，用户被删除后仍可追溯
    username = models.CharField("操作人账号", max_length=64, blank=True, default="")
    action = models.CharField("动作", max_length=16, choices=ACTION_CHOICES)
    method = models.CharField("HTTP 方法", max_length=8, blank=True, default="")
    path = models.CharField("请求路径", max_length=255, blank=True, default="")
    status_code = models.IntegerField("响应状态码", null=True, blank=True)
    ip = models.GenericIPAddressField("来源IP", null=True, blank=True)
    user_agent = models.CharField("User-Agent", max_length=255, blank=True, default="")
    detail = models.TextField("详情", blank=True, default="")
    created_at = models.DateTimeField("时间", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "审计日志"
        verbose_name_plural = "审计日志"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.username} {self.action} {self.path}"
