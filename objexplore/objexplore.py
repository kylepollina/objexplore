
import pydoc
import signal
from typing import Any, Optional, List

from blessed import Terminal
from rich import print as rprint
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.layout import Layout
from rich.panel import Panel
from dataclasses import dataclass

from .cached_object import CachedObject
from .explorer_layout import ExplorerLayout, ExplorerState
from .help_layout import HelpLayout, HelpState
from .preview_layout import PreviewLayout, PreviewState, ValueState

console = Console()

highlighter = ReprHighlighter()

_term = Terminal()

version = "0.9.2"

# TODO methods filter
# or just a type filter?
# TODO fix pandas.IndexSlice / pandas.NA
# TODO for list/set/dict/tuple do length in info panel
# TODO show object stack as a panel
# TODO q to close help menu?




@dataclass
class StackFrame:
    cached_obj: CachedObject
    explorer_layout: ExplorerLayout
    preview_layout: PreviewLayout


class Explorer:
    """ Explorer class used to interactively explore Python Objects """

    def __init__(self, obj: Any):
        cached_obj = CachedObject(obj, dotpath=repr(obj))
        # Figure out all the attributes of the current obj's attributes
        cached_obj.cache_attributes()

        # self.head_obj = cached_obj
        self.cached_obj = cached_obj
        self.stack: List[StackFrame] = []
        self.term = _term
        self.main_view = None

        self.help_layout = HelpLayout(version, visible=False, ratio=3)
        self.explorer_layout = ExplorerLayout(cached_obj=cached_obj)
        self.preview_layout = PreviewLayout()

        # Run self.draw() whenever the win change signal is caught
        signal.signal(signal.SIGWINCH, self.draw)

    def explore(self) -> Optional[Any]:
        """ Open the interactive explorer """

        key = None

        # Clear the screen
        print(self.term.clear, end='')

        with self.term.cbreak(), self.term.hidden_cursor():
            while key not in ('q', 'Q'):
                self.draw()
                key = self.term.inkey()
                res = self.process_key_event(key)

                # If the object is returned as a response the close the explorer and return the selected object
                if res:
                    return res

    def process_key_event(self, key: str) -> Optional[Any]:
        """ Process the incoming key """

        # Help page ###########################################################
        if self.help_layout.visible:
            # Close help page
            if key in ["?", "\x1b"]:
                self.help_layout.visible = False

            # Fullscreen
            elif key == "f":
                with console.capture() as capture:
                    console.print(self.help_text)
                str_out = capture.get()
                pydoc.pager(str_out)

            # Switch panes
            elif key in ["{", "}", "[", "]"]:
                if self.help_layout.state == HelpState.keybindings:
                    self.help_layout.state = HelpState.about
                elif self.help_layout.state == HelpState.about:
                    self.help_layout.state = HelpState.keybindings

            else:
                self.help_layout.visible = False

            return

        if self.help_layout.visible is False and key == "?":
            self.help_layout.visible = True
            return
        #######################################################################

        # Switch between public and private attributes
        if key in ("[", "]"):
            if self.explorer_layout.state == ExplorerState.public:
                self.explorer_layout.state = ExplorerState.private

            elif self.explorer_layout.state == ExplorerState.private:
                self.explorer_layout.state = ExplorerState.public

        elif key in ["{", "}"]:
            if not callable(self.cached_obj.selected_cached_obj.obj):
                return

            if self.preview_layout.value_state == ValueState.repr:
                self.preview_layout.value_state = ValueState.source
            elif self.preview_layout.value_state == ValueState.source:
                self.preview_layout.value_state = ValueState.repr

        # move selected attribute down
        elif key == "j":
            self.explorer_layout.move_down(self.panel_height, self.cached_obj)

        # move selected attribute up
        elif key == "k":
            self.explorer_layout.move_up()

        elif key == "g":
            self.explorer_layout.move_top()

        elif key == "G":
            self.explorer_layout.move_bottom(self.panel_height, self.cached_obj)

        elif key == "H":
            help(self.cached_obj.selected_cached_obj.obj)

        # Toggle docstring view
        elif key == "d":
            self.preview_layout.state = PreviewState.docstring if self.preview_layout.state != PreviewState.docstring else PreviewState.all

        # Toggle value view
        elif key == "v":
            self.preview_layout.state = PreviewState.value if self.preview_layout.state != PreviewState.value else PreviewState.all

        # Fullscreen
        elif key == "f":
            if self.main_view == PreviewState.docstring:
                with console.capture() as capture:
                    console.print(self.cached_obj.selected_cached_obj.docstring)
                str_out = capture.get()
                pydoc.pager(str_out)
            elif self.main_view == PreviewState.value or self.main_view is None:
                with console.capture() as capture:
                    console.print(self.value_panel_text(fullscreen=True))
                str_out = capture.get()
                pydoc.pager(str_out)

        # Return selected object
        elif key == "r":
            return self.cached_obj.selected_cached_obj.obj

        # Enter
        elif key in ["\n", "l"]:
            new_cached_obj = self.cached_obj.selected_cached_obj
            if new_cached_obj.obj is not None and not callable(new_cached_obj.obj):
                self.stack.append(
                    StackFrame(
                        cached_obj=self.cached_obj,
                        explorer_layout=self.explorer_layout,
                        preview_layout=self.preview_layout
                    )
                )
                self.explorer_layout = ExplorerLayout(cached_obj=new_cached_obj)
                self.cached_obj = new_cached_obj
                self.cached_obj.cache_attributes()

        # Escape
        elif key in ["\x1b", "h"] and self.stack:
            frame: StackFrame = self.stack.pop()
            self.cached_obj = frame.cached_obj
            self.explorer_layout = frame.explorer_layout
            self.preview_layout = frame.preview_layout

        elif key == "b":
            breakpoint()
            pass

    def get_explorer_layout(self) -> Layout:
        return self.explorer_layout(self.cached_obj, term_width=self.term.width)

    def get_preview_layout(self) -> Layout:
        if self.help_layout.visible:
            return self.help_layout()
        else:
            return self.preview_layout(
                cached_obj=self.cached_obj.selected_cached_obj,
                term_height=self.term.height
            )

    def draw(self, *args):
        print(self.term.home, end="")
        layout = Layout()

        layout.split_row(
            self.get_explorer_layout(),
            self.get_preview_layout()
        )

        object_explorer = Panel(
            layout,
            # TODO truncate if a huuge object like a dict of all emojis
            title=highlighter(f"{self.cached_obj.obj!r}"),
            subtitle=f"[red][u]q[/u]:quit[/red] [cyan][u]?[/u]:{'exit ' if self.help_layout.visible else ''}help[/]",
            subtitle_align="left",
            height=self.term.height - 1,
            style="blue"
        )
        rprint(object_explorer, end='')

    @property
    def panel_height(self):
        return self.term.height - 8


def explore(obj):
    """ Run the explorer on the given object """
    return Explorer(obj).explore()
