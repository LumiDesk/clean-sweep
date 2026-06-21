"""汇总所有 cleaner 模块的 `steps()`，按固定顺序返回。

新增清理项：在对应模块的 `steps()` 里加一条，再把它的 `key` 写进 ORDER。
应用插件（presets.py，含 Claude 等针对具体应用的清理）是数据驱动的、key 在运行时
才确定，不进 ORDER——统一在固定的「自定义」之前插入（见 all_steps）。
"""

from . import custom, dev, logs, presets, system, user
from .spec import Step

# 显示与执行顺序。开发缓存 → 用户缓存 → 用户数据 → 系统 →（应用插件）→ 自定义。
ORDER = [
    "docker", "pnpm", "npm", "bun", "go", "rust", "sdkman", "gradle", "maven",
    "user_cache", "thumbnails",
    "user_dirs", "trash", "logs",
    "dnf", "apt", "var_cache", "journal", "crash", "snap", "flatpak",
    "custom",
]


def all_steps() -> list[Step]:
    collected = [
        *dev.steps(),
        *system.steps(),
        *user.steps(),
        *logs.steps(),
        *custom.steps(),
    ]
    by_key = {s.key: s for s in collected}
    ordered = [by_key[key] for key in ORDER]
    # 应用插件插在「自定义」之前（两者都是数据驱动、属收尾的可选项）。
    insert_at = ORDER.index("custom")
    return ordered[:insert_at] + presets.steps() + ordered[insert_at:]
