
import pydoc
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


class PreviewState:
    all, docstring, value, source = range(4)


class PreviewLayout(Layout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = PreviewState.all

    def __call__(self, cached_obj, term_height: int) -> Layout:
        if self.state == PreviewState.docstring:
            return Layout(
                self.get_docstring_panel(
                    cached_obj=cached_obj,
                    term_height=term_height,
                    fullscreen=True
                ),
                ratio=3
            )

        elif self.state == PreviewState.value:
            return Layout(self.get_value_panel(cached_obj), ratio=3)

        else:
            layout = Layout(ratio=3)
            layout.split_column(
                Layout(
                    self.get_value_panel(cached_obj),
                    name="obj_value"
                ),
                Layout(
                    self.get_type_panel(cached_obj),
                    name="obj_type",
                    size=3
                ),
                Layout(
                    self.get_docstring_panel(cached_obj),
                    name="obj_doc",
                    size=15
                )
            )
            return layout

    def get_value_panel(self, cached_obj: CachedObject):
        return Panel("value")

    def get_type_panel(self, cached_obj: CachedObject) -> Panel:
        return Panel("type")

    def get_docstring_panel(self, cached_obj: CachedObject, term_height: Optional[int] = None, fullscreen: bool = False) -> Panel:
        """ Build the docstring panel """
        title="[underline]docstring"
        docstring = '\n'.join(cached_obj.docstring.splitlines()[:term_height])
        if fullscreen:
            return Panel(
                docstring,
                title=title,
                subtitle="[dim][u]f[/u]:fullscreen [u]d[/u]:toggle",
                subtitle_align="left",
                style="white",
            )
        else:
            # Only need to show the lines of the docstring that would be visible by
            # the terminal
            return Panel(
                docstring,
                title=title,
                subtitle="[dim][u]d[/u]:toggle",
                subtitle_align="left",
                style="white"
            )


@dataclass
class StackFrame:
    cached_obj: CachedObject
    explorer_layout: ExplorerLayout
    preview_layout: PreviewLayout


class Explorer:
    """ Explorer class used to interactively explore Python Objects """

    def __init__(self, obj: Any):
        obj = CachedObject(obj, dotpath=repr(obj))
        # Figure out all the attributes of the current obj's attributes
        obj.cache_attributes()

        self.head_obj = obj
        self.cached_obj = obj
        self.stack: List[StackFrame] = []
        self.term = _term
        self.main_view = None

        self.help_layout = HelpLayout(version, visible=False, ratio=3)
        self.explorer_layout = ExplorerLayout()
        self.preview_layout = PreviewLayout()

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
            if not callable(self.cached_obj.selected_cached_attribute.obj):
                return

            if self.preview_layout.state == PreviewState.value:
                self.preview_layout.state = PreviewState.source
            elif self.preview_layout.state == PreviewState.source:
                self.preview_layout.state = PreviewState.value

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
            help(self.cached_obj.selected_cached_attribute.obj)

        # Toggle docstring view
        elif key == "d":
            self.main_view = PreviewState.docstring if self.main_view != PreviewState.docstring else None

        # Toggle value view
        elif key == "v":
            self.main_view = PreviewState.value if self.main_view != PreviewState.value else None

        # Fullscreen
        elif key == "f":
            if self.main_view == PreviewState.docstring:
                with console.capture() as capture:
                    console.print(self.cached_obj.selected_cached_attribute.docstring)
                str_out = capture.get()
                pydoc.pager(str_out)
            elif self.main_view == PreviewState.value or self.main_view is None:
                with console.capture() as capture:
                    console.print(self.value_panel_text(fullscreen=True))
                str_out = capture.get()
                pydoc.pager(str_out)

        # Return selected object
        elif key == "r":
            return self.cached_obj.selected_cached_attribute.obj

        # Enter
        elif key in ["\n", "l"]:
            new_cached_obj = self.explorer_layout.get_selected_cached_obj(self.cached_obj)
            if new_cached_obj.obj is not None and not callable(new_cached_obj.obj):
                self.stack.append(
                    StackFrame(
                        cached_obj=self.cached_obj,
                        explorer_layout=self.explorer_layout,
                        preview_layout=self.preview_layout
                    )
                )
                self.explorer_layout = ExplorerLayout()
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
        return self.explorer_layout(self.cached_obj)

    def get_preview_layout(self) -> Layout:
        if self.help_layout.visible:
            return self.help_layout()
        else:
            return self.preview_layout(
                cached_obj=self.cached_obj,
                term_height=self.term.height
            )

    def draw(self):
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

    def get_value_panel(self):
        return Panel(
            self.value_panel_text(),
            title=(
                "[u]value[/u]"
                if not self.cached_obj.selected_cached_attribute or not callable(self.cached_obj.selected_cached_attribute.obj)
                else (
                    "[u]value[/u] [dim]source[/dim]"
                    if self.preview_layout.state != PreviewState.source
                    else "[dim]value[/dim] [u]source[/u]"
                )
            ),
            title_align="left",
            subtitle=f"[dim][u]f[/u]:fullscreen [u]v[/u]:toggle{' [u]{}[/u]:switch pane' if self.cached_obj.selected_cached_attribute and callable(self.cached_obj.selected_cached_attribute.obj) else ''}",
            subtitle_align="left",
            style="white"
        )

    def value_panel_text(self, fullscreen=False):
        # sometimes the current obj will have no public/private attributes in which selected_cached_attribute
        # will be `None`
        if self.cached_obj.selected_cached_attribute:
            return (
                self.cached_obj.selected_cached_attribute.get_preview(self.term, fullscreen)
                if not callable(self.cached_obj.selected_cached_attribute.obj)
                else (
                    self.cached_obj.selected_cached_attribute.get_preview(self.term, fullscreen)
                    if self.preview_layout.state == PreviewState.value
                    else self.cached_obj.selected_cached_attribute.get_source(self.term, fullscreen)
                )
            )
        # if that is the case then return an empty string
        else:
            return ""

    def get_type_panel(self):
        return Panel(
            self.cached_obj.selected_cached_attribute.typeof,
            title="[u]type",
            title_align="left",
            style="white"
        )


def explore(obj):
    """ Run the explorer on the given object """
    return Explorer(obj).explore()
