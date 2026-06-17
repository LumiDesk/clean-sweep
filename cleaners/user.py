"""用户数据清理：常见家目录子目录 + 回收站

命令规格抽成 `_*_cmds()`，按当前实际存在的目录动态生成。删的是用户数据而非
缓存，`steps()` 里标为 USER_DATA：TUI 里带 ⚠、默认不勾选。
"""

import os
import re
import shlex

from .spec import Category, Step

HOME = os.path.expanduser("~")
USER_DIR_NAMES = ["Documents", "Downloads", "Music", "Pictures", "Videos"]
UID = os.getuid()


def user_dirs_existing() -> list[str]:
    return [
        os.path.join(HOME, name)
        for name in USER_DIR_NAMES
        if os.path.isdir(os.path.join(HOME, name))
    ]


def _user_dirs_cmds() -> list[str]:
    # -mindepth 1 保证不会删掉文件夹本身
    return [
        f"find {shlex.quote(path)} -mindepth 1 -delete"
        for path in user_dirs_existing()
    ]


def _xdg_data_home() -> str:
    return os.environ.get("XDG_DATA_HOME") or os.path.join(HOME, ".local/share")


def _mountpoints() -> list[str]:
    """从 /proc/mounts 取所有挂载点（解转义 \\040 之类的八进制）。"""
    try:
        with open("/proc/mounts", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return []
    points = []
    for line in lines:
        fields = line.split()
        if len(fields) >= 2:
            points.append(re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), fields[1]))
    return points


def trash_existing() -> list[str]:
    """所有真实存在的回收站目录：XDG 主回收站 + 各挂载盘 + 老版兼容路径。

    遵循 freedesktop Trash spec：外部盘用 `<挂载点>/.Trash-<uid>` 或
    `<挂载点>/.Trash/<uid>`；只检测当前真实存在的，避免误建/误删。
    """
    candidates = [
        os.path.join(_xdg_data_home(), "Trash"),
        os.path.join(HOME, ".trash"),  # 老 KDE 兼容
        os.path.join(HOME, ".Trash"),
    ]
    for mp in _mountpoints():
        candidates.append(os.path.join(mp, f".Trash-{UID}"))
        candidates.append(os.path.join(mp, ".Trash", str(UID)))

    seen: set[str] = set()
    out: list[str] = []
    for path in candidates:
        if path not in seen and os.path.isdir(path):
            seen.add(path)
            out.append(path)
    return out


def _trash_cmds() -> list[str]:
    # 清空每个回收站目录的内容（保留目录本身，DE 会按需重建 files/info）
    return [
        f"find {shlex.quote(path)} -mindepth 1 -delete"
        for path in trash_existing()
    ]


def steps() -> list[Step]:
    existing = user_dirs_existing()
    trashes = trash_existing()
    return [
        Step(
            "user_dirs", "用户目录", Category.USER_DATA, _user_dirs_cmds(),
            available=bool(existing), reason="无可清理目录",
            note="清空 " + "、".join(USER_DIR_NAMES) + " 的内容（保留文件夹）",
        ),
        Step(
            "trash", "回收站", Category.USER_DATA, _trash_cmds(),
            available=bool(trashes), reason="未找到任何回收站",
            note=f"清空 {len(trashes)} 处回收站（含外部盘）"
            if trashes
            else "清空回收站",
        ),
    ]
