"""应用配置清理：当前包含 Claude (~/.claude, ~/.claude.json)"""

import os
import shlex

from .spec import Category, Step

HOME = os.path.expanduser("~")
CLAUDE_TARGETS = [
    os.path.join(HOME, ".claude"),
    os.path.join(HOME, ".claude.json"),
]


def claude_existing() -> list[str]:
    return [p for p in CLAUDE_TARGETS if os.path.exists(p)]


def _claude_cmds() -> list[str]:
    return [f"rm -rf {shlex.quote(path)}" for path in claude_existing()]


def steps() -> list[Step]:
    existing = claude_existing()
    return [
        Step(
            "claude", "Claude", Category.CONFIG, _claude_cmds(),
            available=bool(existing), reason="未找到 Claude 相关文件",
            note="删除 ~/.claude 与 ~/.claude.json（配置/历史/项目记录）",
        ),
    ]
