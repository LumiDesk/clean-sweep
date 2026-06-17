# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`CleanSweep` 是一个一键清空各类开发缓存（以及部分用户目录、应用配置）的命令行工具，仅面向 Linux。Python 3.14，uv 管理依赖。第三方库：`rich`（执行阶段的终端输出）+ `textual`（勾选清理项的 TUI）。

唯一入口 `main.py`：拉起 TUI 让用户一次性勾选要清理的项，TUI 退出后回到普通终端按顺序执行被选中项。它在模块顶层直接执行，不要加 `if __name__ == "__main__"`。

## Commands

- 运行：`uv run main.py`
- 同步依赖：`uv sync`
- 新增依赖：`uv add <pkg>`

没有测试套件，没有 linter 配置。VSCode 会跑 Ruff 类型的诊断（PostToolUse 会回传 `ide_diagnostics`），别忽略警告。

## Architecture

```
main.py              # 入口：跑 TUI 拿到选中的 key，退出后按顺序 run() 每条命令
tui.py               # textual TUI：勾选列表 + 实时预览 + 一次性确认弹窗
cleaners/
├── _common.py       # 共享 console / run / has
├── spec.py          # Category 枚举 + Step 数据类（清理项的统一描述模型）
├── registry.py      # 汇总各模块 steps()，按 ORDER 固定顺序返回
├── dev.py           # 开发工具缓存：docker, pnpm, npm, bun, go, rust, sdkman
├── system.py        # 系统级：dnf, apt, systemd journal, ~/.cache, /var/cache
├── user.py          # 用户数据目录：Documents/Downloads/Music/Pictures/Videos + 回收站
├── logs.py          # 家目录下所有 .log 日志文件
├── apps.py          # 应用配置：Claude (.claude 文件夹 + .claude.json)
└── custom.py        # 自定义：读项目根目录 custom.json 的 paths 列表
```

数据流：`registry.all_steps()` 收齐所有 `Step` → `tui.CleanSweepApp` 渲染勾选列表（右侧预览 `Step.cmds`）→ 用户勾选 + 回车 → 一次性确认弹窗 → `app.run()` 返回选中的 key 列表 → `main.py` 对每个选中 `Step` 的 `cmds` 逐条 `run(...)`。

**交互不再是逐项二次确认**：上下/jk 移动，空格勾选，`a` 全选 / `n` 全不选 / `c` 仅缓存，回车执行；确认弹窗是唯一一道闸门（回车确认，esc 取消）。

模块按 **删除对象的性质** 分组（`Step.category`），不是按工具分组。这个 `category` 同时决定 TUI 行为，是项目最重要的安全约定：
- `Category.CACHE`（`dev.py` 全部 + `system.py` 的 `~/.cache`）：只动缓存，最坏是下次构建变慢——**默认勾选**，无危险标记。
- `Category.USER_DATA / SYSTEM / CONFIG / CUSTOM`（即 `spec.DESTRUCTIVE`）：删用户数据、配置、系统状态或需 `sudo`——**默认不勾选**，列表里带 `!` 危险标记，确认弹窗里单独统计。新增同类清理时务必归到正确 category，别错标成 CACHE。

### 命令规格

每个 cleaner 模块里，要执行的 shell 命令抽成模块级的 `_<thing>_cmds() -> list[str]`（**不带 `sudo` 前缀**），与 `steps()` 分开维护。模块的 `steps()` 把命令包装成 `Step`：需要提权的在 `steps()` 里给每条命令拼上 `sudo ` 并设 `needs_sudo=True`，`Step.cmds` 即最终命令、也直接当预览展示（所见即所执行）。

`var_cache` / `user_dirs` / `claude` / `custom` 这类目标随系统状态变化的，命令按当前真实存在的路径动态生成，对应模块导出 `*_existing()` 辅助函数给 `steps()` 用（同时决定 `available`）。

### 共用约定（来自 `_common.py`）

- `run(cmd)`：所有 shell 操作都走它——它会先 `console.print` 出命令本身（青色），再 `subprocess.run(..., check=False)`。**不要绕开它直接调 `subprocess` / `os.system`**，否则用户看不到执行的是什么。执行只在 TUI 退出后的 `main.py` 里发生。
- `has(name)`：检测可执行文件是否存在，用于 `steps()` 里算 `available`。工具/路径不存在的项在 TUI 里置灰、不可勾选，不报错退出；整体必须能跨环境跑通。
- 路径里有用户输入或可能含特殊字符时用 `shlex.quote`（参考 `user.py` / `apps.py`）。`dev.py` 里硬编码的工具命令可以不用。

### 增加一个新的 cleaner

1. 判断它属于哪类（开发缓存 / 系统级 / 用户数据 / 应用配置 / 自定义），写到对应文件里；性质不同就新开一个模块（记得在 `registry.py` import 它）。
2. 把命令抽成模块级 `_<thing>_cmds() -> list[str]`（不带 `sudo`）。目标随系统状态变化的，再导出一个 `*_existing()` 给 `steps()` 用。
3. 在该模块的 `steps()` 里追加一条 `Step(key, name, category, cmds, available=..., reason=..., note=..., needs_sudo=...)`：`category` 决定默认勾选与危险标记，缺工具/路径时 `available=False` 并给 `reason`；需提权则 `cmds` 里每条拼 `sudo ` 且 `needs_sudo=True`。
4. 把新 `key` 加进 `registry.ORDER`，位置就是 TUI 里的显示/执行顺序。
5. 不要再写 `clean_*()`，也不要在函数里 `Confirm.ask` —— 确认统一由 TUI 的弹窗负责。

## 文档同步

每次实现新功能或修改既有功能后，**必须查看 `README.md` 是否需要同步更新**（清理项列表、使用说明、架构描述等）。需要更新就直接改，不要等用户提醒。
