import sys

from rich.panel import Panel
from rich.prompt import Confirm

from cleaners._common import console
from cleaners.apps import clean_claude
from cleaners.custom import clean_custom
from cleaners.dev import (
    clean_bun,
    clean_docker,
    clean_go,
    clean_npm,
    clean_pnpm,
    clean_rust,
    clean_sdkman,
)
from cleaners.system import (
    clean_apt,
    clean_dnf,
    clean_journal,
    clean_user_cache,
    clean_var_cache,
)
from cleaners.user import clean_trash, clean_user_dirs

# 输出大标题
console.print(
    Panel(
        r"""  ____ _                  ____
 / ___| | ___  __ _ _ __ / ___|_      _____  ___ _ __
| |   | |/ _ \/ _` | '_ \\___ \ \ /\ / / _ \/ _ \ '_ \
| |___| |  __/ (_| | | | |___) \ V  V /  __/  __/ |_) |
 \____|_|\___|\__,_|_| |_|____/ \_/\_/ \___|\___| .__/
                                                |_|
""",
        title="CleanSweep",
        subtitle="0.1.0",
    )
)

if not Confirm.ask("确认要删除所有的开发缓存吗？此操作无法撤销？", default=True):
    sys.exit(0)

# 清理步骤按顺序执行；序号由位置自动生成，新增/调整顺序只动这张表。
# 涉及用户数据 / 系统状态的步骤各自在函数内部再做二次确认。
STEPS = [
    ("Docker", clean_docker),
    ("pnpm", clean_pnpm),
    ("npm", clean_npm),
    ("Bun", clean_bun),
    ("Go", clean_go),
    ("Rust", clean_rust),
    ("SDKMAN", clean_sdkman),
    ("~/.cache", clean_user_cache),
    ("用户目录", clean_user_dirs),
    ("回收站", clean_trash),
    ("Claude", clean_claude),
    ("dnf", clean_dnf),
    ("apt", clean_apt),
    ("/var/cache", clean_var_cache),
    ("systemd journal", clean_journal),
    ("自定义清理", clean_custom),
]

for index, (name, clean) in enumerate(STEPS, start=1):
    console.rule(f"Step {index:02d}: {name}")
    clean()

console.rule("[green]全部完成[/green]")
