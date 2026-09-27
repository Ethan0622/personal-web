"""初始化数据：权限目录 + 示例外链入口。

这一步对应老项目缺失的"数据迁移脚本"教训 ——
考试模块的题型(1~5)与知识点(1~8)是硬编码依赖的，但没有迁移脚本，
导致重建数据库后必须先手工录入才能用。这里从一开始就用数据迁移解决。

注意：迁移中的权限码刻意内联写死，不 import 业务代码 ——
这样即使将来 perms.py 的内容变化，历史迁移的结果依然可复现。
"""

from django.db import migrations

PERMISSION_CATALOG = [
    ("portal.view", "访问门户", "门户外壳", 10),
    ("portal.user.view", "查看用户列表", "门户外壳", 20),
    ("portal.user.manage", "管理用户（增删改）", "门户外壳", 30),
    ("portal.links.view", "查看外链入口", "门户外壳", 40),
    ("portal.links.manage", "管理外链入口", "门户外壳", 50),
    ("portal.audit.view", "查看审计日志", "门户外壳", 60),
    ("exam.view", "考试：进入考试平台", "考试模块", 110),
    ("exam.answer", "考试：参加考试", "考试模块", 120),
    ("exam.itembank.view", "考试：查看题库", "考试模块", 130),
    ("exam.itembank.manage", "考试：管理题库", "考试模块", 140),
    ("exam.class.view", "考试：查看班级", "考试模块", 150),
    ("exam.class.manage", "考试：管理班级", "考试模块", 160),
    ("exam.grade", "考试：阅卷与评分", "考试模块", 170),
]

# 示例外链：默认停用，仅用于展示"口子"的形状。
# 启用或新增请在 Django 后台 → 外链入口 里操作，无需改代码。
EXAMPLE_LINKS = [
    {
        "title": "学校 OA 系统",
        "url": "https://example.com/oa",
        "icon": "business",
        "description": "示例：替换为学校实际 OA 地址后启用",
        "category": "常用入口",
        "order": 10,
        "is_active": False,
        "required_perm": "portal.links.view",
    },
    {
        "title": "企业微信",
        "url": "https://work.weixin.qq.com",
        "icon": "chat",
        "description": "示例：校内沟通与审批",
        "category": "常用入口",
        "order": 20,
        "is_active": False,
        "required_perm": "portal.links.view",
    },
    {
        "title": "阿里云控制台",
        "url": "https://home.console.aliyun.com",
        "icon": "cloud",
        "description": "示例：服务器与资源管理",
        "category": "运维工具",
        "order": 30,
        "is_active": False,
        "required_perm": "portal.links.view",
    },
]


def seed(apps, schema_editor):
    ModulePermission = apps.get_model("core", "ModulePermission")
    ExternalLink = apps.get_model("core", "ExternalLink")

    for code, name, module, order in PERMISSION_CATALOG:
        ModulePermission.objects.update_or_create(
            code=code,
            defaults={"name": name, "module": module, "order": order},
        )

    for payload in EXAMPLE_LINKS:
        ExternalLink.objects.get_or_create(
            title=payload["title"],
            defaults=payload,
        )


def unseed(apps, schema_editor):
    ModulePermission = apps.get_model("core", "ModulePermission")
    ExternalLink = apps.get_model("core", "ExternalLink")

    ModulePermission.objects.filter(
        code__in=[row[0] for row in PERMISSION_CATALOG]
    ).delete()
    ExternalLink.objects.filter(
        title__in=[row["title"] for row in EXAMPLE_LINKS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
