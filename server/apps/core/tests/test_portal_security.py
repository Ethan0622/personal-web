"""门户外壳与权限体系的回归测试。

这些用例的主要目的不是覆盖率，而是**把老系统踩过的坑固化下来**：
每一条 TestCase 都对应一个当年真实存在的漏洞类型，
将来任何人（包括几个月后的你自己）改动代码时，一旦重新引入同类问题会立刻失败。
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.core.perms import PermCode, Role
from apps.core.models import ExternalLink

User = get_user_model()

PASSWORD = "portal-test-pass-123"


class PortalTestCase(TestCase):
    """公共夹具：一个超管、一个普通成员、一个访客。"""

    @classmethod
    def setUpTestData(cls):
        cls.superadmin = User.objects.create_superuser(
            username="root", password=PASSWORD, real_name="超级管理员"
        )
        cls.staff = User.objects.create_user(
            username="staff", password=PASSWORD, real_name="普通成员"
        )
        cls.guest = User.objects.create_user(
            username="guest", password=PASSWORD, real_name="访客", role=Role.GUEST
        )

    def setUp(self):
        self.client = APIClient()

    def login(self, username, password=PASSWORD):
        response = self.client.post(
            "/api/core/auth/login/", {"username": username, "password": password}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return response.data


# ══════════════════════════════════════════════════ 认证


class AuthTests(PortalTestCase):
    def test_login_success_returns_tokens_and_perms(self):
        data = self.login("root")
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertEqual(data["user"]["role"], Role.SUPERADMIN)
        # 超管持有通配符权限
        self.assertIn("*", data["user"]["perms"])

    def test_login_wrong_password_rejected(self):
        response = self.client.post(
            "/api/core/auth/login/",
            {"username": "root", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        # 不区分"账号不存在"与"密码错误"，防止账号枚举
        self.assertEqual(response.data["message"], "账号或密码错误")

    def test_login_unknown_user_gives_same_message(self):
        """账号不存在时应返回与密码错误完全相同的提示。"""
        response = self.client.post(
            "/api/core/auth/login/",
            {"username": "no-such-user", "password": "whatever"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["message"], "账号或密码错误")

    def test_inactive_user_cannot_login(self):
        self.staff.is_active = False
        self.staff.save(update_fields=["is_active"])
        response = self.client.post(
            "/api/core/auth/login/",
            {"username": "staff", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_anonymous_cannot_read_me(self):
        response = self.client.get("/api/core/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_me_returns_own_permissions(self):
        self.login("staff")
        response = self.client.get("/api/core/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(PermCode.PORTAL_VIEW, response.data["perms"])
        # 普通成员不应拥有管理权限
        self.assertNotIn(PermCode.PORTAL_USER_MANAGE, response.data["perms"])

    def test_change_own_password(self):
        self.login("staff")
        response = self.client.post(
            "/api/core/auth/change-password/",
            {"old_password": PASSWORD, "new_password": "brand-new-pass-456"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.check_password("brand-new-pass-456"))

    def test_change_password_requires_correct_old_password(self):
        self.login("staff")
        response = self.client.post(
            "/api/core/auth/change-password/",
            {"old_password": "not-the-old-one", "new_password": "brand-new-pass-456"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.check_password(PASSWORD))

    def test_logout_blacklists_refresh_token(self):
        data = self.login("staff")
        response = self.client.post(
            "/api/core/auth/logout/", {"refresh": data["refresh"]}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        # 已拉黑的 refresh token 不能再换 access
        self.client.credentials()
        reused = self.client.post(
            "/api/core/auth/refresh/", {"refresh": data["refresh"]}, format="json"
        )
        self.assertEqual(reused.status_code, 401)


# ══════════════════════════════════════════════════ 权限（回归重点）


class PermissionRegressionTests(PortalTestCase):
    """对应老系统的权限漏洞，每一条都是一个曾经真实存在的攻击面。"""

    def test_公开接口不含用户列表(self):
        """老系统 GET /api/users/user_list/ 是 AllowAny，会泄露全部学生信息。

        现在 /api/core/users/ 必须登录且需要权限。
        """
        response = self.client.get("/api/core/users/")
        self.assertEqual(response.status_code, 401)

    def test_普通成员不能查看用户列表(self):
        self.login("staff")
        response = self.client.get("/api/core/users/")
        self.assertEqual(response.status_code, 403)

    def test_普通成员不能创建用户(self):
        """老系统可 POST type=1 注册成管理员。"""
        self.login("staff")
        response = self.client.post(
            "/api/core/users/",
            {"username": "hacker", "password": "hacker-pass-123", "role": Role.SUPERADMIN},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="hacker").exists())

    def test_普通成员不能修改他人密码(self):
        """老系统 user_detail/<id>/ PUT 不校验归属，任何学生可重置教师密码。

        这是最严重的一条：账号接管。这里固化为回归测试。
        """
        self.login("staff")
        response = self.client.patch(
            f"/api/core/users/{self.superadmin.id}/",
            {"password": "hijacked-pass-999"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.superadmin.refresh_from_db()
        # 超管密码必须未被改动
        self.assertTrue(self.superadmin.check_password(PASSWORD))
        self.assertFalse(self.superadmin.check_password("hijacked-pass-999"))

    def test_普通成员不能删除他人(self):
        self.login("staff")
        response = self.client.delete(f"/api/core/users/{self.superadmin.id}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(id=self.superadmin.id).exists())

    def test_普通成员不能管理外链入口(self):
        self.login("staff")
        response = self.client.post(
            "/api/core/links/",
            {"title": "恶意入口", "url": "https://evil.example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_普通成员不能查看审计日志(self):
        self.login("staff")
        response = self.client.get("/api/core/audit-logs/")
        self.assertEqual(response.status_code, 403)

    def test_普通成员不能进入后台管理(self):
        self.login("staff")
        response = self.client.get("/admin/")
        # 未登录后台 → 重定向到登录页
        self.assertIn(response.status_code, (301, 302))


class PrivilegeEscalationTests(PortalTestCase):
    """提权路径必须全部堵死。"""

    def test_非超管创建用户时不能指定角色(self):
        self.login("root")
        # 先给 staff 授予用户管理权限，模拟"有管理权但非超管"的场景
        from apps.core.models import ModulePermission

        perm = ModulePermission.objects.get(code=PermCode.PORTAL_USER_MANAGE)
        self.staff.extra_perms.add(perm)
        self.client.credentials()

        self.login("staff")
        response = self.client.post(
            "/api/core/users/",
            {"username": "sneaky", "password": "sneaky-pass-123", "role": Role.SUPERADMIN},
            format="json",
        )
        # 指定角色会被拒；即便换用默认角色创建，也绝不能变成超管
        if response.status_code == 201:
            created = User.objects.get(username="sneaky")
            self.assertNotEqual(created.role, Role.SUPERADMIN)
            self.assertFalse(created.is_superuser)

    def test_超管创建的用户默认不是管理员(self):
        self.login("root")
        response = self.client.post(
            "/api/core/users/",
            {"username": "normal", "password": "normal-pass-123"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        created = User.objects.get(username="normal")
        self.assertEqual(created.role, Role.STAFF)
        self.assertFalse(created.is_superuser)
        self.assertFalse(created.is_staff)

    def test_接口不接受客户端传入的is_superuser(self):
        """即便请求体里塞了 is_superuser，也必须被忽略。"""
        self.login("root")
        response = self.client.post(
            "/api/core/users/",
            {
                "username": "fakeadmin",
                "password": "fakeadmin-pass-123",
                "is_superuser": True,
                "is_staff": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        created = User.objects.get(username="fakeadmin")
        self.assertFalse(created.is_superuser)
        self.assertFalse(created.is_staff)

    def test_不能删除自己(self):
        self.login("root")
        response = self.client.delete(f"/api/core/users/{self.superadmin.id}/")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(User.objects.filter(username="root").exists())


# ══════════════════════════════════════════════════ 外链入口


class ExternalLinkTests(PortalTestCase):
    def test_外链入口默认不对外公开(self):
        response = self.client.get("/api/core/links/")
        self.assertEqual(response.status_code, 401)

    def test_成员能看到启用且有权访问的入口(self):
        ExternalLink.objects.create(
            title="可用入口",
            url="https://ok.example.com",
            is_active=True,
            required_perm=PermCode.PORTAL_LINKS_VIEW,
        )
        self.login("staff")
        response = self.client.get("/api/core/links/")
        self.assertEqual(response.status_code, 200)
        titles = [row["title"] for row in response.data["results"]]
        self.assertIn("可用入口", titles)

    def test_停用的入口对普通成员不可见(self):
        ExternalLink.objects.create(
            title="已停用入口",
            url="https://disabled.example.com",
            is_active=False,
            required_perm=PermCode.PORTAL_LINKS_VIEW,
        )
        self.login("staff")
        response = self.client.get("/api/core/links/")
        titles = [row["title"] for row in response.data["results"]]
        self.assertNotIn("已停用入口", titles)

    def test_无权访问的入口被过滤(self):
        ExternalLink.objects.create(
            title="仅管理员可见",
            url="https://admin-only.example.com",
            is_active=True,
            required_perm=PermCode.PORTAL_LINKS_MANAGE,
        )
        self.login("staff")
        response = self.client.get("/api/core/links/")
        titles = [row["title"] for row in response.data["results"]]
        self.assertNotIn("仅管理员可见", titles)

    def test_管理员可以新增入口(self):
        self.login("root")
        response = self.client.post(
            "/api/core/links/",
            {"title": "新入口", "url": "https://new.example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(ExternalLink.objects.filter(title="新入口").exists())

    def test_拒绝非法的外链地址(self):
        self.login("root")
        response = self.client.post(
            "/api/core/links/",
            {"title": "坏地址", "url": "javascript:alert(1)"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


# ══════════════════════════════════════════════════ 审计日志


class AuditLogTests(PortalTestCase):
    def test_登录会被记录(self):
        from apps.core.models import AuditLog

        self.login("root")
        self.assertTrue(
            AuditLog.objects.filter(action="login", username="root").exists()
        )

    def test_写操作会被记录(self):
        from apps.core.models import AuditLog

        self.login("root")
        self.client.post(
            "/api/core/links/",
            {"title": "留痕测试", "url": "https://trace.example.com"},
            format="json",
        )
        self.assertTrue(
            AuditLog.objects.filter(action="create", username="root").exists()
        )
