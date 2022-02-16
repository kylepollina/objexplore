from typing import List

import blessed
import rich
from blessed import Terminal
from blessed.keyboard import Keystroke
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from .cached_object import CachedObject
from .config import box_type

console = Console()
highlighter = ReprHighlighter()

# TODO scroll search if input longer than panel width


def isclass(cached_obj: CachedObject):
    return cached_obj.isclass


def isfunction(cached_obj: CachedObject):
    return cached_obj.isfunction


def ismethod(cached_obj: CachedObject):
    return cached_obj.ismethod


def ismodule(cached_obj: CachedObject):
    return cached_obj.ismodule


def isbuiltin(cached_obj: CachedObject):
    return cached_obj.isbuiltin


def isint(cached_obj: CachedObject):
    return type(cached_obj.obj) == int


def isstr(cached_obj: CachedObject):
    return type(cached_obj.obj) == str


def isfloat(cached_obj: CachedObject):
    return type(cached_obj.obj) == float


def isbool(cached_obj: CachedObject):
    return type(cached_obj.obj) == bool


def isdict(cached_obj: CachedObject):
    return type(cached_obj.obj) == dict


def islist(cached_obj: CachedObject):
    return type(cached_obj.obj) == list


def istuple(cached_obj: CachedObject):
    return type(cached_obj.obj) == tuple


def isset(cached_obj: CachedObject):
    return type(cached_obj.obj) == set


@rich.repr.auto
class Filter:
    def __init__(self, term: Terminal):
        self.term = term
        self.layout = Layout(visible=False)

        self.filters = {
            "class": [False, isclass],
            "function": [False, isfunction],
            "method": [False, ismethod],
            "module": [False, ismodule],
            "int": [False, isint],
            "str": [False, isstr],
            "float": [False, isfloat],
            "bool": [False, isbool],
            "dict": [False, isdict],
            "list": [False, islist],
            "tuple": [False, istuple],
            "set": [False, isset],
            "builtin": [False, isbuiltin],
        }
        self.index = 0
        self.receiving_input = False
        self.search_filter = ""
        self.cursor_pos = 0
        self.key_history: List[Keystroke] = []

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

    def get_enabled_filters(self) -> list:
        return [
            function
            for name, (enabled, function) in self.filters.items()
            if enabled is True
        ]

    @property
    def selected_filter(self):
        return list(self.filters.keys())[self.index]

    def toggle(self, cached_obj: CachedObject):
        """ Toggle the selected filter on or off and update the cached_obj filters with the new filters """
        self.filters[self.selected_filter][0] = not self.filters[self.selected_filter][
            0
        ]
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
        self,
        key: blessed.keyboard.Keystroke,
        cached_obj: CachedObject,
        live_update: bool,
    ):
        self.key_history.append(key)
        self.search_filter = (
            self.search_filter[: self.cursor_pos]
            + str(key)
            + self.search_filter[self.cursor_pos :]
        )
        self.cursor_pos += 1

        if live_update:
            cached_obj.set_filters(self.get_enabled_filters(), self.search_filter)

    def backspace(self, cached_obj: CachedObject, live_update: bool):
        """Delete the character before the cursor.
        Args:
            cached_obj: The current object being explored.
            live_update: True/False value whether to update the cached_obj
                filters. If there are too many attributes then updating the
                filters will slow down.
        """
        if self.cursor_pos == 0 and self.search_filter == "":
            self.cancel_search(cached_obj)
        # if the cursor is at the beginning but there is still text in the search, do nothing
        elif self.cursor_pos == 0 and self.search_filter:
            return

        self.search_filter = (
            self.search_filter[: self.cursor_pos - 1]
            + self.search_filter[self.cursor_pos :]
        )
        self.cursor_left()

        if live_update:
            cached_obj.set_filters(self.get_enabled_filters(), self.search_filter)

    def cancel_search(self, cached_obj: CachedObject):
        self.search_filter = ""
        self.cursor_pos = 0
        self.layout.visible = False
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
        self.layout.visible = False
        cached_obj.set_filters(
            self.get_enabled_filters(), search_filter=self.search_filter
        )

    def get_layout(self, width: int) -> Layout:
        if self.receiving_input:
            return self.get_input_layout()

        subtitle = "[dim][u]c[/u]:clear [u]space[/u]:select"
        if width <= 25:
            subtitle = "[dim][u]space[/u]:select"
        if len(console.render_str(subtitle)) > width:
            subtitle = ""

        lines = self.get_lines()
        self.layout.update(
            Panel(
                Text("\n").join(lines),
                title="\[filter]",
                title_align="right",
                subtitle=subtitle,
                subtitle_align="right",
                style="bright_magenta",
                box=box_type,
            )
        )
        self.layout.size = len(lines) + 2
        return self.layout

    def get_input_layout(self) -> Layout:
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

        self.layout.update(
            Panel(
                search_text,
                title="\[search]",
                title_align="right",
                subtitle="[dim][u]esc[/u]:cancel",
                subtitle_align="right",
                style=Style(color="aquamarine1"),
                box=box_type,
            )
        )
        self.layout.size = 3
        return self.layout
