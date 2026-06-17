"""日志文件清理：删除家目录下所有 .log 文件

删的是日志文件（用户数据），函数内单独二次确认。
范围固定为 $HOME，命令静态，不需要 `*_existing()`。
"""

import os
import shlex

from .spec import Category, Step

HOME = os.path.expanduser("~")


def _log_cmds() -> list[str]:
    # 递归删除家目录下所有 .log 常规文件；find 默认不跟随符号链接
    return [f"find {shlex.quote(HOME)} -type f -name '*.log' -delete"]


def steps() -> list[Step]:
    # 范围固定为 $HOME（总是存在），删的是日志文件（用户数据）。
    return [
        Step(
            "logs", "日志文件", Category.USER_DATA, _log_cmds(),
            note=f"递归删除 {HOME} 下所有 .log 文件",
        ),
    ]
