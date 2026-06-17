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
