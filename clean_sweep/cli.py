"""CleanSweep 入口：拉起 TUI 拿到选中项，退出后逐条执行。

`main()` 是控制台脚本入口（pyproject 的 [project.scripts]）。仓库根目录的
`main.py` 只是调用它的薄壳，`uv run main.py` 与安装后的 `clean-sweep` 等价。
"""

from .cleaners._common import console, run
from .cleaners.registry import all_steps
from .tui import CleanSweepApp


def main() -> None:
    # 1) 拉起 TUI 让用户勾选；返回选中的 step key 列表（取消/退出则为 None）。
    steps = all_steps()
    selected_keys = CleanSweepApp(steps).run()

    # 2) TUI 退出后回到普通终端，按顺序执行被选中项（sudo 密码提示也在这里）。
    if not selected_keys:
        console.print("[yellow]已取消，未执行任何清理。[/yellow]")
        return
    chosen = [s for s in steps if s.key in selected_keys]
    for step in chosen:
        console.rule(step.name)
        for cmd in step.cmds:
            run(cmd)
    console.rule("[green]全部完成[/green]")
