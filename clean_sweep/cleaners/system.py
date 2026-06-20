"""系统级清理：dnf / apt 包缓存 / autoremove、systemd 日志、~/.cache、/var/cache、
缩略图、崩溃报告 / coredump、snap 旧版本、flatpak 未用 runtime

`_*_cmds()` 给出不带 `sudo` 的命令规格；`steps()` 里给需要提权的项拼上 `sudo`
再包装成 `Step`。`~/.cache` / 缩略图是缓存性质（默认勾选），其余标为 SYSTEM。
"""

import os
import shlex

from ._common import has
from .spec import Category, Step

HOME = os.path.expanduser("~")
CACHE_DIR = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")

# /var/cache 下每个子目录归属不同应用，全删风险高。
# 只挑公认能自动重建、清完不影响系统启动的几项；dnf 缓存归 clean_dnf 处理。
VAR_CACHE_TARGETS = [
    "/var/cache/man",
    "/var/cache/fontconfig",
    "/var/cache/PackageKit",
    "/var/cache/cups",
]

# 缩略图缓存：老版 ~/.thumbnails 在 ~/.cache 之外，单独覆盖。
THUMBNAIL_DIRS = [
    os.path.join(HOME, ".thumbnails"),
    os.path.join(CACHE_DIR, "thumbnails"),
]

# 崩溃报告 / core dump：apport 与 systemd-coredump 的落点。
CRASH_DIRS = [
    "/var/crash",
    "/var/lib/systemd/coredump",
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


def thumbnails_existing() -> list[str]:
    return [p for p in THUMBNAIL_DIRS if os.path.isdir(p)]


def _thumbnails_cmds() -> list[str]:
    return [
        f"find {shlex.quote(path)} -mindepth 1 -delete"
        for path in thumbnails_existing()
    ]


def crash_existing() -> list[str]:
    return [p for p in CRASH_DIRS if os.path.isdir(p)]


def _crash_cmds() -> list[str]:
    return [
        f"find {shlex.quote(path)} -mindepth 1 -delete"
        for path in crash_existing()
    ]


def _snap_cmds() -> list[str]:
    # 删除所有 disabled（旧版本）的 snap revision，保留当前版本；
    # 管道里 snap list 不需提权，只有 snap remove 需要，故 sudo 内嵌。
    return [
        "snap list --all | awk '/disabled/{print $1, $3}' | "
        'while read -r name rev; do sudo snap remove "$name" --revision="$rev"; done'
    ]


def _flatpak_cmds() -> list[str]:
    # 先清用户级未用 runtime，再清系统级（后者需 sudo）
    return [
        "flatpak uninstall --unused -y",
        "sudo flatpak uninstall --unused -y",
    ]


def steps() -> list[Step]:
    existing_var = var_cache_existing()
    existing_thumb = thumbnails_existing()
    existing_crash = crash_existing()
    return [
        # ~/.cache 性质是缓存，跟 dev.py 同级：默认勾选、无危险标记。
        Step(
            "user_cache", "~/.cache", Category.CACHE, _user_cache_cmds(),
            available=os.path.isdir(CACHE_DIR), reason="目录不存在",
            note="XDG 用户缓存（浏览器 / IDE / 缩略图等）",
        ),
        Step(
            "thumbnails", "缩略图", Category.CACHE, _thumbnails_cmds(),
            available=bool(existing_thumb), reason="无缩略图缓存",
            note="~/.thumbnails + ~/.cache/thumbnails",
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
        Step(
            "crash", "崩溃报告", Category.SYSTEM,
            [f"sudo {c}" for c in _crash_cmds()],
            available=bool(existing_crash), reason="无崩溃报告 / coredump",
            needs_sudo=True,
            note=", ".join(existing_crash) if existing_crash else "/var/crash, coredump",
        ),
        Step(
            "snap", "snap 旧版本", Category.SYSTEM, _snap_cmds(),
            available=has("snap"), reason="未安装 snap", needs_sudo=True,
            note="删除 disabled 的旧 revision，保留当前版本",
        ),
        Step(
            "flatpak", "flatpak 未用 runtime", Category.SYSTEM, _flatpak_cmds(),
            available=has("flatpak"), reason="未安装 flatpak", needs_sudo=True,
            note="uninstall --unused（用户级 + 系统级）",
        ),
    ]
