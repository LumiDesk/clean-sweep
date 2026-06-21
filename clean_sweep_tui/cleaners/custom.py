"""自定义清理：用户在 ~/.config/clean-sweep-tui/custom.json 中列出要删除的目录/文件"""

import json
import os
import shlex

from ._common import is_dangerous_path
from .spec import Category, Step

HOME = os.path.expanduser("~")

# 用户配置目录下的 custom.json（遵循 XDG，安装后仍可写）。
_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME") or os.path.join(HOME, ".config")
CONFIG_PATH = os.path.join(_CONFIG_HOME, "clean-sweep-tui", "custom.json")


def _load_paths() -> list[str] | None:
    """读取并展开 custom.json 里的 paths；读不到或格式不对返回 None。"""
    if not os.path.isfile(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    raw_paths = data.get("paths") if isinstance(data, dict) else None
    if not isinstance(raw_paths, list):
        return None
    return [os.path.expanduser(p) for p in raw_paths if isinstance(p, str) and p]


def custom_existing() -> list[str]:
    """custom.json 中当前真实存在、且非危险的路径列表。"""
    expanded = _load_paths()
    if not expanded:
        return []
    return [p for p in expanded if os.path.exists(p) and not is_dangerous_path(p)]


def _custom_cmds() -> list[str]:
    return [f"rm -rf {shlex.quote(p)}" for p in custom_existing()]


def _reason() -> str:
    """不可用时给出原因（供 TUI 置灰显示）。"""
    if not os.path.isfile(CONFIG_PATH):
        return "未找到 custom.json"
    if _load_paths() is None:
        return "custom.json 读取失败或格式不正确"
    return "无可删除的路径（未配置 / 不存在 / 危险路径已挡）"


def steps() -> list[Step]:
    # custom_existing() 已排除根目录/家目录等危险路径与不存在的路径，
    # cmds 即预览，所见即所删（包括路径本身）。
    existing = custom_existing()
    return [
        Step(
            "custom", "自定义清理", Category.CUSTOM, _custom_cmds(),
            available=bool(existing), reason=_reason(),
            note=f"删除 custom.json 中 {len(existing)} 个路径（含其本身）"
            if existing
            else "读 custom.json 的 paths 列表",
        ),
    ]
