"""开发工具缓存清理：docker / pnpm / npm / bun / go / rust / sdkman

每个清理项的命令规格抽成 `_*_cmds()`；命令一律不带 `sudo`（开发缓存都不需要
提权）。`steps()` 把这些命令包装成 `Step` 供 TUI 与入口使用。
"""

import os

from ._common import has
from .spec import Category, Step

_SDKMAN_INIT = os.path.expanduser("~/.sdkman/bin/sdkman-init.sh")


def _docker_cmds() -> list[str]:
    return [
        # 停止并删除所有容器
        "docker ps -aq | xargs -r docker stop",
        "docker ps -aq | xargs -r docker rm -f",
        # 删除所有镜像
        "docker images -aq | xargs -r docker rmi -f",
        # 删除所有 volume
        "docker volume ls -q | xargs -r docker volume rm -f",
        # 一次性清理系统中残余的镜像、容器、网络、构建缓存、volume
        "docker system prune -a --volumes -f",
        # system prune 只清当前 builder；buildx 独立 builder 的构建缓存要单独清
        "docker buildx prune -a -f",
    ]


def _pnpm_cmds() -> list[str]:
    return [
        # 先清理无引用的内容
        "pnpm store prune",
        # 直接删除整个 store 目录
        'rm -rf "$(pnpm store path 2>/dev/null)"',
        # 兜底：常见的默认位置
        "rm -rf ~/.local/share/pnpm/store ~/.pnpm-store",
    ]


def _npm_cmds() -> list[str]:
    return [
        "npm cache clean --force",
        "rm -rf ~/.npm/_cacache",
    ]


def _bun_cmds() -> list[str]:
    return [
        # 清理全局模块缓存
        "bun pm cache rm",
        # 兜底：直接删除默认缓存目录
        "rm -rf ~/.bun/install/cache",
    ]


def _go_cmds() -> list[str]:
    # 一并清理构建、模块、测试、fuzz 缓存
    return ["go clean -cache -modcache -testcache -fuzzcache"]


def _rust_cmds() -> list[str]:
    # 删除 registry 与 git 缓存，保留已安装的 bin
    return [
        "rm -rf ~/.cargo/registry/cache ~/.cargo/registry/src "
        "~/.cargo/git/db ~/.cargo/git/checkouts"
    ]


def _sdkman_cmds() -> list[str]:
    # sdk 是 shell 函数，必须先 source
    return [f"bash -lc 'source {_SDKMAN_INIT} && sdk flush'"]


def steps() -> list[Step]:
    # 全部是缓存：最坏只是下次构建变慢，默认勾选、无危险标记。
    return [
        Step(
            "docker", "Docker", Category.CACHE, _docker_cmds(),
            available=has("docker"), reason="未安装 docker",
            note="容器 / 镜像 / volume / 构建缓存",
        ),
        Step(
            "pnpm", "pnpm", Category.CACHE, _pnpm_cmds(),
            available=has("pnpm"), reason="未安装 pnpm", note="store 缓存",
        ),
        Step(
            "npm", "npm", Category.CACHE, _npm_cmds(),
            available=has("npm"), reason="未安装 npm", note="cache 目录",
        ),
        Step(
            "bun", "Bun", Category.CACHE, _bun_cmds(),
            available=has("bun"), reason="未安装 bun", note="全局模块缓存",
        ),
        Step(
            "go", "Go", Category.CACHE, _go_cmds(),
            available=has("go"), reason="未安装 go",
            note="build / module / test / fuzz 缓存",
        ),
        Step(
            "rust", "Rust", Category.CACHE, _rust_cmds(),
            available=has("cargo"), reason="未安装 cargo",
            note="registry 与 git 缓存（保留 bin）",
        ),
        Step(
            "sdkman", "SDKMAN", Category.CACHE, _sdkman_cmds(),
            available=os.path.exists(_SDKMAN_INIT), reason="未安装 sdkman",
            note="sdk flush",
        ),
    ]
