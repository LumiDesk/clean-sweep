"""用户数据清理：常见家目录子目录 + 回收站

命令规格抽成 `_*_cmds()`，按当前实际存在的目录动态生成。
删的是用户数据而非缓存，每步在函数内单独二次确认。
"""

import os
import shlex

from rich.prompt import Confirm

from ._common import console, run

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


def clean_user_dirs() -> None:
    targets = USER_DIR_NAMES
    # 这一步删除的是用户数据而非缓存，单独二次确认
    if not Confirm.ask(
        f"将清空 {HOME} 下的 {', '.join(targets)} 内容（保留文件夹本身），确认继续？",
        default=False,
    ):
        console.print("[yellow]已跳过用户目录清理[/yellow]")
        return
    for cmd in _user_dirs_cmds():
        run(cmd)


def clean_trash() -> None:
    if not os.path.isdir(TRASH_DIR):
        console.print("[yellow]未找到回收站，跳过[/yellow]")
        return
    # 回收站内容属于用户数据（即使已经准备删除），二次确认
    if not Confirm.ask(
        f"将清空 {TRASH_DIR} 下的内容（files / info 等子目录会保留），确认继续？",
        default=False,
    ):
        console.print("[yellow]已跳过回收站清理[/yellow]")
        return
    for cmd in _trash_cmds():
        run(cmd)
