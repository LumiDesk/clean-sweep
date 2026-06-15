"""自定义清理：用户在项目根目录的 custom.json 中列出要删除的目录/文件"""

import json
import os
import shlex

from rich.prompt import Confirm

from ._common import console, run

# 项目根目录下的 custom.json（与 main.py 同级）
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "custom.json",
)

HOME = os.path.expanduser("~")


def _is_dangerous(path: str) -> bool:
    """挡掉会造成灾难性删除的路径：根目录、家目录本身。"""
    norm = os.path.normpath(os.path.abspath(path))
    return norm == os.sep or norm == os.path.normpath(HOME)


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
    return [p for p in expanded if os.path.exists(p) and not _is_dangerous(p)]


def _custom_cmds() -> list[str]:
    return [f"rm -rf {shlex.quote(p)}" for p in custom_existing()]


def clean_custom() -> None:
    if not os.path.isfile(CONFIG_PATH):
        console.print(f"[yellow]未找到自定义配置 {CONFIG_PATH}，跳过[/yellow]")
        console.print(
            '[dim]提示：创建该文件，内容形如 {"paths": ["/some/dir", "~/another"]}[/dim]'
        )
        return

    expanded = _load_paths()
    if expanded is None:
        console.print(f"[red]读取 {CONFIG_PATH} 失败或格式不正确[/red]")
        return
    if not expanded:
        console.print(f"[yellow]{CONFIG_PATH} 中未配置 paths，跳过[/yellow]")
        return

    dangerous = [p for p in expanded if _is_dangerous(p)]
    missing = [p for p in expanded if not _is_dangerous(p) and not os.path.exists(p)]
    existing = [p for p in expanded if not _is_dangerous(p) and os.path.exists(p)]

    for p in dangerous:
        console.print(f"[red]拒绝删除危险路径 {p}（根目录或家目录本身），跳过[/red]")
    for p in missing:
        console.print(f"[yellow]未找到 {p}，跳过[/yellow]")

    if not existing:
        console.print("[yellow]自定义列表中没有任何可删除的路径，跳过[/yellow]")
        return

    console.print("将删除以下自定义路径（包括其本身）：")
    for p in existing:
        console.print(f"  [red]- {p}[/red]")

    # 用户自定义的删除清单，二次确认
    if not Confirm.ask("确认全部删除？", default=False):
        console.print("[yellow]已跳过自定义清理[/yellow]")
        return

    for cmd in _custom_cmds():
        run(cmd)
