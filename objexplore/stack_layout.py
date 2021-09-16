from dataclasses import dataclass
from typing import List, Optional

from rich.layout import Layout
from rich.panel import Panel
from rich.tree import Tree

from .cached_object import CachedObject
from .explorer_layout import ExplorerLayout
from .overview_layout import OverviewLayout


@dataclass
class StackFrame:
    """ Datastructure to store a frame in the object stack """

    cached_obj: CachedObject
    explorer_layout: ExplorerLayout
    overview_layout: OverviewLayout


class StackLayout(Layout):
    def __init__(self, head_obj: CachedObject, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.head_obj = head_obj
        self.stack: List[StackFrame] = []
        self.index = 0
        self.window = 0

    def append(self, stack_frame: StackFrame):
        self.stack.append(stack_frame)

    def pop(self) -> Optional[StackFrame]:
        if len(self.stack) > 1:
            return self.stack.pop()

    def __getitem__(self, item):
        return self.stack[item]

    def set_visible(self):
        self.visible = True
        self.index = len(self.stack) - 1

    def __call__(self) -> Layout:
        stack_tree = None

        for index, stack_frame in enumerate(self.stack):
            if index == self.index:
                style = "reverse"
            else:
                style = "none"

            if not stack_tree:
                label = stack_frame.cached_obj.repr
                label.style = style
                stack_tree = Tree(label)
                continue

            stack_tree.add(
                stack_frame.cached_obj.attr_name
                + ": "
                + str(stack_frame.cached_obj.typeof),
                style=style,
            )

        self.update(
            Panel(
                stack_tree,
                title="\[stack]",
                title_align="right",
                subtitle="[dim][u]j[/u]:down [u]k[/u]:up [u]enter[/u]:select",
                subtitle_align="right",
                style="bright_blue",
            )
        )
        return self

    def move_up(self):
        if self.index > 0:
            self.index -= 1
            if self.index < self.window:
                self.window -= 1

    def move_down(self, panel_height: int):
        if self.index < len(self.stack) - 1:
            self.index += 1
            if self.index > self.window + panel_height:
                self.window += 1

    def select(self):
        self.stack = self.stack[: self.index + 1]
        stack_frame = self.stack.pop()
        return stack_frame.cached_obj
