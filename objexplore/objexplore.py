
import pydoc
from typing import Any, Optional

from blessed import Terminal
from rich.text import Text
from rich import print as rprint
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.layout import Layout
from rich.panel import Panel
from dataclasses import dataclass

from .cached_object import CachedObject
from .help_layout import HelpLayout, HelpState

console = Console()

highlighter = ReprHighlighter()

PUBLIC = "PUBLIC"
PRIVATE = "PRIVATE"
DOCSTRING = "DOCSTRING"
VALUE = "VALUE"
SOURCE = "SOURCE"
_term = Terminal()

version = "0.9.2"

# TODO methods filter
# or just a type filter?
# TODO fix pandas.IndexSlice / pandas.NA
# TODO for list/set/dict/tuple do length in info panel
# TODO show object stack as a panel


class ExplorerState:
    public, private = 0, 1


class ExplorerLayout(Layout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = ExplorerState.public
        # the highlighted/selected index attr
        self.public_index = 0
        self.private_index = 0
        # the top shown attribute if we are scrolled down
        self.public_window = 0
        self.private_window = 0

    def __call__(self, cached_obj: CachedObject) -> Layout:
        if self.state == ExplorerState.public:
            attribute_text = []
            for attr in cached_obj.plain_public_attributes[self.public_window:]:
                obj = getattr(cached_obj.obj, attr)
                if callable(obj) or obj is None:
                    style = "dim italic"
                else:
                    style = ""

                if attr == cached_obj.plain_public_attributes[self.public_index]:
                    style += " reverse"

                attribute_text.append(
                    Text(attr, overflow="elipses", style=style)
                )

            title = "[u]public[/u] [dim]private[/dim]"
            subtitle = f"[white]([/white][magenta]{self.public_index + 1}[/magenta][white]/[/white][magenta]{len(cached_obj.plain_public_attributes)}[/magenta][white])"

        elif self.state == ExplorerState.private:
            attribute_text = []
            for attr in cached_obj.plain_private_attributes[self.private_window:]:
                obj = getattr(cached_obj.obj, attr)
                if callable(obj) or obj is None:
                    style = "dim italic"
                else:
                    style = ""

                if attr == cached_obj.selected_private_attribute:
                    style += " reverse"

                attribute_text.append(
                    Text(attr, overflow="elipses", style=style)
                )

            title = "[dim]public[/dim] [underline]private[/underline]"
            subtitle = f"[white]([/white][magenta]{self.private_index + 1}[/magenta][white]/[/white][magenta]{len(cached_obj.plain_private_attributes)}[/magenta][white])"

        renderable_text = None
        for t in attribute_text:
            if not renderable_text:
                # Start with an empty text object, all following Text objects will steal the styles from this one
                renderable_text = Text("", overflow="elipses")
            renderable_text += t + '\n'

        panel = Panel(
            renderable_text,
            title=title,
            subtitle=subtitle,
            subtitle_align="right",
            style="white"
        )
        self.update(panel)
        return self

    def move_down(self, panel_height: int, cached_obj: CachedObject):
        """ Move the current selection down one """
        if self.state == ExplorerState.public:
            if self.public_index < len(cached_obj.plain_public_attributes) - 1:
                self.public_index += 1
                if self.public_index > self.public_window + panel_height:
                    self.public_window += 1

        elif self.state == ExplorerState.private:
            if self.private_index < len(cached_obj.plain_private_attributes) - 1:
                self.private_index += 1
                if self.private_index > self.private_window + panel_height:
                    self.private_window += 1

    def move_up(self):
        if self.attribute_type == PUBLIC:
            if self.public_attribute_index > 0:
                self.public_attribute_index -= 1
                if self.public_attribute_index < self.public_attribute_window:
                    self.public_attribute_window -= 1

        elif self.attribute_type == PRIVATE:
            if self.private_attribute_index > 0:
                self.private_attribute_index -= 1
                if self.private_attribute_index < self.private_attribute_window:
                    self.private_attribute_window -= 1

    def move_top(self):
        if self.attribute_type == PUBLIC:
            self.public_attribute_index = 0
            self.public_attribute_window = 0

        elif self.attribute_type == PRIVATE:
            self.private_attribute_index = 0
            self.private_attribute_window = 0

    def move_bottom(self, panel_height):
        if self.attribute_type == PUBLIC:
            self.public_attribute_index = len(self.plain_public_attributes) - 1
            self.public_attribute_window = max(0, self.public_attribute_index - panel_height)

        elif self.attribute_type == PRIVATE:
            self.private_attribute_index = len(self.plain_private_attributes) - 1
            self.private_attribute_window = max(0, self.private_attribute_index - panel_height)


@dataclass
class StackFrame:
    cached_obj: CachedObject
    explorer_layout: ExplorerLayout


class Explorer:
    """ Explorer class used to interactively explore Python Objects """

    def __init__(self, obj: Any):
        obj = CachedObject(obj, dotpath=repr(obj))
        # Figure out all the attributes of the current obj's attributes
        obj.cache_attributes()

        self.head_obj = obj
        self.current_obj = obj
        self.obj_stack = []
        self.term = _term
        self.main_view = None
        self.value_view = VALUE

        self.help_layout = HelpLayout(version, visible=False, ratio=3)
        self.explorer_layout = ExplorerLayout()

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
            self.explorer_layout.move_down(self.panel_height, self.current_obj)

        # move selected attribute up
        elif key == "k":
            self.explorer_layout.move_up(self.current_obj)

        elif key == "g":
            self.explorer_layout.move_top()

        elif key == "G":
            self.explorer_layout.move_bottom(self.panel_height)

        elif key == "H":
            help(self.current_obj.selected_cached_attribute.obj)

        # Toggle docstring view
        elif key == "d":
            self.main_view = DOCSTRING if self.main_view != DOCSTRING else None

        # Toggle value view
        elif key == "v":
            self.main_view = VALUE if self.main_view != VALUE else None

        # Fullscreen
        elif key == "f":
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

        # Return selected object
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
        return self.explorer_layout(self.current_obj)

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
            # TODO truncate if a huuge object like a dict of all emojis
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
