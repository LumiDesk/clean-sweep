"""CleanSweep TUI 的前端（textual）。

交互：↑↓/jk 移动，空格勾选（TODO 式 [ ] / [x]），a 全选 / n 全不选 / c 仅缓存，
回车执行。右侧实时预览高亮项将要执行的命令。回车后弹出一次性确认，确认即返回
选中的 key 列表给入口去执行；取消或退出（q）返回 None。

勾选状态自己维护（OptionList 只负责导航），所以能完全控制每行前缀：可勾选项
显示 [ ]/[x]，不可用项不显示勾选框、整行置灰。
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, OptionList, Static
from textual.widgets.option_list import Option

from .cleaners.spec import Category, Step

# 每类一个文字徽章（不用 emoji，终端渲染稳定）。
_TAG = {
    Category.CACHE: "[green]缓存[/]",
    Category.USER_DATA: "[yellow]数据[/]",
    Category.SYSTEM: "[red]系统[/]",
    Category.CONFIG: "[magenta]配置[/]",
    Category.CUSTOM: "[cyan]自定[/]",
}

# TODO 式勾选框（\[ 转义成字面量左括号）。
_BOX_OFF = r"\[ ]"
_BOX_ON = r"\[[b green]x[/]]"


def _preview(step: Step) -> str:
    head = f"[b]{step.name}[/]  {_TAG[step.category]}"
    if step.needs_sudo:
        head += "  [red]需要 sudo[/]"
    lines = [head, ""]
    if not step.available:
        lines.append(f"[yellow]不可用：{step.reason}[/]")
        return "\n".join(lines)
    if step.destructive:
        lines.append("[red]! 删除用户数据 / 配置 / 系统状态，无法撤销[/]")
        lines.append("")
    if not step.cmds:
        lines.append("[dim]（无命令）[/]")
    for cmd in step.cmds:
        lines.append(f"[cyan]$ {cmd}[/]")
    return "\n".join(lines)


class CleanList(OptionList):
    """勾选列表：空格切换选中，回车请求执行，jk 移动。

    选中状态由 MainScreen 统一持有（一个共享 set），多个 CleanList 实例共用同一个
    set（通用清理项 / 应用插件各一个列表）；本类只负责渲染与切换自己那些行。
    """

    BINDINGS = [
        Binding("space", "toggle_select", "选择"),
        Binding("enter", "execute", "执行"),
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
    ]

    class ExecuteRequest(Message):
        pass

    def __init__(
        self, steps: list[Step], selected: set[str], list_id: str, title: str
    ) -> None:
        self._steps = steps
        self._by_key = {s.key: s for s in steps}
        # 共享选中集：只增删、不重新赋值，否则会与其它列表断开同步。
        self.selected = selected
        super().__init__(
            *(
                Option(self._render_row(s), id=s.key, disabled=not s.available)
                for s in steps
            ),
            id=list_id,
        )
        self.border_title = title

    def _render_row(self, step: Step) -> str:
        tag = _TAG[step.category]
        if not step.available:
            # 不可用：不显示勾选框，整行置灰，给出原因。
            return f"[dim]{tag} {step.name}  ·  {step.reason}[/]"
        box = _BOX_ON if step.key in self.selected else _BOX_OFF
        mark = "[red]![/]" if step.destructive else " "
        return f"{box} {mark} {tag} {step.name}  [dim]{step.note}[/]"

    def _toggle_index(self, index: int | None) -> None:
        if index is None:
            return
        key = self.get_option_at_index(index).id
        step = self._by_key.get(key) if key is not None else None
        if step is None or not step.available:
            return
        if step.key in self.selected:
            self.selected.discard(step.key)
        else:
            self.selected.add(step.key)
        self.replace_option_prompt_at_index(index, self._render_row(step))

    def refresh_rows(self) -> None:
        """按当前共享 selected 重绘所有行（供 MainScreen 的全选/全不选等调用）。"""
        for index, step in enumerate(self._steps):
            self.replace_option_prompt_at_index(index, self._render_row(step))

    def action_toggle_select(self) -> None:
        self._toggle_index(self.highlighted)

    def action_execute(self) -> None:
        self.post_message(self.ExecuteRequest())

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        # 鼠标点击也当成勾选切换（回车已被改成执行，不会走到这里）。
        event.stop()
        self._toggle_index(event.option_index)


class ConfirmScreen(ModalScreen[bool]):
    """一次性确认：列出将执行的项，回车/确认执行，esc/取消返回。"""

    BINDINGS = [
        Binding("enter", "confirm", "确认"),
        Binding("escape", "cancel", "取消"),
        Binding("n", "cancel", show=False),
    ]

    def __init__(self, chosen: list[Step]) -> None:
        super().__init__()
        self._chosen = chosen

    def compose(self) -> ComposeResult:
        lines = [f"将执行 [b]{len(self._chosen)}[/] 项清理：", ""]
        destructive = sum(s.destructive for s in self._chosen)
        sudo = sum(s.needs_sudo for s in self._chosen)
        for s in self._chosen:
            mark = "[red]![/]" if s.destructive else " "
            sudo_tag = " [red](sudo)[/]" if s.needs_sudo else ""
            lines.append(f"  {mark} {s.name}{sudo_tag}")
        lines.append("")
        if destructive:
            lines.append(f"[red]其中 {destructive} 项会删除数据/配置/系统状态，无法撤销。[/]")
        if sudo:
            lines.append(f"[yellow]有 {sudo} 项需要 sudo，执行时会提示输入密码。[/]")
        with VerticalScroll(id="dialog"):
            yield Static("\n".join(lines), id="summary")
            with Horizontal(id="buttons"):
                yield Button("执行", variant="error", id="confirm")
                yield Button("取消", variant="primary", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#confirm", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class MainScreen(Screen):
    BINDINGS = [
        Binding("a", "select_all", "全选"),
        Binding("n", "select_none", "全不选"),
        Binding("c", "select_cache", "仅缓存"),
        Binding("q", "quit", "退出"),
    ]

    def __init__(self, steps: list[Step]) -> None:
        super().__init__()
        self.steps = steps  # 全量、执行顺序；执行时按它过滤选中项
        self._by_key = {s.key: s for s in steps}
        # 通用清理项与应用插件分区展示；选中集两区共享。
        self._main = [s for s in steps if not s.plugin]
        self._plugins = [s for s in steps if s.plugin]
        # 默认勾选所有可用的缓存项；不可用 / 危险项默认不选。
        self.selected: set[str] = {
            s.key for s in steps if s.available and not s.destructive
        }

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="lists"):
                yield CleanList(self._main, self.selected, "list", "清理项")
                if self._plugins:
                    yield CleanList(
                        self._plugins, self.selected, "plugin-list", "应用插件"
                    )
            with VerticalScroll(id="preview-wrap"):
                yield Static("", id="preview")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#preview-wrap").border_title = "预览"
        first = self.query_one("#list", CleanList)
        first.focus()
        if self._main:
            self._show_preview(self._main[0])

    def _show_preview(self, step: Step) -> None:
        self.query_one("#preview", Static).update(_preview(step))

    def _refresh_lists(self) -> None:
        for cl in self.query(CleanList):
            cl.refresh_rows()

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        step = self._by_key.get(event.option_id)
        if step is not None:
            self._show_preview(step)

    def on_clean_list_execute_request(self, _: CleanList.ExecuteRequest) -> None:
        self.action_execute()

    def _set_selection(self, keys) -> None:
        # 原地改共享 set（不能重新赋值，否则与各 CleanList 断开同步），再重绘。
        self.selected.clear()
        self.selected.update(keys)
        self._refresh_lists()

    def action_select_all(self) -> None:
        self._set_selection(s.key for s in self.steps if s.available)

    def action_select_none(self) -> None:
        self._set_selection([])

    def action_select_cache(self) -> None:
        self._set_selection(
            s.key for s in self.steps if s.available and not s.destructive
        )

    def action_quit(self) -> None:
        self.app.exit(None)

    def action_execute(self) -> None:
        chosen = [s for s in self.steps if s.key in self.selected]
        if not chosen:
            self.notify("未选择任何清理项", severity="warning")
            return
        ordered = [s.key for s in chosen]

        def done(confirmed: bool | None) -> None:
            if confirmed:
                self.app.exit(ordered)

        self.app.push_screen(ConfirmScreen(chosen), done)


class CleanSweepApp(App[list[str]]):
    TITLE = "CleanSweep TUI"
    SUB_TITLE = "↑↓ 移动 · 空格选择 · 回车执行 · q 退出"

    CSS = """
    #lists {
        width: 1fr;
        margin: 0 1 0 0;
    }
    CleanList {
        width: 1fr;
        border: round $primary;
        padding: 0 1;
    }
    #list {
        height: 2fr;
        margin: 0 0 1 0;
    }
    #plugin-list {
        height: 1fr;
        border: round $accent;
    }
    #preview-wrap {
        width: 1fr;
        border: round $primary;
        padding: 0 1;
    }
    ConfirmScreen {
        align: center middle;
    }
    #dialog {
        width: 64;
        max-height: 80%;
        height: auto;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }
    #buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    #buttons Button {
        margin: 0 2;
    }
    """

    def __init__(self, steps: list[Step]) -> None:
        super().__init__()
        self._steps = steps

    def on_mount(self) -> None:
        self.push_screen(MainScreen(self._steps))
