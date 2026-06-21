# 🧹 CleanSweep TUI

> 一键清空各类开发缓存，以及部分用户目录、应用配置的终端小工具。勾选、预览、确认，三步清空磁盘。

<p>
  <img alt="Platform" src="https://img.shields.io/badge/platform-Linux-informational">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="Package manager" src="https://img.shields.io/badge/deps-uv-purple">
  <img alt="License" src="https://img.shields.io/badge/license-GPLv3-green">
</p>

CleanSweep TUI 把「该删的缓存」整理成一份清单，用 TUI（终端图形界面）让你**勾选 → 预览要执行的命令 → 一次性确认 → 执行**。每一项删什么都清清楚楚，所见即所删，不藏黑盒。

<p align="center">
  <img alt="CleanSweep TUI 运行截图：左侧勾选清单，右侧实时命令预览" src="https://raw.githubusercontent.com/LumiDesk/clean-sweep-tui/main/showcase.png" width="860">
</p>

## ✨ 特性

- **一眼看清要删什么** —— 选中任意一项，右侧实时显示即将执行的原始 shell 命令，没有隐藏动作。
- **安全分级，默认稳妥** —— 缓存类默认勾选（最坏只是下次构建变慢）；会动用户数据 / 配置 / 系统状态的项带 `!` 标记、**默认不勾**，需要你自己选中。
- **跨环境自适应** —— 没装的工具、不存在的目录会自动置灰跳过，不会因为环境缺东西就报错；同一份脚本在不同机器上都能跑。
- **一道确认闸门** —— 勾选过程随便改，真正执行前弹出确认弹窗，列全选中项并单独标出「会删数据 / 需 sudo」的项。
- **应用插件** —— 针对具体软件的清理规则（Claude、思源笔记……）写成 JSON，随包分发、在 TUI 独立区域开箱即选；想加新软件只需丢一个 JSON 文件，不用改代码。
- **可自定义** —— 通过 `custom.json` 添加你自己想清理的路径。

> [!WARNING]
> 这个工具会**真实删除文件**，其中部分项（用户目录、回收站、应用配置、系统缓存）删除后无法恢复。清理范围对应作者的使用习惯，请在勾选前看清右侧命令预览，**确认每一项要删什么再执行**。默认只勾选缓存类，危险项需要你主动选中——这是有意为之的安全设计。

## 📋 清理项一览

启动后进入 TUI 勾选界面，左侧分成上下两块：**「清理项」**（下表的通用项）和 **「应用插件」**（针对具体软件的规则，含 Claude，详见 [应用插件](#-应用插件presets) 一节）。下表是「清理项」区，编号即列表顺序：

| # | 目标 | 性质 |
| --- | --- | --- |
| 01 | Docker：容器 / 镜像 / volume / 构建缓存 | 缓存 |
| 02 | pnpm store | 缓存 |
| 03 | npm cache（`_cacache` / `_logs` / `_npx`） | 缓存 |
| 04 | Bun：全局模块缓存（`~/.bun/install/cache`） | 缓存 |
| 05 | Go build / module / test / fuzz 缓存 | 缓存 |
| 06 | Rust：registry（含 index）与 git 缓存（保留 `~/.cargo/bin`，支持 `CARGO_HOME`） | 缓存 |
| 07 | SDKMAN：`sdk flush` + 删下载归档 `archives/`（支持 `SDKMAN_DIR`） | 缓存 |
| 08 | Gradle：`~/.gradle/caches`（支持 `GRADLE_USER_HOME`） | 缓存 |
| 09 | Maven：本地仓库 `~/.m2/repository` | 缓存 |
| 10 | 清空 `~/.cache/`（XDG 用户缓存，支持 `XDG_CACHE_HOME`） | 缓存 |
| 11 | 缩略图缓存：`~/.thumbnails` + `~/.cache/thumbnails` | 缓存 |
| 12 | 清空 `~/Documents`、`~/Downloads`、`~/Music`、`~/Pictures`、`~/Videos` 的内容（保留文件夹本身） | **用户数据** |
| 13 | 清空所有回收站：主回收站（`$XDG_DATA_HOME/Trash`）+ 各挂载盘的 `.Trash-<uid>` / `.Trash/<uid>` + 老版兼容路径 | **用户数据** |
| 14 | 递归删除家目录 `~` 下所有 `.log` 日志文件（跳过 `node_modules` / `.git`） | **用户数据** |
| 15 | `sudo dnf autoremove` + `sudo dnf clean all` | **系统（需 sudo）** |
| 16 | `sudo apt-get autoremove` + `sudo apt-get clean` | **系统（需 sudo）** |
| 17 | 清空 `/var/cache/man`、`/var/cache/fontconfig`、`/var/cache/PackageKit`、`/var/cache/cups` | **系统（需 sudo）** |
| 18 | 清空全部 systemd 日志（`sudo journalctl --rotate` + `--vacuum-time=1s`，不保留历史） | **系统（需 sudo）** |
| 19 | 崩溃报告 / core dump：`/var/crash`、systemd-coredump | **系统（需 sudo）** |
| 20 | 删除 snap 旧版本（disabled 的 revision，保留当前版本） | **系统（需 sudo）** |
| 21 | flatpak 未用 runtime（`flatpak uninstall --unused`，用户级 + 系统级） | **系统（需 sudo）** |
| 22 | 读 `~/.config/clean-sweep-tui/custom.json` 中 `paths` 列表，删除指定路径（**包括路径本身**） | **用户自定义** |

> 「应用插件」区（Claude、思源笔记等针对具体软件的清理）单独列在界面下方，数量随规则文件变化，不在上表编号内——见 [应用插件](#-应用插件presets) 一节。

关于这份清单的几条重要说明：

- **缺失的工具会自动跳过**：检测不到（没装 Docker、没有回收站、`custom.json` 未配置等）的项在列表里直接置灰、无法勾选。
- **默认勾选策略**：缓存类（# 01–11）默认就勾上了；标了 `!` 的用户数据 / 系统项默认**不勾**，要删得自己用空格选中。应用插件同理——`cache` 类默认勾、`config` 类（如 Claude）默认不勾。
- **# 14** 只扫描家目录 `~`，不会动 `/var/log` 等系统日志；只删常规文件，不跟随符号链接，且跳过 `node_modules` / `.git` 目录（不误删项目与依赖里的日志）。
- **# 15–21** 需要 `sudo`，执行阶段会按需弹出密码提示；# 15 仅 Fedora/RHEL 系有效，# 16 仅 Debian/Ubuntu 系有效，# 20/21 需装了 snap/flatpak，其余发行版 / 未安装会置灰。`/var/cache` 下没列出的子目录不会被动到。
- **# 22** 没有配置文件时置灰。

## 🚀 安装与使用

仅支持 Linux，需要 Python 3.10+。

### 方式一：从 PyPI 安装（推荐）

命令行工具用 [pipx](https://pipx.pypa.io/) 或 [uv](https://docs.astral.sh/uv/) 装到独立环境，装完直接敲 `clean-sweep-tui` 启动：

```bash
pipx install clean-sweep-tui      # 或
uv tool install clean-sweep-tui

clean-sweep-tui
```

> 现在的 Debian/Ubuntu 因 [PEP 668](https://peps.python.org/pep-0668/) 会拦截 `sudo pip install` 系统级安装，pipx / uv tool 是装 CLI 工具的正确方式。

### 方式二：从源码运行

需要 [uv](https://docs.astral.sh/uv/)：

```bash
# 1. 克隆仓库
git clone https://github.com/LumiDesk/clean-sweep-tui.git
cd clean-sweep-tui

# 2. 同步依赖
uv sync

# 3. 启动
uv run main.py
```

### TUI 操作

| 按键 | 作用 |
| --- | --- |
| `↑` / `↓`（或 `j` / `k`） | 在当前区域内上下移动，右侧实时显示该项将要执行的命令 |
| `Tab` / `Shift+Tab` | 在「清理项」与「应用插件」两个区域间切换焦点 |
| `空格` | 勾选 / 取消当前项 |
| `a` | 全选 |
| `n` | 全不选 |
| `c` | 只选缓存类 |
| `回车` | 执行：弹出一次性确认，列出全部选中项并标出会删数据 / 需 sudo 的项；再按 `回车` 确认，`esc` 取消 |
| `q` | 退出，什么都不做 |

确认后 TUI 退出，回到普通终端逐条打印并执行命令（sudo 密码也在这一步输入）。

## ⚙️ 自定义清理（custom.json）

想清理清单之外的路径？在 `~/.config/clean-sweep-tui/custom.json` 放一份配置（支持 `XDG_CONFIG_HOME`）：

```json
{
  "paths": [
    "~/某个临时目录",
    "/tmp/foo"
  ]
}
```

- 支持 `~` 展开；不存在或危险（根目录 `/`、家目录本身）的路径会被自动排除，整项无可删路径时置灰。
- 确认后用 `rm -rf` 删除，**路径本身一并删掉**（与 # 12 只清空内容不同），请谨慎填写。

## 🧩 应用插件（presets）

`custom.json` 是「你临时列几条路径」，**应用插件**是「预先写好、按软件分组的规则库」：每个软件（Claude、思源笔记、各类编辑器……）的清理路径写成一个 JSON 文件，启动后自动扫描，在 TUI 左侧下方的**「应用插件」独立区域**展示，和通用清理项分开。**想支持一个新软件，只要丢一个 JSON 文件，不用改代码——连 Claude 本身也是一个内置 JSON。**

扫描两个目录，**同 `key` 时用户目录覆盖内置**：

| 来源 | 位置 | 说明 |
| --- | --- | --- |
| 内置 | 随包分发的 `clean_sweep_tui/presets/*.json` | 项目自带的规则库（目前含 Claude、思源笔记） |
| 用户 | `~/.config/clean-sweep-tui/presets/*.json`（支持 `XDG_CONFIG_HOME`） | 你自己加的 / 覆盖内置同 key 的规则 |

一个预设 JSON 长这样（与 `custom.json` 一样只支持「删路径」模型）：

```json
{
  "key": "siyuan",
  "name": "思源笔记（配置 + 默认工作区）",
  "category": "config",
  "note": "删 ~/SiYuan 默认工作区 + ~/.config/siyuan + SiYuan-Electron 用户数据；笔记请确认放在别处",
  "paths": [
    "~/SiYuan",
    "~/.config/siyuan",
    "~/.config/SiYuan-Electron"
  ]
}
```

- `key`（必填）：稳定标识，同 `key` 的用户预设会覆盖内置预设。
- `name`（必填）：列表显示名。
- `paths`（必填）：要 `rm -rf` 的路径，支持 `~` 展开；不存在或危险路径自动排除，全没有时整项置灰。**删的是路径本身**。
- `category`（可选，默认 `cache`）：`cache` 默认勾选、无标记；`user_data` / `config` / `system` / `custom` 会带 `!` 标记、默认不勾。决定默认勾选与危险提示，仅影响安全分级，不会加 `sudo`。
- `note`（可选）：一行简介。

内置规则现有两条，都是 `config` 类（默认**不勾**、带 `!`，需主动选中）：

- **Claude**：删除 `~/.claude` 与 `~/.claude.json`（配置 / 历史 / 项目记录）。
- **思源笔记**：删除整个 `~/SiYuan`（默认工作区）、`~/.config/siyuan`（思源配置）和 `~/.config/SiYuan-Electron`（Electron 用户数据）——即「除程序本体与真实工作区外的所有配置」。

> [!WARNING]
> 思源这条会删掉**整个默认工作区 `~/SiYuan`**。如果你的笔记就放在那里，**不要勾选它**；笔记放在别处时这一项才安全。工作区路径不同的话，复制内置规则到用户预设目录、改 `paths` 即可（同 `key` 自动覆盖内置）。

## 🛡️ 它不会做什么

- 不会动 `~/.cargo/bin`（保留已安装的 cargo 命令）。
- 不会删上面清单之外的任何东西，也不会替你勾选危险项。
- 不用猜每条命令长什么样：选中某项时右侧预览就是即将执行的原始命令，所见即所删。

## 🤝 贡献

欢迎提 Issue 和 PR。新增清理项时请注意把它归到正确的安全分级（缓存 / 用户数据 / 系统 / 配置 / 自定义），项目的开发约定见 [CLAUDE.md](CLAUDE.md)。

## 📄 License

本项目以 [GNU General Public License v3.0](LICENSE) 授权发布。你可以自由使用、修改和分发本软件，但衍生作品必须同样以 GPLv3 开源。
