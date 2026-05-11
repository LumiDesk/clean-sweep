# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`cleansh` 是一个一键清空各类开发缓存（以及部分用户目录、应用配置）的命令行工具。Python 3.14，uv 管理依赖，唯一第三方库是 `rich`。

## Commands

- 运行：`uv run main.py`（唯一入口，不要为子模块加 `if __name__ == "__main__"`）
- 同步依赖：`uv sync`
- 新增依赖：`uv add <pkg>`

没有测试套件，没有 linter 配置。VSCode 会跑 Ruff 类型的诊断（PostToolUse 会回传 `ide_diagnostics`），别忽略警告。

## Architecture

```
main.py              # 入口：banner + 顶层 Confirm + 按 Step 顺序调用每个 cleaner
cleaners/
├── _common.py       # 共享 console / run / has / skip
├── dev.py           # 开发工具缓存：docker, pnpm, npm, go, rust, sdkman
├── user.py          # 用户数据目录：Desktop/Documents/Downloads/Music/Pictures/Videos
└── apps.py          # 应用配置：Claude (.claude 文件夹 + .claude.json)
```

模块按 **删除对象的性质** 分组，不是按工具分组：
- `dev.py` 里的清理只动缓存，最坏后果是下次构建变慢——共用顶层 Confirm 即可。
- `user.py` / `apps.py` 删的是用户数据/配置，**每个函数内部必须再加一层 `Confirm.ask(default=False)`**，并且只在用户确认后才执行 `run(...)`。这是这个项目最重要的安全约定，新增同类清理时要遵守。

### 共用约定（来自 `_common.py`）

- `run(cmd)`：所有 shell 操作都走它——它会先 `console.print` 出命令本身（青色），再 `subprocess.run(..., check=False)`。**不要绕开它直接调 `subprocess` / `os.system`**，否则用户看不到执行的是什么。
- `has(name)` + `skip(tool)`：检测可执行文件是否存在；不存在就 `skip(...)` 然后 `return`，不要报错退出。整体流程必须能跨环境跑通（缺哪个工具就跳哪步）。
- 路径里有用户输入或可能含特殊字符时用 `shlex.quote`（参考 `user.py` / `apps.py`）。`dev.py` 里硬编码的工具命令可以不用。

### 增加一个新的 cleaner

1. 判断它属于哪类（开发缓存 / 用户数据 / 应用配置），写到对应文件里；性质不同就新开一个模块。
2. 命名 `clean_<thing>()`，无参数无返回值。
3. 入口先用 `has(...)` 或 `os.path.exists(...)` 探测，缺失就提示并 return。
4. 若涉及用户数据/配置，函数内必须 `Confirm.ask(..., default=False)`，拒绝时打印跳过提示并 return。
5. 在 `main.py` 里 import 并加一条 `console.rule("Step NN: <name>")` + 调用，顺序追加在末尾。

## 文档同步

每次实现新功能或修改既有功能后，**必须查看 `README.md` 是否需要同步更新**（清理项列表、使用说明、架构描述等）。需要更新就直接改，不要等用户提醒。
