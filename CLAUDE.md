# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`CleanSweep` 是一个一键清空各类开发缓存（以及部分用户目录、应用配置）的命令行工具，仅面向 Linux。Python 3.14，uv 管理依赖。第三方库只有 `rich`（终端输出）。

唯一入口 `main.py`：命令行界面，终端里逐步二次确认。它在模块顶层直接执行，不要加 `if __name__ == "__main__"`。

## Commands

- 运行：`uv run main.py`
- 同步依赖：`uv sync`
- 新增依赖：`uv add <pkg>`

没有测试套件，没有 linter 配置。VSCode 会跑 Ruff 类型的诊断（PostToolUse 会回传 `ide_diagnostics`），别忽略警告。

## Architecture

```
main.py              # 入口：banner + 顶层 Confirm + 按 STEPS 表顺序调用每个 cleaner
cleaners/
├── _common.py       # 共享 console / run / has / skip
├── dev.py           # 开发工具缓存：docker, pnpm, npm, bun, go, rust, sdkman
├── system.py        # 系统级：dnf, apt, systemd journal, ~/.cache, /var/cache
├── user.py          # 用户数据目录：Documents/Downloads/Music/Pictures/Videos + 回收站
├── apps.py          # 应用配置：Claude (.claude 文件夹 + .claude.json)
└── custom.py        # 自定义：读项目根目录 custom.json 的 paths 列表
```

`main.py` 用一张 `STEPS = [(名称, clean_函数), ...]` 表驱动：Step 序号按表中位置自动生成，新增/调整顺序只改这张表，不要再手写 `Step NN`。

模块按 **删除对象的性质** 分组，不是按工具分组：
- `dev.py` 里的清理只动缓存，最坏后果是下次构建变慢——共用顶层 Confirm 即可。`system.py` 里的 `clean_user_cache`（`~/.cache`）性质上也是缓存，同样不加二次确认。
- `user.py` / `apps.py` / `custom.py`，以及 `system.py` 里涉及 `sudo` / 卸载包 / 删日志的清理，删的是用户数据、配置或系统状态，**每个函数内部必须再加一层 `Confirm.ask(default=False)`**，并且只在用户确认后才执行 `run(...)`。这是这个项目最重要的安全约定，新增同类清理时要遵守。

### 命令规格

每个 cleaner 模块里，要执行的 shell 命令抽成模块级的 `_<thing>_cmds() -> list[str]`（**不带 `sudo` 前缀**），与执行/确认流程分开维护。`clean_*()` 负责终端的检测/跳过提示 + 二次确认，确认后对每条命令 `run(...)`（需提权的自己拼 `sudo `）。

`var_cache` / `user_dirs` / `claude` / `custom` 这类目标随系统状态变化的，命令按当前真实存在的路径动态生成，对应模块导出 `*_existing()` 辅助函数给检测/动态生成用。

### 共用约定（来自 `_common.py`）

- `run(cmd)`：所有 shell 操作都走它——它会先 `console.print` 出命令本身（青色），再 `subprocess.run(..., check=False)`。**不要绕开它直接调 `subprocess` / `os.system`**，否则用户看不到执行的是什么。
- `has(name)` + `skip(tool)`：检测可执行文件是否存在；不存在就 `skip(...)` 然后 `return`，不要报错退出。整体流程必须能跨环境跑通（缺哪个工具就跳哪步）。
- 路径里有用户输入或可能含特殊字符时用 `shlex.quote`（参考 `user.py` / `apps.py`）。`dev.py` 里硬编码的工具命令可以不用。

### 增加一个新的 cleaner

1. 判断它属于哪类（开发缓存 / 系统级 / 用户数据 / 应用配置 / 自定义），写到对应文件里；性质不同就新开一个模块。
2. 把命令抽成模块级 `_<thing>_cmds() -> list[str]`（不带 `sudo`）。目标随系统状态变化的，再导出一个 `*_existing()` 给检测/动态生成用。
3. 命名 `clean_<thing>()`，无参数无返回值；入口先用 `has(...)` 或 `os.path.exists(...)` 探测，缺失就提示并 return。
4. 若涉及用户数据 / 配置 / 系统状态（`sudo`、卸载包、删日志等），函数内必须 `Confirm.ask(..., default=False)`，拒绝时打印跳过提示并 return；提权命令自己拼 `sudo `。
5. 在 `main.py` 里 import，并在 `STEPS` 表里追加一条 `("<name>", clean_<thing>)`，顺序就是表里的位置。

## 文档同步

每次实现新功能或修改既有功能后，**必须查看 `README.md` 是否需要同步更新**（清理项列表、使用说明、架构描述等）。需要更新就直接改，不要等用户提醒。
