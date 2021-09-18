import pydoc
import signal
from typing import Any, Optional, Union

import blessed
from blessed import Terminal
from rich import print as rprint
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.syntax import Syntax

from .utils import is_selectable
from .cached_object import CachedObject
from .explorer_layout import ExplorerLayout, ExplorerState
from .help_layout import HelpLayout, HelpState, random_error_quote
from .overview_layout import OverviewLayout, OverviewState, PreviewState
from .stack_layout import StackFrame, StackLayout

version = "1.2"

# TODO fix explore(namedtuple)
# TODO methods filter
# or just a type filter?
# TODO empty overview layouts for when there are 0 public attributes
# TODO search filter
# TODO generate the explorer lines on cachedobject instatiation to speed up processing
#    - Auto generate ALL renderables on init. docstring, repr (i think already done) type, len, source, etc
# TODO use inspect.ismethod inspect.ismodule, inspect.isfunction isclass
# TODO 'i' to fullscreen print rich.inspect

console = Console()


class Explorer:
    """ Explorer class used to interactively explore Python Objects """

    def __init__(self, obj: Any):
        cached_obj = CachedObject(obj, dotpath=repr(obj))
        # Figure out all the attributes of the current obj's attributes
        cached_obj.cache_attributes()

        # self.head_obj = cached_obj
        self.cached_obj: CachedObject = cached_obj
        self.term = Terminal()
        self.stack = StackLayout(head_obj=self.cached_obj, visible=False)
        self.help_layout = HelpLayout(version, visible=False, ratio=3)
        self.explorer_layout = ExplorerLayout(cached_obj=cached_obj)
        self.overview_layout = OverviewLayout(ratio=3)

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
                try:
                    self.draw()
                    key = self.term.inkey()
                    res = self.process_key_event(key)

                    # If the object is returned as a response then close the explorer and return the selected object
                    if res:
                        break

                except RuntimeError as err:
                    # Some kind of error during resizing events. Ignore and continue
                    if (
                        err.args[0]
                        == "reentrant call inside <_io.BufferedWriter name='<stdout>'>"
                    ):
                        pass
                    # Otherwise it is a new error. Raise
                    else:
                        raise err
        return res

    def process_key_event(self, key: blessed.keyboard.Keystroke) -> Any:
        """ Process the incoming key """

        if key == "b":
            breakpoint()
            pass

        # Help page ###########################################################

        if self.help_layout.visible:
            # Close help page
            if key == "?" or key.code == self.term.KEY_ESCAPE:
                self.help_layout.visible = False
                return

            # Fullscreen
            elif key == "f":
                with console.capture() as capture:
                    console.print(self.help_layout.text)
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

        # if the stack view is open, only accept inputs to move around/close thes tack view
        if self.stack.visible and (
            key not in ("o", "j", "k", "\n")
            and key.code
            not in (self.term.KEY_UP, self.term.KEY_DOWN, self.term.KEY_RIGHT)
        ):
            return

        elif key == "k" or key.code == self.term.KEY_UP:
            if self.stack.visible:
                self.stack.move_up()
            else:
                self.explorer_layout.move_up()

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

            # if new_cached_obj.obj not in (None, [], {}, (), set()) and not callable(
            #     new_cached_obj.obj
            # ):
            if is_selectable(new_cached_obj):
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
            printable: Union[str, Syntax]

            if self.overview_layout.state == OverviewState.docstring:
                printable = self.cached_obj.selected_cached_obj.docstring

            elif self.overview_layout.preview_state == PreviewState.repr:
                printable = self.cached_obj.selected_cached_obj.obj

            elif self.overview_layout.preview_state == PreviewState.source:
                printable = self.cached_obj.selected_cached_obj.get_source(
                    fullscreen=True
                )

            with console.capture() as capture:
                console.print(printable)

            str_out = capture.get()
            pydoc.pager(str_out)

        elif key == "H":
            help(self.cached_obj.selected_cached_obj.obj)

        # Other ################################################################

        # Return selected object
        elif key == "r":
            return self.cached_obj.selected_cached_obj.obj

    def get_explorer_layout(self) -> Layout:
        if self.stack.visible:
            layout = Layout()
            layout.split_column(
                self.explorer_layout(
                    term_width=self.term.width, term_height=self.term.height
                ),
                self.stack(term_width=self.term.width),
            )
            return layout
        else:
            return self.explorer_layout(
                term_width=self.term.width, term_height=self.term.height
            )

    def get_overview_layout(self) -> Layout:
        if self.help_layout.visible:
            return self.help_layout()
        else:
            return self.overview_layout(
                cached_obj=self.cached_obj.selected_cached_obj,
                term_height=self.term.height,
                console=console,
            )

    def draw(self, *args):
        """ Draw the application. the *args argument is due to resize events and are unused """
        print(self.term.home, end="")
        layout = Layout()

        layout.split_row(self.get_explorer_layout(), self.get_overview_layout())

        title = self.cached_obj.title

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
        # TODO this shouldn't be here
        if self.stack.visible:
            return (self.term.height - 10) // 2
        else:
            return self.term.height - 6


def explore(obj: Any) -> Any:
    """ Run the explorer on the given object """
    try:
        e = Explorer(obj)
        return e.explore()
    except Exception as e:
        console.print_exception(show_locals=True)
        print()
        rprint(f"[red]{random_error_quote()}")
        formatted_link = f"https://github.com/kylepollina/objexplore/issues/new?assignees=&labels=&template=bug_report.md&title={e}".replace(
            " ", "+"
        )
        print("Please report the issue here:")
        rprint(f"   [link={formatted_link}][u]{formatted_link}[/u][/link]")
        rprint(
            "[yellow italic]Make sure to copy/paste the above traceback to the issue to make the issue quicker to solve!"
        )
