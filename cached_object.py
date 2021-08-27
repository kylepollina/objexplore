
from rich import print as rprint
# from rich.repr import rich_repr
from rich.text import Text
from rich.panel import Panel
from rich.console import Console


PUBLIC = "PUBLIC"
PRIVATE = "PRIVATE"

console = Console()


class CachedObject:

    def __init__(self, obj, name=None):
        self.obj = obj
        self.name = name
        self.attribute_type = PUBLIC
        self.public_attribute_index = 0
        self.private_attribute_index = 0
        self.public_attribute_window = 0
        self.private_attribute_window = 0

        self.public_attributes = sorted(
            attr for attr in dir(self.obj) if not attr.startswith('_')
        )
        self.private_attributes = sorted(
            attr for attr in dir(self.obj) if attr.startswith('_')
        )
        self.cached_public_attributes = []
        self.cached_private_attributes = []

        with console.capture() as capture:
            console.print(type(self.obj))

        self.obj_type = capture.get()

    def cache_attributes(self):
        self.cached_public_attributes = [
            CachedObject(getattr(self.obj, attr), name=attr)
            for attr in self.public_attributes
        ]
        self.cached_private_attributes = [
            CachedObject(getattr(self.obj, attr), name=attr)
            for attr in self.private_attributes
        ]

    def __getitem__(self, item):
        return CachedObject(getattr(self.obj, item))

    @property
    def selected_public_attribute(self):
        return self.public_attributes[self.public_attribute_index]

    @property
    def selected_private_attribute(self):
        return self.private_attributes[self.private_attribute_index]

    @property
    def selected_public_attr_cached(self):
        return self.cached_public_attributes[self.public_attribute_index]

    @property
    def private_attribute(self):
        return self.private_attributes[self.private_attribute_index]

    @property
    def selected_private_attr_cached(self):
        return self.cached_private_attributes[self.private_attribute_index]

    def get_current_obj_attr_panel(self) -> Panel:
        """ TODO """
        if self.attribute_type == PUBLIC:
            attribute_text = [
                Text(attr, overflow="elipses", style="reverse") if attr == self.selected_public_attribute
                else Text(attr, overflow="elipses")
                for attr in self.public_attributes[self.public_attribute_window:]
            ]
            title = "[reverse]public[/reverse] - private"
            subtitle = f"({self.public_attribute_index + 1}/{len(self.public_attributes)})"

        elif self.attribute_type == PRIVATE:
            attribute_text = [
                Text(attr, overflow="elipses", style="reverse") if attr == self.private_attribute
                else Text(attr, overflow="elipses")
                for attr in self.private_attributes[self.private_attribute_window:]
            ]
            title = "public - [reverse]private[/reverse]"
            subtitle = f"({self.private_attribute_index + 1}/{len(self.private_attributes)})"

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
            subtitle_align="right"
        )

        return panel

    def get_selected_obj_attr_panel(self) -> Panel:
        if self.attribute_type == PUBLIC:
            selected_attr = self.selected_public_attr_cached
            title = self.selected_public_attribute
        elif self.attribute_type == PRIVATE:
            selected_attr = self.selected_private_attr_cached
            title = self.selected_private_attribute

        # text = Text("", end="\n")
        text = ""
        text += f"{len(selected_attr.public_attributes)} public attributes\n"
        text += f"{len(selected_attr.private_attributes)} private attributes\n"
        text += selected_attr.obj_type

        panel = Panel(
            Text(selected_attr.obj_type, overflow="elipses"),
            # "[red]hello",
            title=title
        )
        return panel

    def move_down(self, panel_height):
        """ Move the current selection down one """
        if self.attribute_type == PUBLIC:
            if self.public_attribute_index < len(self.public_attributes) - 1:
                self.public_attribute_index += 1
                if self.public_attribute_index > self.public_attribute_window + panel_height:
                    self.public_attribute_window += 1

        elif self.attribute_type == PRIVATE:
            if self.private_attribute_index < len(self.private_attributes) - 1:
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
            self.public_attribute_index = len(self.public_attributes) - 1
            self.public_attribute_window = max(0, self.public_attribute_index - panel_height)

        elif self.attribute_type == PRIVATE:
            self.private_attribute_index = len(self.private_attributes) - 1
            self.private_attribute_window = max(0, self.private_attribute_index - panel_height)
