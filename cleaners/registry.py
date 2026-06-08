"""清理任务注册表：把每个 Step 的「检测 + 命令规格」声明为数据，供 GUI 消费。

CLI（main.py）走各模块自己的 `clean_*()`，保留终端二次确认；GUI 则读这里的
`TASKS`：用 `detect()` 决定能否勾选，用 `plan()` 取要执行的命令（不带提权前缀），
`privileged` 决定执行层是否用 `pkexec`。命令字符串本身只在各 cleaner 模块里维护一份。
"""

import os
from collections.abc import Callable
from dataclasses import dataclass, field

from . import apps, custom, dev, system, user
from ._common import has


@dataclass(frozen=True)
class Task:
    key: str  # 稳定标识，如 "docker"
    label: str  # GUI 显示名
    category: str  # 分类标题：dev / system / user / apps / custom
    detect: Callable[[], bool]  # 当前系统是否存在可清理对象
    plan: Callable[[], list[str]]  # 要执行的命令（不含 sudo/pkexec）
    privileged: bool = False  # 是否需要提权（GUI 用 pkexec）
    sensitive: bool = False  # 是否删用户数据/配置/系统状态（GUI 勾选时高亮）
    detail: str = ""  # 说明：会删掉什么
    note: Callable[[], str] = field(default=lambda: "")  # 动态补充说明（如具体路径）


# 分类的中文标题（GUI 分组用）
CATEGORY_TITLES = {
    "dev": "开发工具缓存",
    "system": "系统级",
    "user": "用户数据",
    "apps": "应用配置",
    "custom": "自定义",
}


def _claude_note() -> str:
    existing = apps.claude_existing()
    return "、".join(existing) if existing else ""


def _var_cache_note() -> str:
    existing = system.var_cache_existing()
    return "、".join(existing) if existing else ""


def _user_dirs_note() -> str:
    existing = user.user_dirs_existing()
    return "、".join(existing) if existing else ""


def _custom_note() -> str:
    existing = custom.custom_existing()
    return "、".join(existing) if existing else ""


TASKS: list[Task] = [
    # —— 开发工具缓存（缓存，删了最多下次构建变慢）——
    Task("docker", "Docker", "dev", lambda: has("docker"), dev._docker_cmds,
         detail="容器 / 镜像 / volume / 构建缓存"),
    Task("pnpm", "pnpm", "dev", lambda: has("pnpm"), dev._pnpm_cmds,
         detail="pnpm store"),
    Task("npm", "npm", "dev", lambda: has("npm"), dev._npm_cmds,
         detail="npm cache"),
    Task("bun", "Bun", "dev", lambda: has("bun"), dev._bun_cmds,
         detail="bun 全局模块缓存（~/.bun/install/cache）"),
    Task("go", "Go", "dev", lambda: has("go"), dev._go_cmds,
         detail="build / module / test / fuzz 缓存"),
    Task("rust", "Rust", "dev", lambda: has("cargo"), dev._rust_cmds,
         detail="registry 与 git 缓存（保留 ~/.cargo/bin）"),
    Task("sdkman", "SDKMAN", "dev",
         lambda: os.path.exists(dev._SDKMAN_INIT),
         dev._sdkman_cmds, detail="sdk flush"),
    # —— 系统级 ——
    Task("user_cache", "~/.cache", "system",
         lambda: os.path.isdir(system.CACHE_DIR),
         system._user_cache_cmds,
         detail="XDG 用户缓存（浏览器 / IDE / 缩略图等）"),
    Task("dnf", "dnf", "system", lambda: has("dnf"), system._dnf_cmds,
         privileged=True, sensitive=True,
         detail="autoremove 卸载孤立包 + clean all 清包缓存（需 sudo）"),
    Task("apt", "apt", "system", lambda: has("apt-get"), system._apt_cmds,
         privileged=True, sensitive=True,
         detail="autoremove 卸载孤立包 + clean 清包缓存（需 sudo）"),
    Task("var_cache", "/var/cache", "system",
         lambda: bool(system.var_cache_existing()), system._var_cache_cmds,
         privileged=True, sensitive=True,
         detail="man / fontconfig / PackageKit / cups 缓存（需 sudo）",
         note=_var_cache_note),
    Task("journal", "systemd journal", "system",
         lambda: has("journalctl"), system._journal_cmds,
         privileged=True, sensitive=True,
         detail="清空全部 systemd 日志，不保留历史（需 sudo）"),
    # —— 用户数据 ——
    Task("user_dirs", "家目录常见文件夹", "user",
         lambda: bool(user.user_dirs_existing()), user._user_dirs_cmds,
         sensitive=True,
         detail="清空 Documents/Downloads/Music/Pictures/Videos 内容（保留文件夹）",
         note=_user_dirs_note),
    Task("trash", "回收站", "user",
         lambda: os.path.isdir(user.TRASH_DIR), user._trash_cmds,
         sensitive=True, detail="清空 ~/.local/share/Trash"),
    # —— 应用配置 ——
    Task("claude", "Claude", "apps",
         lambda: bool(apps.claude_existing()), apps._claude_cmds,
         sensitive=True, detail="删除 ~/.claude 文件夹和 ~/.claude.json",
         note=_claude_note),
    # —— 自定义 ——
    Task("custom", "自定义路径", "custom",
         lambda: bool(custom.custom_existing()), custom._custom_cmds,
         sensitive=True, detail="删除 custom.json 中列出的路径（含路径本身）",
         note=_custom_note),
]
