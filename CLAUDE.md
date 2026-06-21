# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`CleanSweep TUI` 是一个一键清空各类开发缓存（以及部分用户目录、应用配置）的命令行工具，仅面向 Linux。Python ≥3.10（开发用 3.14），uv 管理依赖。第三方库：`rich`（执行阶段的终端输出）+ `textual`（勾选清理项的 TUI）。

代码在 `clean_sweep_tui/` 包内。入口是 `clean_sweep_tui/cli.py` 的 `main()`：拉起 TUI 让用户一次性勾选要清理的项，TUI 退出后回到普通终端按顺序执行被选中项。`main()` 也是 pyproject `[project.scripts]` 注册的 `clean-sweep-tui` 命令入口；仓库根目录的 `main.py` 只是 `from clean_sweep_tui.cli import main; main()` 的薄壳，让 `uv run main.py` 仍等价于装好后的 `clean-sweep-tui`。PyPI 分发名也是 `clean-sweep-tui`。

## Commands

- 运行：`uv run main.py`（或装好后 `clean-sweep-tui`）
- 同步依赖：`uv sync`
- 新增依赖：`uv add <pkg>`
- 发版（一条命令）：`scripts/publish.sh [patch|minor|major|X.Y.Z]`（默认 patch）——自动升版本号（同步 `pyproject.toml` 与 `clean_sweep_tui/__init__.py`）、构建、上传 PyPI、打 tag 并 push。token 从仓库根目录 `.env` 的 `UV_PUBLISH_TOKEN` 读（见 `.env.example`，`.env` 已 gitignore）。
- 手动构建：`uv build`（生成 `dist/*.whl` 与 `*.tar.gz`）；手动上传 `uv publish`

没有测试套件，没有 linter 配置。VSCode 会跑 Ruff 类型的诊断（PostToolUse 会回传 `ide_diagnostics`），别忽略警告。

## Architecture

```
main.py                    # 根目录薄壳：import clean_sweep_tui.cli.main 并调用
clean_sweep_tui/
├── cli.py                 # 入口 main()：跑 TUI 拿到选中的 key，退出后按顺序 run() 每条命令
├── tui.py                 # textual TUI：勾选列表（通用 / 应用插件两区）+ 实时预览 + 一次性确认弹窗
├── presets/               # 内置应用插件规则库（随包分发的 *.json，加文件=加功能）
│   ├── claude.json        #   Claude（~/.claude + ~/.claude.json，config 类）
│   └── siyuan.json        #   思源笔记（~/SiYuan + ~/.config/siyuan + SiYuan-Electron，config 类）
└── cleaners/
    ├── _common.py         # 共享 console / run / has / is_dangerous_path
    ├── spec.py            # Category 枚举 + Step 数据类（含 plugin 标记）
    ├── registry.py        # 汇总各模块 steps()，按 ORDER 固定顺序返回；presets 插在 custom 前
    ├── dev.py             # 开发工具缓存：docker, pnpm, npm, bun, go, rust, sdkman, gradle, maven
    ├── system.py          # 系统级：dnf, apt, journal, ~/.cache, /var/cache, 缩略图, 崩溃报告, snap, flatpak
    ├── user.py            # 用户数据目录：Documents/.../Videos + 回收站（含外部盘 .Trash-<uid>）
    ├── logs.py            # 家目录下所有 .log 日志文件
    ├── presets.py         # 应用插件：扫描内置 presets/*.json + 用户 ~/.config/.../presets/*.json
    └── custom.py          # 自定义：读 ~/.config/clean-sweep-tui/custom.json 的 paths 列表
```

数据流：`registry.all_steps()` 收齐所有 `Step` → `tui.CleanSweepApp` 渲染勾选列表（`plugin=True` 的进「应用插件」区，其余进「清理项」区；右侧预览 `Step.cmds`）→ 用户勾选 + 回车 → 一次性确认弹窗 → `app.run()` 返回选中的 key 列表 → `cli.main()` 对每个选中 `Step` 的 `cmds` 逐条 `run(...)`。

### 应用插件（presets）

数据驱动的「插件」层：**针对某个具体软件**（Claude、思源笔记……）的清理规则写成一个 JSON 文件，扫描成 `Step`，在 TUI 的「应用插件」区单独展示（与通用清理项分区，靠 `Step.plugin=True` 区分）。和 `custom.py` 互补——custom 是用户临时列路径，presets 是预先写好、随包分发的规则库。**加一个软件（含 Claude 这种）= 加一个 JSON，不改代码。**

- 扫描两个目录，同 key 用户覆盖内置：内置 `clean_sweep_tui/presets/*.json`（随包分发）、用户 `~/.config/clean-sweep-tui/presets/*.json`（支持 `XDG_CONFIG_HOME`）。
- JSON schema（**仅路径模型**，同 custom）：`key`（必填，稳定标识）、`name`（必填）、`paths`（必填，rm -rf 的路径，支持 `~`）、`category`（可选，默认 `cache`；取值 `cache/user_data/system/config/custom`，缺省/非法都按 `cache`）、`note`（可选）。
- 路径会 `expanduser` + 排除危险路径（根 / 家目录，复用 `_common.is_dangerous_path`），只对**当前真实存在**的路径生成命令；全不存在/被挡掉则整项置灰。`Step.key` 加 `preset:` 前缀避免与内置 key 冲突，故不进 `registry.ORDER`，统一在 `custom` 之前插入。
- `category` 决定该插件的默认勾选与危险标记，沿用全局约定：`cache` 默认勾选无标记，`config`（如 Claude、思源——删配置/默认工作区）等 destructive 类默认不勾、带 `!`。插件无 sudo（纯用户态路径删除），填 destructive 类只影响标记不会拼 sudo。
- 加一个应用清理：在 `clean_sweep_tui/presets/` 放一个新 `*.json` 即可（hatchling 默认把包内 json 纳入分发，已验证进 wheel）。删之前务必确认 `paths` 删的是缓存/可重建数据，而非用户内容。

包内模块一律用相对导入（`from .cleaners.registry import ...`、`from .spec import ...`）。

**交互不再是逐项二次确认**：上下/jk 移动，空格勾选，`a` 全选 / `n` 全不选 / `c` 仅缓存，回车执行；确认弹窗是唯一一道闸门（回车确认，esc 取消）。

模块按 **删除对象的性质** 分组（`Step.category`），不是按工具分组。这个 `category` 同时决定 TUI 行为，是项目最重要的安全约定：
- `Category.CACHE`（`dev.py` 全部 + `system.py` 的 `~/.cache`）：只动缓存，最坏是下次构建变慢——**默认勾选**，无危险标记。
- `Category.USER_DATA / SYSTEM / CONFIG / CUSTOM`（即 `spec.DESTRUCTIVE`）：删用户数据、配置、系统状态或需 `sudo`——**默认不勾选**，列表里带 `!` 危险标记，确认弹窗里单独统计。新增同类清理时务必归到正确 category，别错标成 CACHE。

### 命令规格

每个 cleaner 模块里，要执行的 shell 命令抽成模块级的 `_<thing>_cmds() -> list[str]`（**不带 `sudo` 前缀**），与 `steps()` 分开维护。模块的 `steps()` 把命令包装成 `Step`：需要提权的在 `steps()` 里给每条命令拼上 `sudo ` 并设 `needs_sudo=True`，`Step.cmds` 即最终命令、也直接当预览展示（所见即所执行）。

`var_cache` / `user_dirs` / `custom` 这类目标随系统状态变化的，命令按当前真实存在的路径动态生成，对应模块导出 `*_existing()` 辅助函数给 `steps()` 用（同时决定 `available`）。应用插件（presets）的路径同理按实际存在生成。

### 共用约定（来自 `_common.py`）

- `run(cmd)`：所有 shell 操作都走它——它会先 `console.print` 出命令本身（青色），再 `subprocess.run(..., check=False)`。**不要绕开它直接调 `subprocess` / `os.system`**，否则用户看不到执行的是什么。执行只在 TUI 退出后的 `cli.main()` 里发生。
- `has(name)`：检测可执行文件是否存在，用于 `steps()` 里算 `available`。工具/路径不存在的项在 TUI 里置灰、不可勾选，不报错退出；整体必须能跨环境跑通。
- 路径里有用户输入或可能含特殊字符时用 `shlex.quote`（参考 `user.py` / `custom.py` / `presets.py`）。`dev.py` 里硬编码的工具命令可以不用。

### 增加一个新的 cleaner

> 针对**某个具体应用**、且纯靠删路径就能搞定的，别写模块——直接在 `clean_sweep_tui/presets/` 加一个 JSON（见上「应用插件」），零代码。下面这套是给通用清理项 / 需要代码逻辑的项用的。

1. 判断它属于哪类（开发缓存 / 系统级 / 用户数据 / 自定义），写到对应文件里；性质不同就新开一个模块（记得在 `registry.py` import 它）。
2. 把命令抽成模块级 `_<thing>_cmds() -> list[str]`（不带 `sudo`）。目标随系统状态变化的，再导出一个 `*_existing()` 给 `steps()` 用。
3. 在该模块的 `steps()` 里追加一条 `Step(key, name, category, cmds, available=..., reason=..., note=..., needs_sudo=...)`：`category` 决定默认勾选与危险标记，缺工具/路径时 `available=False` 并给 `reason`；需提权则 `cmds` 里每条拼 `sudo ` 且 `needs_sudo=True`。
4. 把新 `key` 加进 `registry.ORDER`，位置就是 TUI 里的显示/执行顺序。
5. 不要再写 `clean_*()`，也不要在函数里 `Confirm.ask` —— 确认统一由 TUI 的弹窗负责。

## 文档同步

每次实现新功能或修改既有功能后，**必须查看 `README.md` 是否需要同步更新**（清理项列表、使用说明、架构描述等）。需要更新就直接改，不要等用户提醒。
