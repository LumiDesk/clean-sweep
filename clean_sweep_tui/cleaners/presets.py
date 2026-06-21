"""应用插件清理：扫描内置 + 用户预设目录里的 JSON 规则，每个 JSON 生成一个 Step。

定位：custom.py 是「用户临时列几条路径」，presets 是「预先写好、随包分发的规则库」
——针对具体软件（Claude、思源笔记、JetBrains……）总结好「删哪些文件夹」，用户在
TUI 的「应用插件」区勾选即可。加一个软件 = 加一个 JSON 文件，不用改代码。

这些项都标 `plugin=True`，TUI 据此与通用清理项分区展示。

扫描两个目录（同名 key 用户覆盖内置）：
- 内置：随包分发的 ``clean_sweep_tui/presets/*.json``
- 用户：``~/.config/clean-sweep-tui/presets/*.json``（支持 XDG_CONFIG_HOME）

每个 JSON 的 schema（只支持「删路径」模型，与 custom.py 一致）::

    {
      "key": "siyuan",            // 必填，稳定标识；同 key 用户预设覆盖内置
      "name": "思源笔记缓存",       // 必填，列表显示名
      "category": "cache",         // 可选，默认 cache；决定默认勾选与危险标记
      "note": "一行简介",           // 可选
      "paths": ["~/SiYuan/temp"]   // 必填，要 rm -rf 的路径（支持 ~ 展开）
    }

``paths`` 会展开 ``~``、排除危险路径（根 / 家目录），只对当前真实存在的路径生成
``rm -rf`` 命令——所见即所删（含路径本身），不存在/全被挡掉则整项置灰。
"""

import json
import os
import shlex
from pathlib import Path

from ._common import is_dangerous_path
from .spec import Category, Step

HOME = os.path.expanduser("~")

# 内置预设目录：本文件在 cleaners/ 下，parents[1] 即包根 clean_sweep_tui/。
_BUNDLED_DIR = Path(__file__).resolve().parents[1] / "presets"

# 用户预设目录（遵循 XDG，安装后仍可增删）。
_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME") or os.path.join(HOME, ".config")
_USER_DIR = Path(_CONFIG_HOME) / "clean-sweep-tui" / "presets"

# category 字符串 → 枚举；缺省 / 非法都按 cache（默认勾选、无危险标记）处理。
_CATEGORY_BY_NAME = {
    "cache": Category.CACHE,
    "user_data": Category.USER_DATA,
    "system": Category.SYSTEM,
    "config": Category.CONFIG,
    "custom": Category.CUSTOM,
}


def _load_file(path: Path) -> dict | None:
    """读取并校验单个预设 JSON；格式不对返回 None。"""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    key = data.get("key")
    name = data.get("name")
    paths = data.get("paths")
    if not (isinstance(key, str) and key and isinstance(name, str) and name):
        return None
    if not isinstance(paths, list):
        return None
    return data


def _collect() -> dict[str, dict]:
    """汇总所有预设，按 key 去重；用户目录覆盖内置目录的同 key 项。"""
    found: dict[str, dict] = {}
    for directory in (_BUNDLED_DIR, _USER_DIR):  # 用户目录在后，覆盖内置
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            data = _load_file(path)
            if data is not None:
                found[data["key"]] = data
    return found


def _existing_paths(raw_paths: list) -> list[str]:
    """展开 ~、排除危险路径，只留下当前真实存在的路径。"""
    out: list[str] = []
    for p in raw_paths:
        if not isinstance(p, str) or not p:
            continue
        expanded = os.path.expanduser(p)
        if os.path.exists(expanded) and not is_dangerous_path(expanded):
            out.append(expanded)
    return out


def steps() -> list[Step]:
    out: list[Step] = []
    for raw_key, data in sorted(_collect().items()):
        name = data["name"]
        category = _CATEGORY_BY_NAME.get(
            str(data.get("category", "cache")).lower(), Category.CACHE
        )
        note = data.get("note")
        existing = _existing_paths(data["paths"])
        cmds = [f"rm -rf {shlex.quote(p)}" for p in existing]
        # key 加 preset: 前缀，避免与内置清理项的 key 冲突。
        out.append(
            Step(
                f"preset:{raw_key}", name, category, cmds,
                available=bool(existing),
                reason="无可删除的路径（未安装 / 不存在 / 危险路径已挡）",
                note=note if isinstance(note, str) and note
                else f"删除 {name} 的缓存路径（含其本身）",
                plugin=True,
            )
        )
    return out
