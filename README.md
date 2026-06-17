# CleanSweep

一键清空各类开发缓存，以及部分用户目录、应用配置的 TUI 小工具，仅支持 Linux。

> ⚠️ **这是自用脚本，未必适合所有人。** 它会按作者本人的工作习惯做删除（缓存、用户家目录下的常见文件夹、Claude 配置等），里面的目录和清理范围都是写死的。请先读完源码、确认每一项要删什么，再决定是否使用。

## 它会做什么

启动后进入一个 TUI 勾选界面，下面这些是可勾选的清理项（编号即列表顺序）：

| # | 目标 | 性质 |
| --- | --- | --- |
| 01 | Docker：容器 / 镜像 / volume / 构建缓存 | 缓存 |
| 02 | pnpm store | 缓存 |
| 03 | npm cache | 缓存 |
| 04 | Bun：全局模块缓存（`~/.bun/install/cache`） | 缓存 |
| 05 | Go build / module / test / fuzz 缓存 | 缓存 |
| 06 | Rust：registry 与 git 缓存（保留 `~/.cargo/bin`） | 缓存 |
| 07 | SDKMAN：`sdk flush` | 缓存 |
| 08 | 清空 `~/.cache/`（XDG 用户缓存，含浏览器 / IDE / 缩略图等） | 缓存 |
| 09 | 清空 `~/Documents`、`~/Downloads`、`~/Music`、`~/Pictures`、`~/Videos` 的内容（保留文件夹本身） | **用户数据** |
| 10 | 清空 `~/.local/share/Trash`（回收站） | **用户数据** |
| 11 | 递归删除家目录 `~` 下所有 `.log` 日志文件 | **用户数据** |
| 12 | 删除 `~/.claude` 文件夹和 `~/.claude.json` | **应用配置** |
| 13 | `sudo dnf autoremove` + `sudo dnf clean all` | **系统（需 sudo）** |
| 14 | `sudo apt-get autoremove` + `sudo apt-get clean` | **系统（需 sudo）** |
| 15 | 清空 `/var/cache/man`、`/var/cache/fontconfig`、`/var/cache/PackageKit`、`/var/cache/cups` | **系统（需 sudo）** |
| 16 | 清空全部 systemd 日志（`sudo journalctl --rotate` + `--vacuum-time=1s`，不保留历史） | **系统（需 sudo）** |
| 17 | 读项目根目录 `custom.json` 中 `paths` 列表，删除指定路径（**包括路径本身**） | **用户自定义** |

- 缺失的工具会自动跳过：检测不到（没装 Docker、没有回收站、custom.json 未配置等）的项在列表里直接置灰、无法勾选。
- 缓存类（# 01–08）默认就勾上了；标了 `!` 的用户数据 / 配置 / 系统项默认**不勾**，要删得自己用空格选中。
- # 11 只扫描家目录 `~`，不会动 `/var/log` 等系统日志；只删常规文件，不跟随符号链接。
- # 13、14、15、16 需要 `sudo`，执行阶段会按需弹出密码提示；# 13 仅 Fedora/RHEL 系有效，# 14 仅 Debian/Ubuntu 系有效，其他发行版会置灰。`/var/cache` 下没列出的子目录不会被动到。
- # 17 没有配置文件时置灰。配置示例：

  ```json
  {
    "paths": [
      "~/某个临时目录",
      "/tmp/foo"
    ]
  }
  ```

  支持 `~` 展开；不存在或危险（根目录 `/`、家目录本身）的路径会被排除，整项无可删路径时置灰；确认后会用 `rm -rf` 删除（**路径本身一并删掉**，与 # 09 只清空内容不同）。

## 使用

需要 Python 3.14 和 [uv](https://docs.astral.sh/uv/)，仅支持 Linux。

```bash
uv sync
```

```bash
uv run main.py
```

进入 TUI 后：

- `↑` / `↓`（或 `j` / `k`）移动，`空格` 勾选 / 取消，右侧实时显示该项将要执行的命令。
- `a` 全选、`n` 全不选、`c` 只选缓存类。
- `回车` 执行：弹出一次性确认，列出全部选中项并标出会删数据 / 需 sudo 的项；再按 `回车` 确认，`esc` 取消。
- `q` 退出，什么都不做。

确认后 TUI 退出，回到普通终端逐条打印并执行命令（sudo 密码也在这一步输入）。

## 不会做什么

- 不会动 `~/.cargo/bin`（保留已安装的 cargo 命令）。
- 不会删上面清单之外的任何东西，也不会替你勾选危险项。
- 不用猜每条命令长什么样：选中某项时右侧预览就是即将执行的原始命令，所见即所删。

## License

见 [LICENSE](LICENSE)。
