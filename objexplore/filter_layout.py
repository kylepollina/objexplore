
from typing import List, Dict

import types

from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from .cached_object import CachedObject


class FilterLayout(Layout):
    def __init__(self, cached_obj: CachedObject, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cached_obj = cached_obj
        self.filters: Dict[str, List[bool, types.FunctionType]] = {
            'class': [False, lambda cached_obj: cached_obj.isclass],
            'function': [False, lambda cached_obj: cached_obj.isfunction],
            'method': [False, lambda cached_obj: cached_obj.ismethod],
            'module': [False, lambda cached_obj: cached_obj.ismodule],
            'int': [False, lambda cached_obj: type(cached_obj.obj) == int],
            'float': [False, lambda cached_obj: type(cached_obj.obj) == float],
            'bool': [False, lambda cached_obj: type(cached_obj.obj) == bool],
            'dict': [False, lambda cached_obj: type(cached_obj.obj) == dict],
            'list': [False, lambda cached_obj: type(cached_obj.obj) == list],
            'tuple': [False, lambda cached_obj: type(cached_obj.obj) == tuple],
            'set': [False, lambda cached_obj: type(cached_obj.obj) == set],
            'builtin': [False, lambda cached_obj: cached_obj.isbuiltin],
        }
        self.index = 0
        self.cached_obj.set_filters(self.get_enabled_filters())

    def move_down(self):
        if self.index < len(self.filters) - 1:
            self.index += 1

    def move_up(self):
        if self.index > 0:
            self.index -= 1

    def get_enabled_filters(self) -> List[types.FunctionType]:
        return [method for name, (enabled, method) in self.filters.items() if enabled is True]

    def toggle(self):
        filter_name = list(self.filters.keys())[self.index]
        self.filters[filter_name][0] = not self.filters[filter_name][0]
        self.cached_obj.set_filters(self.get_enabled_filters())

    def get_lines(self) -> List[Text]:
        lines = []
        for index, (name, (enabled, method)) in enumerate(self.filters.items()):
            line = (
                Text("[", style=Style(color="white"))
                + Text("X" if enabled else " ", style=Style(color="blue"))
                + Text("] ", style=Style(color="white"))
                + Text(name, style=Style(color="white"))
            )
            if index == self.index:
                line.style += Style(reverse=True)
            lines.append(line)
        return lines

    def __call__(self):
        lines = self.get_lines()
        self.update(
            Panel(
                Text("\n").join(lines),
                title="filter"
            )
        )
        return self
