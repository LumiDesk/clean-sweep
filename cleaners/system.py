"""系统级清理：dnf / apt 包缓存 / autoremove、systemd 日志、~/.cache、/var/cache

`_*_cmds()` 给出不带 `sudo` 的命令规格；`steps()` 里给需要提权的项拼上 `sudo`
再包装成 `Step`。除 `~/.cache`（缓存性质）外都标为 SYSTEM，TUI 里默认不勾选。
"""

import os
import shlex

from ._common import has
from .spec import Category, Step

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


def steps() -> list[Step]:
    existing_var = var_cache_existing()
    return [
        # ~/.cache 性质是缓存，跟 dev.py 同级：默认勾选、无危险标记。
        Step(
            "user_cache", "~/.cache", Category.CACHE, _user_cache_cmds(),
            available=os.path.isdir(CACHE_DIR), reason="目录不存在",
            note="XDG 用户缓存（浏览器 / IDE / 缩略图等）",
        ),
        Step(
            "dnf", "dnf", Category.SYSTEM,
            [f"sudo {c}" for c in _dnf_cmds()],
            available=has("dnf"), reason="非 Fedora/RHEL 系", needs_sudo=True,
            note="autoremove 孤立包 + clean all",
        ),
        Step(
            "apt", "apt", Category.SYSTEM,
            [f"sudo {c}" for c in _apt_cmds()],
            available=has("apt-get"), reason="非 Debian/Ubuntu 系", needs_sudo=True,
            note="autoremove 孤立包 + clean",
        ),
        Step(
            "var_cache", "/var/cache", Category.SYSTEM,
            [f"sudo {c}" for c in _var_cache_cmds()],
            available=bool(existing_var), reason="无可清理子目录", needs_sudo=True,
            note=", ".join(existing_var) if existing_var else "man/fontconfig/...",
        ),
        Step(
            "journal", "systemd journal", Category.SYSTEM,
            [f"sudo {c}" for c in _journal_cmds()],
            available=has("journalctl"), reason="无 journalctl", needs_sudo=True,
            note="清空全部日志，不保留历史",
        ),
    ]
