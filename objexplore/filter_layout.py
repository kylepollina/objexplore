import types
from typing import Dict, List, Union

from rich.highlighter import ReprHighlighter
from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
import rich

from .explorer_layout import ExplorerLayout
from .cached_object import CachedObject
from .terminal import Terminal

highlighter = ReprHighlighter()

# TODO scroll search if input longer than panel width


@rich.repr.auto
class FilterLayout(Layout):
    def __init__(self, term: Terminal, *args, **kwargs):
        self.filters: Dict[str, List[Union[bool, types.FunctionType]]] = {
            "class": [False, lambda cached_obj: cached_obj.isclass],
            "function": [False, lambda cached_obj: cached_obj.isfunction],
            "method": [False, lambda cached_obj: cached_obj.ismethod],
            "module": [False, lambda cached_obj: cached_obj.ismodule],
            "int": [False, lambda cached_obj: type(cached_obj.obj) == int],
            "str": [False, lambda cached_obj: type(cached_obj.obj) == str],
            "float": [False, lambda cached_obj: type(cached_obj.obj) == float],
            "bool": [False, lambda cached_obj: type(cached_obj.obj) == bool],
            "dict": [False, lambda cached_obj: type(cached_obj.obj) == dict],
            "list": [False, lambda cached_obj: type(cached_obj.obj) == list],
            "tuple": [False, lambda cached_obj: type(cached_obj.obj) == tuple],
            "set": [False, lambda cached_obj: type(cached_obj.obj) == set],
            "builtin": [False, lambda cached_obj: cached_obj.isbuiltin],
        }
        self.term = term
        self.index = 0
        self.receiving_input = False
        self.search_filter = ""
        self.cursor_pos = 0
        self.key_history = []
        super().__init__(*args, **kwargs)

    def move_down(self):
        if self.index < len(self.filters) - 1:
            self.index += 1

    def move_up(self):
        if self.index > 0:
            self.index -= 1

    def move_top(self):
        self.index = 0

    def move_bottom(self):
        self.index = len(self.filters) - 1

    def get_enabled_filters(self) -> List[types.FunctionType]:
        return [
            method
            for name, (enabled, method) in self.filters.items()
            if enabled is True
        ]

    def toggle(self, cached_obj: CachedObject):
        """ Toggle the selected filter on or off and update the cached_obj filters with the new filters """
        filter_name = list(self.filters.keys())[self.index]
        self.filters[filter_name][0] = not self.filters[filter_name][0]
        cached_obj.set_filters(self.get_enabled_filters(), self.search_filter)

    def clear_filters(self, cached_obj: CachedObject):
        for name, filter_data in self.filters.copy().items():
            self.filters[name][0] = False
        self.search_filter = ""
        self.cursor_pos = 0
        cached_obj.set_filters([])

    def get_lines(self) -> List[Text]:
        lines = []
        for index, (name, (enabled, method)) in enumerate(self.filters.items()):
            line = (
                Text("[", style=Style(color="white"))
                + Text("X" if enabled else " ", style=Style(color="blue"))
                + Text("] ", style=Style(color="white"))
                + Text(name, style=Style(color="magenta"))
            )
            if index == self.index:
                line.style += Style(reverse=True)  # type: ignore
            lines.append(line)

        if self.search_filter:
            lines.extend(
                [
                    Text("Search filter:", style=Style(italic=True, underline=True)),
                    Text(" " + self.search_filter),
                ]
            )

        return lines

    def add_search_char(
        self, key: str, cached_obj: CachedObject, explorer_layout: ExplorerLayout
    ):
        self.key_history.append(key)
        self.search_filter = (
            self.search_filter[: self.cursor_pos]
            + str(key)
            + self.search_filter[self.cursor_pos :]
        )
        self.cursor_pos += 1

        if len(explorer_layout.get_all_attributes()) < 130:
            cached_obj.set_filters(self.get_enabled_filters(), self.search_filter)

    def backspace(self, cached_obj: CachedObject, explorer_layout: ExplorerLayout):
        if self.cursor_pos == 0 and not self.search_filter:
            self.cancel_search(cached_obj)
        elif self.cursor_pos == 0 and self.search_filter:
            return
        self.search_filter = (
            self.search_filter[: self.cursor_pos - 1]
            + self.search_filter[self.cursor_pos :]
        )
        self.cursor_left()

        if len(explorer_layout.get_all_attributes()) < 130:
            cached_obj.set_filters(self.get_enabled_filters(), self.search_filter)

    def cancel_search(self, cached_obj: CachedObject):
        self.search_filter = ""
        self.cursor_pos = 0
        self.visible = False
        self.receiving_input = False
        cached_obj.set_filters(self.get_enabled_filters(), self.search_filter)

    def cursor_left(self):
        if self.cursor_pos > 0:
            self.cursor_pos -= 1

    def cursor_right(self):
        if self.cursor_pos < len(self.search_filter):
            self.cursor_pos += 1

    def end_search(self, cached_obj: CachedObject):
        self.receiving_input = False
        self.visible = False
        cached_obj.set_filters(
            self.get_enabled_filters(), search_filter=self.search_filter
        )

    def __call__(self) -> Layout:
        if self.receiving_input:
            return self.input_box()

        subtitle = "[dim][u]c[/u]:clear [u]space[/u]:select"
        if self.term.explorer_panel_width <= 25:
            subtitle = "[dim][u]space[/u]:select"

        lines = self.get_lines()
        self.update(
            Panel(
                Text("\n").join(lines),
                title="\[filter]",
                title_align="right",
                subtitle=subtitle,
                subtitle_align="right",
                style="bright_magenta",
            )
        )
        self.size = len(lines) + 2
        return self

    def input_box(self) -> Layout:
        if len(self.search_filter) == 0:
            search_text = Text(
                "█", style=Style(underline=True, blink=True, reverse=True)
            )
        elif self.cursor_pos == len(self.search_filter):
            search_text = Text(self.search_filter) + Text(
                "█", style=Style(underline=True, blink=True, reverse=True)
            )
        else:
            search_text = (
                Text(self.search_filter[: self.cursor_pos])
                + Text(
                    self.search_filter[self.cursor_pos],
                    style=Style(
                        underline=True,
                        blink=True,
                        color="black",
                        bgcolor="aquamarine1",
                    ),
                )
                + Text(self.search_filter[self.cursor_pos + 1 :])
            )

        self.update(
            Panel(
                search_text,
                title="\[search]",
                title_align="right",
                subtitle="[dim][u]esc[/u]:cancel",
                subtitle_align="right",
                style=Style(color="aquamarine1"),
            )
        )
        self.size = 3
        return self
