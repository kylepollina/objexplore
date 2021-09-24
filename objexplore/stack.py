from dataclasses import dataclass
from typing import List, Optional

from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
import rich
from rich.tree import Tree

from .cached_object import CachedObject
from .overview import Overview


@dataclass
class StackFrame:
    """ Datastructure to store a frame in the object stack """

    cached_obj: CachedObject
    explorer: "Explorer"
    filter: "Filter"
    # overview_layout: Overview


class Stack:
    def __init__(self, head_obj: CachedObject, explorer, filter):
        self.head_obj = head_obj
        self.index = 0
        self.layout = Layout(visible=False)
        self.stack: List[StackFrame] = [
            StackFrame(cached_obj=head_obj, explorer=explorer, filter=filter)
        ]

    def push(self, cached_obj: CachedObject, explorer, filter):
        self.stack.append(
            StackFrame(cached_obj=cached_obj, explorer=explorer, filter=filter)
        )

    def pop(self) -> Optional[StackFrame]:
        if len(self.stack) > 1:
            return self.stack.pop()
        return None

    def __getitem__(self, item):
        return self.stack[item]

    def set_visible(self):
        self.layout.visible = True
        self.index = len(self.stack) - 1

    def get_layout(self, width: int) -> Layout:
        stack_tree: Tree

        for index, stack_frame in enumerate(self.stack):
            if index == self.index:
                style = "reverse"
            else:
                style = "none"

            if index == 0:
                label = stack_frame.cached_obj.repr.copy()
                label.style = style
                label.overflow = "ellipsis"
                label.truncate(max_width=width - 1)
                stack_tree = Tree(label, guide_style="white")
                continue

            label = (
                Text(stack_frame.cached_obj.attr_name)
                + Text(": ")
                + stack_frame.cached_obj.typeof
            )
            label.overflow = "ellipsis"
            label.truncate(max_width=width - 4)
            stack_tree.add(
                label,
                style=style,
            )

        self.layout.update(
            Panel(
                stack_tree,
                title="\[stack]",
                title_align="right",
                subtitle="[dim][u]space[/u]:select",
                subtitle_align="right",
                style="bright_blue",
            )
        )
        self.layout.size = len(self.stack) + 5
        return self.layout

    def move_up(self):
        if self.index > 0:
            self.index -= 1

    def move_down(self, panel_height: int):
        if self.index < len(self.stack) - 1:
            self.index += 1

    def move_top(self):
        self.index = 0

    def move_bottom(self):
        self.index = len(self.stack) - 1

    def select(self) -> CachedObject:
        """The stack always contains every stack frame including the current frame
        so selecting based on the index, we want to rebuild the stack to be everything
        up to the selected index and then pop the very top off and return

        TODO more documentation
        """
        self.stack = self.stack[: self.index + 1]
        stack_frame = self.stack.pop()
        return stack_frame.cached_obj
