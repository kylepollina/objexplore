
from typing import Any
import pydoc

from blessed import Terminal
from rich import print as rprint
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.layout import Layout
from rich.panel import Panel

from . import cached_object
from .help_layout import HelpLayout, HelpState

console = Console()

highlighter = ReprHighlighter()

PUBLIC = "PUBLIC"
PRIVATE = "PRIVATE"
DOCSTRING = "DOCSTRING"
VALUE = "VALUE"
SOURCE = "SOURCE"
KEYBINDINGS = "KEYBINDINGS"
ABOUT = "ABOUT"
_term = Terminal()

version = "0.9.2"

# TODO methods filter
# or just a type filter?
# TODO fix pandas.IndexSlice / pandas.NA
# TODO for list/set/dict/tuple do length in info panel
# TODO show object stack as a panel


class Explorer:
    """ Explorer class used to interactively explore Python Objects """

    def __init__(self, obj: Any):
        obj = cached_object.CachedObject(obj, dotpath=repr(obj))
        # Figure out all the attributes of the current obj's attributes
        obj.cache_attributes()

        self.head_obj = obj
        self.current_obj = obj
        self.obj_stack = []
        self.term = _term
        self.main_view = None
        self.help_page = KEYBINDINGS
        self.value_view = VALUE

        self.help_layout = HelpLayout(version, visible=False, ratio=3)

    def explore(self):
        """ Open the interactive explorer """

        key = None

        # Clear the screen
        print(self.term.clear, end='')

        with self.term.cbreak(), self.term.hidden_cursor():
            while key not in ('q', 'Q'):
                self.draw()
                key = self.term.inkey()
                self.process_key_event(key)

    def process_key_event(self, key: str):

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
            elif key in ["{", "}"]:
                if self.help_layout.state == HelpState.keybindings:
                    self.help_layout.state = HelpState.about
                elif self.help_layout.state == HelpState.about:
                    self.help_layout.state = HelpState.keybindings

            return

        if self.help_layout.visible is False and key == "?":
            self.help_layout.visible = True
            return
        #######################################################################

        # Switch between public and private attributes
        if key in ("[", "]"):
            if self.current_obj.attribute_type == PUBLIC:
                self.current_obj.attribute_type = PRIVATE

            elif self.current_obj.attribute_type == PRIVATE:
                self.current_obj.attribute_type = PUBLIC

        elif key in ["{", "}"]:
            if not callable(self.current_obj.selected_cached_attribute.obj):
                return

            if self.value_view == VALUE:
                self.value_view = SOURCE
            elif self.value_view == SOURCE:
                self.value_view = VALUE

        # move selected attribute down
        elif key == "j":
            self.current_obj.move_down(self.panel_height)

        # move selected attribute up
        elif key == "k":
            self.current_obj.move_up()

        elif key == "g":
            self.current_obj.move_top()

        elif key == "G":
            self.current_obj.move_bottom(self.panel_height)

        elif key == "H":
            help(self.current_obj.selected_cached_attribute.obj)

        elif key == "d":
            # Toggle docstring view
            self.main_view = DOCSTRING if self.main_view != DOCSTRING else None

        elif key == "v":
            # Toggle value view
            self.main_view = VALUE if self.main_view != VALUE else None

        elif key == "f":
            # Fullscreen
            if self.main_view == DOCSTRING:
                with console.capture() as capture:
                    console.print(self.current_obj.selected_cached_attribute.docstring)
                str_out = capture.get()
                pydoc.pager(str_out)
            elif self.main_view == VALUE or self.main_view is None:
                with console.capture() as capture:
                    console.print(self.value_panel_text(fullscreen=True))
                str_out = capture.get()
                pydoc.pager(str_out)

        elif key == "r":
            return self.current_obj.selected_cached_attribute.obj

        # Enter
        elif key in ["\n", "l"]:
            if self.current_obj.attribute_type == PUBLIC:
                new_cached_obj = self.current_obj[self.current_obj.selected_public_attribute]
                if new_cached_obj.obj is not None and not callable(new_cached_obj.obj):
                    self.obj_stack.append(self.current_obj)
                    self.current_obj = new_cached_obj
                    self.current_obj.cache_attributes()

            elif self.current_obj.attribute_type == PRIVATE:
                new_cached_obj = self.current_obj[self.current_obj.selected_private_attribute]
                if new_cached_obj.obj is not None and not callable(new_cached_obj.obj):
                    self.obj_stack.append(self.current_obj)
                    self.current_obj = new_cached_obj
                    self.current_obj.cache_attributes()

        # Escape
        elif key in ["\x1b", "h"] and self.obj_stack:
            self.current_obj = self.obj_stack.pop()

        elif key == "b":
            breakpoint()
            pass

    def get_explorer_layout(self) -> Layout:
        current_obj_attributes = self.current_obj.get_current_obj_attr_panel()
        return Layout(current_obj_attributes)

    def get_preview_layout(self) -> Layout:
        if self.help_layout.visible:
            return self.help_layout()

        elif self.main_view == DOCSTRING:
            return Layout(self.get_docstring_panel(fullscreen=True), ratio=3)

        elif self.main_view == VALUE:
            return Layout(self.get_value_panel(), ratio=3)

        else:
            layout = Layout(ratio=3)
            layout.split_column(
                Layout(
                    self.get_value_panel(),
                    name="obj_value"
                ),
                Layout(
                    self.get_type_panel(),
                    name="obj_type",
                    size=3
                ),
                Layout(
                    self.get_docstring_panel(),
                    name="obj_doc",
                    size=15
                )
            )
            return layout

    def draw(self):
        print(self.term.home, end="")
        layout = Layout()

        layout.split_row(
            self.get_explorer_layout(),
            self.get_preview_layout()
        )

        object_explorer = Panel(
            layout,
            title=highlighter(f"{self.current_obj.obj!r}"),
            subtitle=f"[red][u]q[/u]:quit[/red] [cyan][u]?[/u]:{'exit ' if self.help_layout.visible else ''}help[/]",
            subtitle_align="left",
            height=self.term.height - 1,
            style="blue"
        )
        rprint(object_explorer, end='')

    @property
    def panel_height(self):
        return self.term.height - 8

    def get_docstring_panel(self, fullscreen=False):
        return Panel(
            self.current_obj.selected_cached_attribute.get_docstring(self.term, fullscreen),
            title="[underline]docstring",
            title_align="left",
            subtitle=f"[dim]{'[u]f[/u]:fullscreen ' if fullscreen else ''}[u]d[/u]:toggle",
            subtitle_align="left",
            style="white"
        )

    def get_value_panel(self):
        return Panel(
            self.value_panel_text(),
            title=(
                "[u]value[/u]"
                if not self.current_obj.selected_cached_attribute or not callable(self.current_obj.selected_cached_attribute.obj)
                else (
                    "[u]value[/u] [dim]source[/dim]"
                    if self.value_view != SOURCE
                    else "[dim]value[/dim] [u]source[/u]"
                )
            ),
            title_align="left",
            subtitle=f"[dim][u]f[/u]:fullscreen [u]v[/u]:toggle{' [u]{}[/u]:switch pane' if self.current_obj.selected_cached_attribute and callable(self.current_obj.selected_cached_attribute.obj) else ''}",
            subtitle_align="left",
            style="white"
        )

    def value_panel_text(self, fullscreen=False):
        # sometimes the current obj will have no public/private attributes in which selected_cached_attribute
        # will be `None`
        if self.current_obj.selected_cached_attribute:
            return (
                self.current_obj.selected_cached_attribute.get_preview(self.term, fullscreen)
                if not callable(self.current_obj.selected_cached_attribute.obj)
                else (
                    self.current_obj.selected_cached_attribute.get_preview(self.term, fullscreen)
                    if self.value_view == VALUE
                    else self.current_obj.selected_cached_attribute.get_source(self.term, fullscreen)
                )
            )
        # if that is the case then return an empty string
        else:
            return ""

    def get_type_panel(self):
        return Panel(
            self.current_obj.selected_cached_attribute.typeof,
            title="[u]type",
            title_align="left",
            style="white"
        )


def explore(obj):
    """ Run the explorer on the given object """
    return Explorer(obj).explore()
