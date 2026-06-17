"""用户数据清理：常见家目录子目录 + 回收站

命令规格抽成 `_*_cmds()`，按当前实际存在的目录动态生成。删的是用户数据而非
缓存，`steps()` 里标为 USER_DATA：TUI 里带 ⚠、默认不勾选。
"""

import os
import shlex

from .spec import Category, Step

HOME = os.path.expanduser("~")
USER_DIR_NAMES = ["Documents", "Downloads", "Music", "Pictures", "Videos"]
TRASH_DIR = os.path.join(HOME, ".local/share/Trash")


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


def _trash_cmds() -> list[str]:
    return [f"find {shlex.quote(TRASH_DIR)} -mindepth 2 -delete"]


def steps() -> list[Step]:
    existing = user_dirs_existing()
    return [
        Step(
            "user_dirs", "用户目录", Category.USER_DATA, _user_dirs_cmds(),
            available=bool(existing), reason="无可清理目录",
            note="清空 " + "、".join(USER_DIR_NAMES) + " 的内容（保留文件夹）",
        ),
        Step(
            "trash", "回收站", Category.USER_DATA, _trash_cmds(),
            available=os.path.isdir(TRASH_DIR), reason="未找到回收站",
            note="清空 ~/.local/share/Trash",
        ),
    ]
