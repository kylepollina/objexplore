
import asyncio
import pydoc
from random import choice
from textwrap import dedent

from blessed import Terminal
from rich import print as rprint
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.layout import Layout
from rich.panel import Panel

from . import cached_object

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


class Explorer:
    def __init__(self, obj):
        obj = cached_object.CachedObject(obj)
        # Figure out all the attributes of the current obj's attributes
        obj.cache_attributes()
        self.head_obj = obj
        self.current_obj = obj
        self.obj_stack = []
        self.term = _term
        self.main_view = None
        self.show_help = False
        self.help_page = KEYBINDINGS
        self.value_view = VALUE

    def explore(self):
        key = None
        print(self.term.clear, end='')

        with self.term.cbreak(), self.term.hidden_cursor():
            while key not in ('q', 'Q'):
                self.draw()
                key = self.term.inkey()

                if self.show_help:
                    if key in ["?", "\x1b"]:
                        self.show_help = False
                    elif key == "f":
                        with console.capture() as capture:
                            console.print(self.help_text)
                        str_out = capture.get()
                        pydoc.pager(str_out)
                    elif key in ["{", "}"]:
                        if self.help_page == KEYBINDINGS:
                            self.help_page = ABOUT
                        elif self.help_page == ABOUT:
                            self.help_page = KEYBINDINGS
                    continue

                if key == "?":
                    self.show_help = True

                # Switch between public and private attributes
                if key in ("[", "]"):
                    if self.current_obj.attribute_type == PUBLIC:
                        self.current_obj.attribute_type = PRIVATE

                    elif self.current_obj.attribute_type == PRIVATE:
                        self.current_obj.attribute_type = PUBLIC

                elif key in ["{", "}"]:
                    if not callable(self.current_obj.selected_cached_attribute.obj):
                        continue

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

                elif key == "p":
                    rprint(self.current_obj.selected_cached_attribute.fullname)
                    rprint(self.current_obj.selected_cached_attribute.obj)
                    break

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

    def draw(self):
        print(self.term.home, end="")
        layout = Layout()

        layout.split_row(
            Layout(name="explorer"),
            Layout(name="preview", ratio=3)
        )
        current_obj_attributes = self.current_obj.get_current_obj_attr_panel()
        layout["explorer"].update(current_obj_attributes)

        if self.show_help:
            layout["preview"].update(self.get_help_panel())

        elif self.main_view == DOCSTRING:
            layout["preview"].update(self.get_docstring_panel(fullscreen=True))

        elif self.main_view == VALUE:
            layout["preview"].update(self.get_value_panel())

        else:
            layout["preview"].split_column(
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

        object_explorer = Panel(
            layout,
            title=highlighter(f"{self.current_obj.obj!r}"),
            subtitle=f"[red][u]q[/u]:quit[/red] [cyan][u]?[/u]:{'exit ' if self.show_help else ''}help[/]",
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
                if not callable(self.current_obj.selected_cached_attribute.obj)
                else (
                    "[u]value[/u] [dim]source[/dim]"
                    if self.value_view != SOURCE
                    else "[dim]value[/dim] [u]source[/u]"
                )
            ),
            title_align="left",
            subtitle=f"[dim][u]f[/u]:fullscreen [u]v[/u]:toggle{' [u]{}[/u]:switch pane' if callable(self.current_obj.selected_cached_attribute.obj) else ''}",
            subtitle_align="left",
            style="white"
        )

    def value_panel_text(self, fullscreen=False):
        return (
            self.current_obj.selected_cached_attribute.preview
            if not callable(self.current_obj.selected_cached_attribute.obj)
            else (
                self.current_obj.selected_cached_attribute.preview
                if self.value_view == VALUE
                else self.current_obj.selected_cached_attribute.get_source(self.term, fullscreen)
            )
        )

    def get_type_panel(self):
        return Panel(
            self.current_obj.selected_cached_attribute.typeof,
            title="[u]type",
            title_align="left",
            style="white"
        )

    def get_help_panel(self):
        return Panel(
            self.help_text,
            title=(
                "help | [u]key bindings[/u] [dim]about"
                if self.help_page == KEYBINDINGS
                else "help | [dim]key bindings[/dim] [u]about"
            ),
            title_align="left",
            subtitle="[dim white][u]f[/u]:fullscreen [u]{}[/u]:switch pane [u]?[/u]:exit help",
            subtitle_align="left",
            style="magenta"
        )

    @property
    def help_text(self):
        """ Return the text to be displayed on the help page """
        if self.help_page == KEYBINDINGS:
            return dedent(
                """
                [white]
                      k - [cyan]up[/cyan]
                      j - [cyan]down[/cyan]
                      g - [cyan]go to top[/cyan]
                      G - [cyan]go to bottom[/cyan]
                l Enter - [cyan]explore selected attribute[/cyan]
                  h Esc - [cyan]go back to parent object[/cyan]
                    [ ] - [cyan]switch attribute type (public/private)[/cyan]
                    { } - [cyan]switch pane[/cyan]
                      v - [cyan]toggle full preview[/cyan]
                      d - [cyan]toggle full docstring[/cyan]
                      f - [cyan]open fullscreen view[/cyan]
                      H - [cyan]open help page on selected attribute[/cyan]
                      p - [cyan]exit and print value of selected attribute[/cyan]
                      ? - [cyan]toggle help page[/cyan]
                    q Q - [cyan]quit[/cyan]
                """
            ).strip()
        elif self.help_page == ABOUT:
            return dedent(
                f"""
                [white]
                [u]Objexplore[/u] Interactive Python Object Explorer
                Author: [cyan]Kyle Pollina[/cyan]
                Version: [cyan]{version}[/cyan]
                PyPI: [cyan]https://pypi.org/project/objexplore[/cyan]
                Source: [cyan]https://github.com/kylepollina/objexplore[/cyan]
                [yellow italic]Report an issue[/yellow italic]: [cyan]https://github.com/kylepollina/objexplore/issues[/cyan]

                """ + self.random_quote()
            ).strip()

    def random_quote(self):
        return choice(
            [
                "[i]Have a nice day!![/i]",
                "[i]You look rather dashing today![/i]",
                "[i]:)[/i]",
                "[i]:earth_africa:[/i]",
                "[i]<3[/i]",
            ]
        )


def explore(obj):
    """ Run the explorer on the given object """
    Explorer(obj).explore()
