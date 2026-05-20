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


def clean_custom() -> None:
    if not os.path.isfile(CONFIG_PATH):
        console.print(f"[yellow]未找到自定义配置 {CONFIG_PATH}，跳过[/yellow]")
        console.print(
            '[dim]提示：创建该文件，内容形如 {"paths": ["/some/dir", "~/another"]}[/dim]'
        )
        return

    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        console.print(f"[red]读取 {CONFIG_PATH} 失败：{e}[/red]")
        return

    raw_paths = data.get("paths") if isinstance(data, dict) else None
    if not isinstance(raw_paths, list) or not raw_paths:
        console.print(f"[yellow]{CONFIG_PATH} 中未配置 paths，跳过[/yellow]")
        return

    expanded = [os.path.expanduser(p) for p in raw_paths if isinstance(p, str) and p]
    existing = [p for p in expanded if os.path.exists(p)]
    missing = [p for p in expanded if not os.path.exists(p)]

    for p in missing:
        console.print(f"[yellow]未找到 {p}，跳过[/yellow]")

    if not existing:
        console.print("[yellow]自定义列表中没有任何存在的路径，跳过[/yellow]")
        return

    console.print("将删除以下自定义路径（包括其本身）：")
    for p in existing:
        console.print(f"  [red]- {p}[/red]")

    # 用户自定义的删除清单，二次确认
    if not Confirm.ask("确认全部删除？", default=False):
        console.print("[yellow]已跳过自定义清理[/yellow]")
        return

    for p in existing:
        run(f"rm -rf {shlex.quote(p)}")
