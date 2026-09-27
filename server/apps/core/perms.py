"""权限码目录。

设计原则：**默认拒绝**。任何接口必须显式声明所需权限码，
未声明且未标记 allow_any 的视图在系统检查阶段就会给出警告。

新增模块时，在这里追加该模块的权限码，然后在数据迁移中登记。
"""


class PermCode:
    """权限码常量。命名约定：<模块>.<资源>.<动作>"""

    # 门户外壳
    PORTAL_VIEW = "portal.view"
    PORTAL_USER_VIEW = "portal.user.view"
    PORTAL_USER_MANAGE = "portal.user.manage"
    PORTAL_LINKS_VIEW = "portal.links.view"
    PORTAL_LINKS_MANAGE = "portal.links.manage"
    PORTAL_AUDIT_VIEW = "portal.audit.view"

    # 考试模块（迁移 apps/exam 时启用）
    EXAM_VIEW = "exam.view"
    EXAM_ANSWER = "exam.answer"
    EXAM_ITEMBANK_VIEW = "exam.itembank.view"
    EXAM_ITEMBANK_MANAGE = "exam.itembank.manage"
    EXAM_CLASS_VIEW = "exam.class.view"
    EXAM_CLASS_MANAGE = "exam.class.manage"
    EXAM_GRADE = "exam.grade"


class Role:
    """角色。与 core.models.User.role 的 choices 保持一致。"""

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    STAFF = "staff"
    GUEST = "guest"


ROLE_CHOICES = [
    (Role.SUPERADMIN, "超级管理员"),
    (Role.ADMIN, "管理员"),
    (Role.STAFF, "普通成员"),
    (Role.GUEST, "访客"),
]

# 通配符：拥有该权限码即代表拥有一切权限
WILDCARD = "*"

# 角色默认权限 —— 角色只是"默认值"，可以在后台为用户追加额外权限
ROLE_DEFAULT_PERMS: dict[str, set[str]] = {
    Role.SUPERADMIN: {WILDCARD},
    Role.ADMIN: {
        PermCode.PORTAL_VIEW,
        PermCode.PORTAL_USER_VIEW,
        PermCode.PORTAL_LINKS_VIEW,
        PermCode.PORTAL_LINKS_MANAGE,
        PermCode.PORTAL_AUDIT_VIEW,
    },
    Role.STAFF: {
        PermCode.PORTAL_VIEW,
        PermCode.PORTAL_LINKS_VIEW,
    },
    Role.GUEST: {
        PermCode.PORTAL_VIEW,
    },
}

# 权限目录：(权限码, 显示名, 所属模块, 排序)
# 数据迁移会以此为准同步数据库中的 core.ModulePermission 记录
PERMISSION_CATALOG = [
    (PermCode.PORTAL_VIEW, "访问门户", "门户外壳", 10),
    (PermCode.PORTAL_USER_VIEW, "查看用户列表", "门户外壳", 20),
    (PermCode.PORTAL_USER_MANAGE, "管理用户（增删改）", "门户外壳", 30),
    (PermCode.PORTAL_LINKS_VIEW, "查看外链入口", "门户外壳", 40),
    (PermCode.PORTAL_LINKS_MANAGE, "管理外链入口", "门户外壳", 50),
    (PermCode.PORTAL_AUDIT_VIEW, "查看审计日志", "门户外壳", 60),
    (PermCode.EXAM_VIEW, "考试：进入考试平台", "考试模块", 110),
    (PermCode.EXAM_ANSWER, "考试：参加考试", "考试模块", 120),
    (PermCode.EXAM_ITEMBANK_VIEW, "考试：查看题库", "考试模块", 130),
    (PermCode.EXAM_ITEMBANK_MANAGE, "考试：管理题库", "考试模块", 140),
    (PermCode.EXAM_CLASS_VIEW, "考试：查看班级", "考试模块", 150),
    (PermCode.EXAM_CLASS_MANAGE, "考试：管理班级", "考试模块", 160),
    (PermCode.EXAM_GRADE, "考试：阅卷与评分", "考试模块", 170),
]
