"""开发工具缓存清理：docker / pnpm / npm / go / rust / sdkman

每个清理项的命令规格抽成 `_*_cmds()`，由对应的 `clean_*()` 调用；命令一律
不带 `sudo`（开发缓存都不需要提权）。
"""

import os

from ._common import has, run, skip

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


def clean_docker() -> None:
    if not has("docker"):
        skip("docker")
        return
    for cmd in _docker_cmds():
        run(cmd)


def clean_pnpm() -> None:
    if not has("pnpm"):
        skip("pnpm")
        return
    for cmd in _pnpm_cmds():
        run(cmd)


def clean_npm() -> None:
    if not has("npm"):
        skip("npm")
        return
    for cmd in _npm_cmds():
        run(cmd)


def clean_bun() -> None:
    if not has("bun"):
        skip("bun")
        return
    for cmd in _bun_cmds():
        run(cmd)


def clean_go() -> None:
    if not has("go"):
        skip("go")
        return
    for cmd in _go_cmds():
        run(cmd)


def clean_rust() -> None:
    if not has("cargo"):
        skip("cargo")
        return
    for cmd in _rust_cmds():
        run(cmd)


def clean_sdkman() -> None:
    if not os.path.exists(_SDKMAN_INIT):
        skip("sdkman")
        return
    for cmd in _sdkman_cmds():
        run(cmd)
