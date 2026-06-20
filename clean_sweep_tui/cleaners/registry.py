"""汇总所有 cleaner 模块的 `steps()`，按固定顺序返回。

新增清理项：在对应模块的 `steps()` 里加一条，再把它的 `key` 写进 ORDER。
"""

from . import apps, custom, dev, logs, system, user
from .spec import Step

# 显示与执行顺序。开发缓存 → 用户缓存 → 用户数据 → 应用配置 → 系统 → 自定义。
ORDER = [
    "docker", "pnpm", "npm", "bun", "go", "rust", "sdkman", "gradle", "maven",
    "user_cache", "thumbnails",
    "user_dirs", "trash", "logs",
    "claude",
    "dnf", "apt", "var_cache", "journal", "crash", "snap", "flatpak",
    "custom",
]


def all_steps() -> list[Step]:
    collected = [
        *dev.steps(),
        *system.steps(),
        *user.steps(),
        *logs.steps(),
        *apps.steps(),
        *custom.steps(),
    ]
    by_key = {s.key: s for s in collected}
    return [by_key[key] for key in ORDER]
