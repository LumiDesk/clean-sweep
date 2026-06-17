"""日志文件清理：删除家目录下所有 .log 文件

删的是日志文件（用户数据），函数内单独二次确认。
范围固定为 $HOME，命令静态，不需要 `*_existing()`。
"""

import os
import shlex

from .spec import Category, Step

HOME = os.path.expanduser("~")


def _log_cmds() -> list[str]:
    # 递归删除家目录下所有 .log 常规文件，但跳过 node_modules / .git
    # （避免误删项目源码与依赖里的日志）。find 默认不跟随符号链接。
    # 不用 -delete：它会启用 -depth，使 -prune 失效；改用 prune + xargs rm。
    home = shlex.quote(HOME)
    return [
        f"find {home} -type d \\( -name node_modules -o -name .git \\) -prune "
        f"-o -type f -name '*.log' -print0 | xargs -0 -r rm -f --"
    ]


def steps() -> list[Step]:
    # 范围固定为 $HOME（总是存在），删的是日志文件（用户数据）。
    return [
        Step(
            "logs", "日志文件", Category.USER_DATA, _log_cmds(),
            note=f"递归删 {HOME} 下所有 .log（跳过 node_modules / .git）",
        ),
    ]
