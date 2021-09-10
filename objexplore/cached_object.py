
from typing import Optional, Dict, Any
import inspect
from rich.syntax import Syntax
from rich.text import Text
from rich.panel import Panel
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.pretty import Pretty

highlighter = ReprHighlighter()


PUBLIC = "PUBLIC"
PRIVATE = "PRIVATE"

# TODO should contain functions to get type/docstring/source of selected attribute

console = Console()

# TODO fix bug if there is no public/private attributes


class CachedObject:

    def __init__(
        self,
        obj,
        dotpath,
    ):
        self.obj: Any = obj
        self.dotpath: str = dotpath
        self.attribute_type = PUBLIC
        self.public_attribute_index = 0
        self.private_attribute_index = 0
        self.public_attribute_window = 0
        self.private_attribute_window = 0

        self.plain_attrs = dir(self.obj)

        if '__weakref__' in self.plain_attrs:
            # Ignore weakrefs
            self.plain_attrs.remove('__weakref__')

        self.plain_public_attributes = sorted(
            attr for attr in self.plain_attrs if not attr.startswith('_')
        )
        self.plain_private_attributes = sorted(
            attr for attr in self.plain_attrs if attr.startswith('_')
        )

        # Key:val pair of attribute name and the cached object associated with it
        self.cached_attributes: Dict[str, CachedObject] = {}

        self.typeof: Text = highlighter(str(type(self.obj)))
        self.docstring: str = inspect.getdoc(self.obj) or "[magenta italic]None"

        try:
            self._source = inspect.getsource(self.obj)
        except Exception:
            self._source = None

    def cache_attributes(self):
        """ Create a CachedObject for each attribute of the self.obj """
        if not self.cached_attributes:
            for attr in self.plain_attrs:
                self.cached_attributes[attr] = CachedObject(
                    getattr(self.obj, attr),
                    dotpath=f'{self.dotpath}.{attr}'
                )

    def get_preview(self, term, fullscreen=False) -> Pretty:
        if fullscreen:
            return Pretty(self.obj)
        else:
            return Pretty(self.obj, max_length=term.height)

    @property
    def fullname(self):
        return self.parent_name + '.' + self.name

    def __getitem__(self, key):
        return self.cached_attributes[key]

    def get_docstring(self, term, fullscreen=False):
        if fullscreen:
            return self.docstring
        else:
            return '\n'.join(self.docstring.splitlines()[:term.height])

    def get_source(self, term, fullscreen=False):
        if not self._source:
            return "[red italic]Source code unavailable"
        if fullscreen:
            return Syntax(
                self._source,
                "python",
                line_numbers=True,
                background_color="default"
            )
        else:
            return Syntax(
                self._source,
                "python",
                line_numbers=True,
                line_range=[0, term.height],
                background_color="default"
            )

    @property
    def display_name(self):
        return f"{self.parent_name}.{self.name}" if self.name else repr(self.obj)

    @property
    def selected_public_attribute(self) -> Optional[str]:
        if self.plain_public_attributes:
            return self.plain_public_attributes[self.public_attribute_index]
        return None

    @property
    def selected_private_attribute(self) -> Optional[str]:
        if self.plain_private_attributes:
            return self.plain_private_attributes[self.private_attribute_index]
        return None

    @property
    def selected_cached_attribute(self):
        if self.attribute_type == PUBLIC and self.selected_public_attribute:
            return self[self.selected_public_attribute]

        elif self.attribute_type == PRIVATE and self.selected_private_attribute:
            return self[self.selected_private_attribute]

    def get_current_obj_attr_panel(self) -> Panel:
        """ TODO """
        # TODO dim if callable?
        if self.attribute_type == PUBLIC:
            attribute_text = []
            for attr in self.plain_public_attributes[self.public_attribute_window:]:
                obj = getattr(self.obj, attr)
                if callable(obj) or obj is None:
                    style = "dim italic"
                else:
                    style = ""

                if attr == self.selected_public_attribute:
                    style += " reverse"

                attribute_text.append(
                    Text(attr, overflow="elipses", style=style)
                )

            title = "[u]public[/u] [dim]private[/dim]"
            subtitle = f"[white]([/white][magenta]{self.public_attribute_index + 1}[/magenta][white]/[/white][magenta]{len(self.plain_public_attributes)}[/magenta][white])"

        elif self.attribute_type == PRIVATE:
            attribute_text = []
            for attr in self.plain_private_attributes[self.private_attribute_window:]:
                obj = getattr(self.obj, attr)
                if callable(obj) or obj is None:
                    style = "dim italic"
                else:
                    style = ""

                if attr == self.selected_private_attribute:
                    style += " reverse"

                attribute_text.append(
                    Text(attr, overflow="elipses", style=style)
                )

            title = "[dim]public[/dim] [underline]private[/underline]"
            subtitle = f"[white]([/white][magenta]{self.private_attribute_index + 1}[/magenta][white]/[/white][magenta]{len(self.plain_private_attributes)}[/magenta][white])"

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

        return panel

    def move_down(self, panel_height):
        """ Move the current selection down one """
        if self.attribute_type == PUBLIC:
            if self.public_attribute_index < len(self.plain_public_attributes) - 1:
                self.public_attribute_index += 1
                if self.public_attribute_index > self.public_attribute_window + panel_height:
                    self.public_attribute_window += 1

        elif self.attribute_type == PRIVATE:
            if self.private_attribute_index < len(self.plain_private_attributes) - 1:
                self.private_attribute_index += 1
                if self.private_attribute_index > self.private_attribute_window + panel_height:
                    self.private_attribute_window += 1

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
