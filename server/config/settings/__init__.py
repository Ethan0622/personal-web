"""配置包入口。

默认加载 dev，生产环境通过 DJANGO_SETTINGS_MODULE 指定 prod。
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
