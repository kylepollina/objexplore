import pydoc
import signal
from dataclasses import dataclass
from typing import Any, List, Optional

import blessed
from blessed import Terminal
from rich import print as rprint
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.tree import Tree

from .cached_object import CachedObject
from .explorer_layout import ExplorerLayout, ExplorerState
from .help_layout import HelpLayout, HelpState
from .overview_layout import OverviewLayout, OverviewState, PreviewState

version = "0.9.3"

# TODO methods filter
# or just a type filter?
# TODO for list/set/dict/tuple do length in info panel
# TODO empty overview layouts for when there are 0 public attributes


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
        self.visible = False
        return stack_frame.cached_obj


class Explorer:
    """ Explorer class used to interactively explore Python Objects """

    def __init__(self, obj: Any):
        cached_obj = CachedObject(obj, dotpath=repr(obj))
        # Figure out all the attributes of the current obj's attributes
        cached_obj.cache_attributes()

        # self.head_obj = cached_obj
        self.cached_obj: CachedObject = cached_obj
        self.term = Terminal()
        self.console = Console()
        self.stack = StackLayout(head_obj=self.cached_obj, visible=False)
        self.help_layout = HelpLayout(version, visible=False, ratio=3)
        self.explorer_layout = ExplorerLayout(cached_obj=cached_obj)
        self.overview_layout = OverviewLayout()

        self.stack.append(
            StackFrame(
                cached_obj=self.cached_obj,
                explorer_layout=self.explorer_layout,
                overview_layout=self.overview_layout,
            )
        )

        # Run self.draw() whenever the win change signal is caught
        signal.signal(signal.SIGWINCH, self.draw)

    def explore(self) -> Optional[Any]:
        """ Open the interactive explorer """

        key = None
        res = None

        # Clear the screen
        print(self.term.clear, end="")

        with self.term.cbreak(), self.term.hidden_cursor():
            while key not in ("q", "Q"):
                self.draw()
                key = self.term.inkey()
                res = self.process_key_event(key)

                # If the object is returned as a response the close the explorer and return the selected object
                if res:
                    break
        return res

    def process_key_event(self, key: blessed.keyboard.Keystroke) -> Any:
        """ Process the incoming key """

        # Help page ###########################################################

        if self.help_layout.visible:
            # Close help page
            if key in ("?", "\x1b"):
                self.help_layout.visible = False
                return

            # Fullscreen
            elif key == "f":
                with self.console.capture() as capture:
                    self.console.print(self.help_layout.text)
                str_out = capture.get()
                pydoc.pager(str_out)
                return

            # Switch panes
            elif key in ("{", "}", "[", "]"):
                if self.help_layout.state == HelpState.keybindings:
                    self.help_layout.state = HelpState.about
                elif self.help_layout.state == HelpState.about:
                    self.help_layout.state = HelpState.keybindings
                return

            elif key in ("j", "k") or key.code in (
                self.term.KEY_UP,
                self.term.KEY_DOWN,
            ):
                # Continue on and process these keys as normal
                self.help_layout.visible = False

            else:
                return

        if self.help_layout.visible is False and key == "?":
            self.help_layout.visible = True
            return

        # Navigation ##########################################################

        if self.stack.visible and (
            key not in ("o", "j", "k", "\n")
            and key.code
            not in (self.term.KEY_UP, self.term.KEY_DOWN, self.term.KEY_RIGHT)
        ):
            return

        # move selected attribute up
        elif key == "k" or key.code == self.term.KEY_UP:
            if self.stack.visible:
                self.stack.move_up()
            else:
                self.explorer_layout.move_up()

        # move selected attribute down
        elif key == "j" or key.code == self.term.KEY_DOWN:
            if self.stack.visible:
                self.stack.move_down(self.panel_height)
            else:
                self.explorer_layout.move_down(self.panel_height, self.cached_obj)

        # Enter
        elif key in ("\n", "l") or key.code == self.term.KEY_RIGHT:
            if self.stack.visible:
                new_cached_obj = self.stack.select()
            else:
                new_cached_obj = self.cached_obj.selected_cached_obj

            if new_cached_obj.obj is not None and not callable(new_cached_obj.obj):
                self.explorer_layout = ExplorerLayout(cached_obj=new_cached_obj)
                self.cached_obj = new_cached_obj
                self.cached_obj.cache_attributes()
                self.stack.append(
                    StackFrame(
                        cached_obj=self.cached_obj,
                        explorer_layout=self.explorer_layout,
                        overview_layout=self.overview_layout,
                    )
                )

        # Escape
        elif (key in ("\x1b", "h") or key.code == self.term.KEY_LEFT) and self.stack:
            self.stack.pop()
            self.cached_obj = self.stack[-1].cached_obj
            self.explorer_layout = self.stack[-1].explorer_layout
            self.overview_layout = self.stack[-1].overview_layout

        elif key == "g":
            self.explorer_layout.move_top()

        elif key == "G":
            self.explorer_layout.move_bottom(self.panel_height, self.cached_obj)

        # View ################################################################

        if key == "o" and self.stack.visible:
            self.stack.visible = False

        elif key == "o" and not self.stack.visible:
            self.stack.set_visible()

        # Switch between public and private attributes
        elif key in ("[", "]"):
            if self.explorer_layout.state == ExplorerState.public:
                self.explorer_layout.state = ExplorerState.private

            elif self.explorer_layout.state == ExplorerState.private:
                self.explorer_layout.state = ExplorerState.public

        elif key in ("{", "}"):
            if not callable(self.cached_obj.selected_cached_obj.obj):
                return

            if self.overview_layout.preview_state == PreviewState.repr:
                self.overview_layout.preview_state = PreviewState.source
            elif self.overview_layout.preview_state == PreviewState.source:
                self.overview_layout.preview_state = PreviewState.repr

        # Toggle docstring view
        elif key == "d":
            self.overview_layout.state = (
                OverviewState.docstring
                if self.overview_layout.state != OverviewState.docstring
                else OverviewState.all
            )

        # Toggle value view
        elif key == "p":
            self.overview_layout.state = (
                OverviewState.value
                if self.overview_layout.state != OverviewState.value
                else OverviewState.all
            )

        # Fullscreen
        elif key == "f":
            if self.overview_layout.state == OverviewState.docstring:
                printable = self.cached_obj.selected_cached_obj.docstring

            elif self.overview_layout.preview_state == PreviewState.repr:
                printable = self.cached_obj.selected_cached_obj.obj

            elif self.overview_layout.preview_state == PreviewState.source:
                printable = self.cached_obj.selected_cached_obj.get_source(
                    fullscreen=True
                )

            with self.console.capture() as capture:
                self.console.print(printable)

            str_out = capture.get()
            pydoc.pager(str_out)

        elif key == "H":
            help(self.cached_obj.selected_cached_obj.obj)

        # Other ################################################################

        # Return selected object
        elif key == "r":
            return self.cached_obj.selected_cached_obj.obj

        elif key == "b":
            breakpoint()
            pass

    def get_explorer_layout(self) -> Layout:
        if self.stack.visible:
            layout = Layout()
            layout.split_column(
                self.explorer_layout(self.cached_obj, term_width=self.term.width),
                self.stack(),
            )
            return layout
        else:
            return self.explorer_layout(self.cached_obj, term_width=self.term.width)

    def get_overview_layout(self) -> Layout:
        if self.help_layout.visible:
            return self.help_layout()
        else:
            return self.overview_layout(
                cached_obj=self.cached_obj.selected_cached_obj,
                term_height=self.term.height,
                console=self.console,
            )

    def draw(self, *args):
        """ Draw the application. the *args argument is due to resize events and are unused """
        print(self.term.home, end="")
        layout = Layout()

        layout.split_row(self.get_explorer_layout(), self.get_overview_layout())

        title = self.cached_obj.repr

        object_explorer = Panel(
            layout,
            title=title,
            subtitle=(
                "[red][u]q[/u]:quit[/red] "
                f"[cyan][u]?[/u]:{'exit ' if self.help_layout.visible else ''}help[/] "
                "[white][dim][u]o[/u]:toggle stack view[/dim]"
            ),
            subtitle_align="left",
            height=self.term.height - 1,
            style="blue",
        )
        rprint(object_explorer, end="")

    @property
    def panel_height(self) -> int:
        if self.stack.visible:
            return (self.term.height - 10) // 2
        else:
            return self.term.height - 6


def explore(obj: Any) -> Any:
    """ Run the explorer on the given object """
    return Explorer(obj).explore()
