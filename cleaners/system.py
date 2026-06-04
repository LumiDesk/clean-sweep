"""系统级清理：dnf / apt 包缓存 / autoremove、systemd 日志、~/.cache、/var/cache"""

import os
import shlex

from rich.prompt import Confirm

from ._common import console, has, run, skip


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
    run("sudo dnf autoremove -y")
    run("sudo dnf clean all")


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
    run("sudo apt-get autoremove -y")
    run("sudo apt-get clean")


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
    # 先 rotate 关闭当前活动日志文件，再用极小阈值清空全部归档
    run("sudo journalctl --rotate")
    run("sudo journalctl --vacuum-time=1s")


def clean_user_cache() -> None:
    cache_dir = os.path.expanduser("~/.cache")
    if not os.path.isdir(cache_dir):
        skip("~/.cache")
        return
    # XDG 用户缓存（浏览器 / IDE / 缩略图等），删完应用会按需重建。
    # 性质上是缓存，跟 dev.py 同等级，不加二次确认。
    run(f"find {shlex.quote(cache_dir)} -mindepth 1 -delete")


def clean_var_cache() -> None:
    # /var/cache 下每个子目录归属不同应用，全删风险高。
    # 只挑公认能自动重建、清完不影响系统启动的几项；
    # dnf 缓存归 clean_dnf 处理，这里不重复。
    targets = [
        "/var/cache/man",
        "/var/cache/fontconfig",
        "/var/cache/PackageKit",
        "/var/cache/cups",
    ]
    existing = [p for p in targets if os.path.isdir(p)]
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
    for path in existing:
        run(f"sudo find {shlex.quote(path)} -mindepth 1 -delete")
