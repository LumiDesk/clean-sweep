# cleansh

一键清空各类开发缓存，以及部分用户目录、应用配置的命令行小工具。

> ⚠️ **这是自用脚本，未必适合所有人。** 它会按作者本人的工作习惯做删除（缓存、用户家目录下的常见文件夹、Claude 配置等），里面的目录和清理范围都是写死的。请先读完源码、确认每一步要删什么，再决定是否使用。

## 它会做什么

按顺序执行：

| Step | 目标 | 性质 |
| --- | --- | --- |
| 01 | Docker：容器 / 镜像 / volume / 构建缓存 | 缓存 |
| 02 | pnpm store | 缓存 |
| 03 | npm cache | 缓存 |
| 04 | Go build / module / test / fuzz 缓存 | 缓存 |
| 05 | Rust：registry 与 git 缓存（保留 `~/.cargo/bin`） | 缓存 |
| 06 | SDKMAN：`sdk flush` | 缓存 |
| 07 | 清空 `~/.cache/`（XDG 用户缓存，含浏览器 / IDE / 缩略图等） | 缓存 |
| 08 | 清空 `~/Desktop`、`~/Documents`、`~/Downloads`、`~/Music`、`~/Pictures`、`~/Videos` 的内容（保留文件夹本身） | **用户数据** |
| 09 | 清空 `~/.local/share/Trash`（回收站） | **用户数据** |
| 10 | 删除 `~/.claude` 文件夹和 `~/.claude.json` | **应用配置** |
| 11 | `sudo dnf autoremove` + `sudo dnf clean all` | **系统（需 sudo）** |
| 12 | `sudo apt-get autoremove` + `sudo apt-get clean` | **系统（需 sudo）** |
| 13 | 清空 `/var/cache/man`、`/var/cache/fontconfig`、`/var/cache/PackageKit`、`/var/cache/cups` | **系统（需 sudo）** |
| 14 | `sudo journalctl --vacuum-time=7d` 清理 systemd 日志 | **系统（需 sudo）** |

- 缺失的工具会自动跳过（比如没装 Docker 就跳 Step 01）。
- Step 08、09、10、11、12、13、14 删的不是缓存（或涉及系统级改动），每步都有**单独的二次确认**，默认 No。
- Step 11、12、13、14 需要 `sudo`，会按需弹出密码提示；Step 11 仅 Fedora/RHEL 系有效，Step 12 仅 Debian/Ubuntu 系有效，其他发行版会跳过。`/var/cache` 下没列出的子目录不会被动到。

## 使用

需要 Python 3.14 和 [uv](https://docs.astral.sh/uv/)。

```bash
uv sync
uv run main.py
```

启动时会有一次总确认；遇到 Step 07 / 08 还会再问一遍——想跳过就在那两步回车（默认 No）即可。

## 不会做什么

- 不会动 `~/.cargo/bin`（保留已安装的 cargo 命令）。
- 不会删用户家目录下除上述清单之外的任何东西。
- 没有 dry-run 模式。要看每条命令长什么样，直接读 [cleaners/](cleaners/) 下的源码——一共一百多行，很短。

## License

见 [LICENSE](LICENSE)。
