"""清理项的描述模型。

每个 cleaner 模块用 `steps()` 暴露一组 `Step`，TUI 据此渲染勾选列表与预览，
入口据此执行被选中项的命令。`Step.cmds` 是最终要执行的命令（需要提权的已带
`sudo` 前缀），同时直接用作预览内容。
"""

from dataclasses import dataclass, field
from enum import Enum


class Category(Enum):
    """删除对象的性质，决定默认是否勾选与危险标记。"""

    CACHE = "缓存"
    USER_DATA = "用户数据"
    SYSTEM = "系统"
    CONFIG = "应用配置"
    CUSTOM = "自定义"


# 缓存以外的都属于“删了有代价”的，TUI 里加 ⚠ 标记、默认不勾选。
DESTRUCTIVE = frozenset(
    {Category.USER_DATA, Category.SYSTEM, Category.CONFIG, Category.CUSTOM}
)


@dataclass
class Step:
    key: str  # 稳定标识，TUI 选择与执行都用它
    name: str  # 列表里显示的名字
    category: Category
    cmds: list[str] = field(default_factory=list)  # 最终命令（含 sudo），也是预览内容
    available: bool = True  # 工具/路径是否存在；为假则列表中置灰、不可选
    reason: str = ""  # 不可用时的原因（置灰显示）
    note: str = ""  # 一行简介
    needs_sudo: bool = False
    # 针对某个具体应用的清理项（Claude、思源……），在 TUI 的「应用插件」区单独
    # 展示，与通用清理项分开。与 category（安全分级）正交：插件也分缓存/配置等。
    plugin: bool = False

    @property
    def destructive(self) -> bool:
        return self.category in DESTRUCTIVE
