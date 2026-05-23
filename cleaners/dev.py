"""开发工具缓存清理：docker / pnpm / npm / go / rust / sdkman"""

import os

from ._common import has, run, skip


def clean_docker() -> None:
    if not has("docker"):
        skip("docker")
        return
    # 停止并删除所有容器
    run("docker ps -aq | xargs -r docker stop")
    run("docker ps -aq | xargs -r docker rm -f")
    # 删除所有镜像
    run("docker images -aq | xargs -r docker rmi -f")
    # 删除所有 volume
    run("docker volume ls -q | xargs -r docker volume rm -f")
    # 一次性清理系统中残余的镜像、容器、网络、构建缓存、volume
    run("docker system prune -a --volumes -f")


def clean_pnpm() -> None:
    if not has("pnpm"):
        skip("pnpm")
        return
    # 先清理无引用的内容
    run("pnpm store prune")
    # 直接删除整个 store 目录
    run("rm -rf \"$(pnpm store path 2>/dev/null)\"")
    # 兜底：常见的默认位置
    run("rm -rf ~/.local/share/pnpm/store ~/.pnpm-store")


def clean_npm() -> None:
    if not has("npm"):
        skip("npm")
        return
    run("npm cache clean --force")
    run("rm -rf ~/.npm/_cacache")


def clean_go() -> None:
    if not has("go"):
        skip("go")
        return
    # 一并清理构建、模块、测试、fuzz 缓存
    run("go clean -cache -modcache -testcache -fuzzcache")


def clean_rust() -> None:
    if not has("cargo"):
        skip("cargo")
        return
    # 删除 registry 与 git 缓存，保留已安装的 bin
    run("rm -rf ~/.cargo/registry/cache ~/.cargo/registry/src ~/.cargo/git/db ~/.cargo/git/checkouts")


def clean_sdkman() -> None:
    init = os.path.expanduser("~/.sdkman/bin/sdkman-init.sh")
    if not os.path.exists(init):
        skip("sdkman")
        return
    # sdk 是 shell 函数，必须先 source
    run(f"bash -lc 'source {init} && sdk flush'")
