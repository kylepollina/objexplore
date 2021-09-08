
import pydoc
from blessed import Terminal
from rich.pretty import Pretty
from rich import print as rprint
from rich.text import Text
from rich.layout import Layout
from rich.repr import rich_repr
from rich.panel import Panel
from rich.console import Console
from rich.highlighter import ReprHighlighter
import cached_object

console = Console()

highlighter = ReprHighlighter()

PUBLIC = "PUBLIC"
PRIVATE = "PRIVATE"
DOCSTRING = "DOCSTRING"
VALUE = "VALUE"
_term = Terminal()

# TODO methods filter
# or just a type filter?
# Move to next type with {}


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

    @property
    def panel_height(self):
        return self.term.height - 8

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
                    continue

                if key == "?":
                    self.show_help = True

                # Switch between public and private attributes
                if key in ("[", "]"):
                    if self.current_obj.attribute_type == PUBLIC:
                        self.current_obj.attribute_type = PRIVATE

                    elif self.current_obj.attribute_type == PRIVATE:
                        self.current_obj.attribute_type = PUBLIC

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
                    else:
                        with console.capture() as capture:
                            console.print(self.current_obj.selected_cached_attribute.preview)
                        str_out = capture.get()
                        pydoc.pager(str_out)

                # Enter
                elif key in ["\n", "l"]:
                    if self.current_obj.attribute_type == PUBLIC:
                        new_cached_obj = self.current_obj[self.current_obj.selected_public_attribute]
                        if new_cached_obj.obj and not callable(new_cached_obj.obj):
                            self.obj_stack.append(self.current_obj)
                            self.current_obj = new_cached_obj
                            self.current_obj.cache_attributes()

                    elif self.current_obj.attribute_type == PRIVATE:
                        new_cached_obj = self.current_obj[self.current_obj.selected_private_attribute]
                        if new_cached_obj.obj and not callable(new_cached_obj.obj):
                            self.obj_stack.append(self.current_obj)
                            self.current_obj = new_cached_obj
                            self.current_obj.cache_attributes()

                # Escape
                elif key in ["\x1b", "h"] and self.obj_stack:
                    self.current_obj = self.obj_stack.pop()

                elif key == "b":
                    breakpoint()

    def draw(self):
        print(self.term.home, end="")
        layout = Layout()

        layout.split_row(
            Layout(name="explorer"),
            Layout(name="preview")
        )
        layout["preview"].ratio = 3
        current_obj_attributes = self.current_obj.get_current_obj_attr_panel()
        layout["explorer"].update(current_obj_attributes)
        if self.main_view == DOCSTRING:
            layout["preview"].update(self.get_docstring_panel(fullscreen=True))

        elif self.main_view == VALUE:
            layout["preview"].update(self.get_value_panel())

        elif self.show_help:
            layout["preview"].update(self.get_help_panel())

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
            subtitle=f"[red]q:quit[/red] [cyan]?:{'exit ' if self.show_help else ''}help[/]",
            subtitle_align="left",
            height=self.term.height - 1,
            style="blue"
        )
        rprint(object_explorer, end='')

    def get_docstring_panel(self, fullscreen=False):
        return Panel(
            self.current_obj.selected_cached_attribute.docstring,
            title="[underline]docstring",
            title_align="left",
            subtitle=f"[dim]{'f:fullscreen ' if fullscreen else ''}d:toggle",
            subtitle_align="right",
            style="white"
        )

    def get_value_panel(self):
        return Panel(
            self.current_obj.selected_cached_attribute.preview,
            title="[u]value",
            title_align="left",
            subtitle="[dim]f:fullscreen v:toggle",
            subtitle_align="right",
            style="white"
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
                title="[u]help",
                title_align="left",
                subtitle="[dim white]f:fullscreen ?exit help",
                subtitle_align="right",
                style="magenta"
            )

    @property
    def help_text(self):
        return "[magenta]This is the help page"

def ox(obj):
    explorer = Explorer(obj)
    explorer.explore()


if __name__ == "__main__":
    from importlib import reload
    reload(cached_object)
    ex = Explorer("hello")
    ox(ex)
