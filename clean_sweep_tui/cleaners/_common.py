import os
import shutil
import subprocess

from rich.console import Console

console = Console()


def run(cmd: str) -> None:
    """通过 shell 执行命令，输出直接打印到终端。"""
    console.print(f"[cyan]$ {cmd}[/cyan]")
    try:
        subprocess.run(cmd, shell=True, check=False)
    except Exception as e:
        console.print(f"[red]执行失败: {e}[/red]")


def has(name: str) -> bool:
    return shutil.which(name) is not None


def is_dangerous_path(path: str) -> bool:
    """挡掉会造成灾难性删除的路径：根目录、家目录本身。

    custom.py / presets.py 这类「删用户给的路径」的清理项共用，避免一条
    配置就把整个家目录 rm 掉。传入路径应已 expanduser。
    """
    norm = os.path.normpath(os.path.abspath(path))
    return norm == os.sep or norm == os.path.normpath(os.path.expanduser("~"))
