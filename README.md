# CleanSweep

一键清空各类开发缓存，以及部分用户目录、应用配置的命令行小工具，仅支持 Linux。

> ⚠️ **这是自用脚本，未必适合所有人。** 它会按作者本人的工作习惯做删除（缓存、用户家目录下的常见文件夹、Claude 配置等），里面的目录和清理范围都是写死的。请先读完源码、确认每一步要删什么，再决定是否使用。

## 它会做什么

按顺序执行：

| Step | 目标 | 性质 |
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
| 11 | 删除 `~/.claude` 文件夹和 `~/.claude.json` | **应用配置** |
| 12 | `sudo dnf autoremove` + `sudo dnf clean all` | **系统（需 sudo）** |
| 13 | `sudo apt-get autoremove` + `sudo apt-get clean` | **系统（需 sudo）** |
| 14 | 清空 `/var/cache/man`、`/var/cache/fontconfig`、`/var/cache/PackageKit`、`/var/cache/cups` | **系统（需 sudo）** |
| 15 | 清空全部 systemd 日志（`sudo journalctl --rotate` + `--vacuum-time=1s`，不保留历史） | **系统（需 sudo）** |
| 16 | 读项目根目录 `custom.json` 中 `paths` 列表，删除指定路径（**包括路径本身**） | **用户自定义** |

- 缺失的工具会自动跳过（比如没装 Docker 就跳 Step 01）。
- Step 09、10、11、12、13、14、15、16 删的不是缓存（或涉及系统级改动），每步都有**单独的二次确认**，默认 No。
- Step 12、13、14、15 需要 `sudo`，会按需弹出密码提示；Step 12 仅 Fedora/RHEL 系有效，Step 13 仅 Debian/Ubuntu 系有效，其他发行版会跳过。`/var/cache` 下没列出的子目录不会被动到。
- Step 16 没有配置文件时直接跳过。配置示例：

  ```json
  {
    "paths": [
      "~/某个临时目录",
      "/tmp/foo"
    ]
  }
  ```

  支持 `~` 展开；不存在的路径会逐条提示并跳过；确认后会用 `rm -rf` 删除（**路径本身一并删掉**，与 Step 09 只清空内容不同）。根目录 `/` 和家目录本身会被直接拒绝，不会删。

## 使用

需要 Python 3.14 和 [uv](https://docs.astral.sh/uv/)，仅支持 Linux。

```bash
uv sync
```

```bash
uv run main.py
```

启动时会有一次总确认；后续涉及用户数据 / 系统级 / 自定义的步骤会再单独询问一次——想跳过就在那几步回车（默认 No）即可。

## 不会做什么

- 不会动 `~/.cargo/bin`（保留已安装的 cargo 命令）。
- 不会删用户家目录下除上述清单之外的任何东西。
- 没有 dry-run 模式。要看每条命令长什么样，直接读 [cleaners/](cleaners/) 下的源码——一共一百多行，很短。

## License

见 [LICENSE](LICENSE)。
