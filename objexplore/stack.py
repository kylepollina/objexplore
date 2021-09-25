from dataclasses import dataclass
from typing import List, Optional

import rich
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from rich.tree import Tree

from .cached_object import CachedObject
from .filter import Filter

console = Console()


@rich.repr.auto
@dataclass
class StackFrame:
    """ Datastructure to store a frame in the object stack """

    # flake8: noqa
    cached_obj: CachedObject
    filter: Filter
    state: "ExplorerState"  # type: ignore
    public_index: int
    public_window: int
    private_index: int
    private_window: int
    dict_index: int
    dict_window: int
    list_index: int
    list_window: int


class Stack:
    def __init__(self, head_obj: CachedObject):
        self.head_obj = head_obj
        self.index = 0
        self.layout = Layout(visible=False)
        self.stack: List[StackFrame] = []

    def push(self, stack_frame: StackFrame):
        self.stack.append(stack_frame)

    def pop(self) -> Optional[StackFrame]:
        if self.stack:
            return self.stack.pop()
        return None

    def __getitem__(self, item):
        return self.stack[item]

    def set_visible(self):
        self.layout.visible = True
        self.index = len(self.stack)

    def get_layout(self, width: int, current_obj: CachedObject) -> Layout:

        # Add the head obj as the base of the tree
        head_label = self.head_obj.repr
        if self.index == 0:
            head_label.style = Style(reverse=True)
        else:
            head_label.style = Style()

        head_label.truncate(width)
        stack_tree = Tree(head_label)

        # Go through the stack and add to the stack tree
        for index, stack_frame in enumerate(self.stack[1:]):
            if index + 1 == self.index:
                style = Style(reverse=True)
            else:
                style = Style()

            label = (
                Text(stack_frame.cached_obj.attr_name)
                + Text(": ")
                + stack_frame.cached_obj.typeof
            )
            label.overflow = "ellipsis"
            label.truncate(width - 4)
            stack_tree.add(
                label,
                style=style,
            )

        if self.stack != []:
            # Finally add the current obj to the tree just for clarity sake on what is being looked at
            # Only do it if the stack is not empty since we already have the head obj at the base of the tree
            if self.index == len(self.stack):
                style = Style(reverse=True)
            else:
                style = Style()
            label = Text(current_obj.attr_name) + Text(": ") + current_obj.typeof
            label.overflow = "ellipsis"
            label.truncate(width - 4)
            stack_tree.add(
                label,
                style=style,
            )

        subtitle = "[dim][u]space[/u]:select"
        if len(console.render_str(subtitle)) > width:
            subtitle = ""

        self.layout.update(
            Panel(
                stack_tree,
                title="\[stack]",
                title_align="right",
                subtitle=subtitle,
                subtitle_align="right",
                style="bright_blue",
            )
        )
        self.layout.size = len(self.stack) + 5
        return self.layout

    def move_up(self):
        if self.index > 0:
            self.index -= 1

    def move_down(self):
        if self.index < len(self.stack):
            self.index += 1

    def move_top(self):
        self.index = 0

    def move_bottom(self):
        self.index = len(self.stack) - 1

    def select(self) -> Optional[StackFrame]:
        """The stack always contains every stack frame including the current frame
        so selecting based on the index, we want to rebuild the stack to be everything
        up to the selected index and then pop the very top off and return

        TODO more documentation
        """
        if self.index != len(self.stack):
            self.stack = self.stack[: self.index + 1]
            if self.stack:
                return self.stack.pop()
        return None
