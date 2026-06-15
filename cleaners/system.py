"""系统级清理：dnf / apt 包缓存 / autoremove、systemd 日志、~/.cache、/var/cache

`_*_cmds()` 给出不带 `sudo` 的命令规格；`clean_*()` 里按需拼上 `sudo`。
需要提权或删系统状态的项另带一层二次确认。
"""

import os
import shlex

from rich.prompt import Confirm

from ._common import console, has, run, skip

CACHE_DIR = os.path.expanduser("~/.cache")

# /var/cache 下每个子目录归属不同应用，全删风险高。
# 只挑公认能自动重建、清完不影响系统启动的几项；dnf 缓存归 clean_dnf 处理。
VAR_CACHE_TARGETS = [
    "/var/cache/man",
    "/var/cache/fontconfig",
    "/var/cache/PackageKit",
    "/var/cache/cups",
]


def _dnf_cmds() -> list[str]:
    return ["dnf autoremove -y", "dnf clean all"]


def _apt_cmds() -> list[str]:
    return ["apt-get autoremove -y", "apt-get clean"]


def _journal_cmds() -> list[str]:
    # 先 rotate 关闭当前活动日志文件，再用极小阈值清空全部归档
    return ["journalctl --rotate", "journalctl --vacuum-time=1s"]


def _user_cache_cmds() -> list[str]:
    return [f"find {shlex.quote(CACHE_DIR)} -mindepth 1 -delete"]


def var_cache_existing() -> list[str]:
    return [p for p in VAR_CACHE_TARGETS if os.path.isdir(p)]


def _var_cache_cmds() -> list[str]:
    return [
        f"find {shlex.quote(path)} -mindepth 1 -delete"
        for path in var_cache_existing()
    ]


def clean_dnf() -> None:
    if not has("dnf"):
        skip("dnf")
        return
    # 涉及 sudo 且 autoremove 会卸载未被依赖的包，二次确认
    if not Confirm.ask(
        "将执行 sudo dnf autoremove / clean all（会卸载孤立包并清除包缓存），确认继续？",
        default=False,
    ):
        console.print("[yellow]已跳过 dnf 清理[/yellow]")
        return
    for cmd in _dnf_cmds():
        run(f"sudo {cmd}")


def clean_apt() -> None:
    if not has("apt-get"):
        skip("apt")
        return
    # 涉及 sudo 且 autoremove 会卸载未被依赖的包，二次确认
    if not Confirm.ask(
        "将执行 sudo apt-get autoremove / clean（会卸载孤立包并清除包缓存），确认继续？",
        default=False,
    ):
        console.print("[yellow]已跳过 apt 清理[/yellow]")
        return
    for cmd in _apt_cmds():
        run(f"sudo {cmd}")


def clean_journal() -> None:
    if not has("journalctl"):
        skip("journalctl")
        return
    # 删除的是系统日志，影响后续问题排查，二次确认
    if not Confirm.ask(
        "将清空全部 systemd 日志（不保留任何历史），确认继续？",
        default=False,
    ):
        console.print("[yellow]已跳过 journal 清理[/yellow]")
        return
    for cmd in _journal_cmds():
        run(f"sudo {cmd}")


def clean_user_cache() -> None:
    if not os.path.isdir(CACHE_DIR):
        skip("~/.cache")
        return
    # XDG 用户缓存（浏览器 / IDE / 缩略图等），删完应用会按需重建。
    # 性质上是缓存，跟 dev.py 同等级，不加二次确认。
    for cmd in _user_cache_cmds():
        run(cmd)


def clean_var_cache() -> None:
    existing = var_cache_existing()
    if not existing:
        console.print("[yellow]未发现 /var/cache 下可清理项，跳过[/yellow]")
        return
    # 涉及 sudo，二次确认
    if not Confirm.ask(
        f"将清空 {', '.join(existing)} 下的内容（sudo），确认继续？",
        default=False,
    ):
        console.print("[yellow]已跳过 /var/cache 清理[/yellow]")
        return
    for cmd in _var_cache_cmds():
        run(f"sudo {cmd}")
