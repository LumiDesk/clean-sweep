"""应用配置清理：当前包含 Claude (~/.claude, ~/.claude.json)"""

import os
import shlex

from rich.prompt import Confirm

from ._common import console, run


def clean_claude() -> None:
    home = os.path.expanduser("~")
    targets = [
        os.path.join(home, ".claude"),
        os.path.join(home, ".claude.json"),
    ]
    existing = [p for p in targets if os.path.exists(p)]
    if not existing:
        console.print("[yellow]未找到 Claude 相关文件，跳过[/yellow]")
        return
    # Claude 的配置 / 历史 / 项目记录都在 .claude 里，单独二次确认
    if not Confirm.ask(
        f"将删除：{', '.join(existing)}，确认继续？",
        default=False,
    ):
        console.print("[yellow]已跳过 Claude 清理[/yellow]")
        return
    for path in existing:
        run(f"rm -rf {shlex.quote(path)}")
