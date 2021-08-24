
from blessed import Terminal
from rich import print as rprint
from rich.repr import rich_repr
from rich.text import Text
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console

console = Console()

PUBLIC = "PUBLIC"
PRIVATE = "PRIVATE"
_term = Terminal()

# TODO methods filter
# or just a type filter?
# Move to next type with {}


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

    def __repr__(self):
        return repr(self.obj)

    @property
    def public_attribute(self):
        return self.cached_public_attributes[self.public_attribute_index]

    @property
    def private_attribute(self):
        return self.cached_private_attributes[self.private_attribute_index]

    def get_panel(self) -> Panel:
        """ TODO """
        if self.attribute_type == PUBLIC:
            attribute_text = [
                Text(attr.name, overflow="elipses", style="reverse") if attr.name == self.public_attribute.name
                else Text(attr.name, overflow="elipses")
                for attr in self.cached_public_attributes[self.public_attribute_window:]
            ]
            title = "[reverse]public[/reverse] - private"
            footer = f"({self.public_attribute_index + 1}/{len(self.public_attributes)})"

        elif self.attribute_type == PRIVATE:
            attribute_text = [
                Text(attr.name, overflow="elipses", style="reverse") if attr.name == self.private_attribute.name
                else Text(attr.name, overflow="elipses")
                for attr in self.cached_private_attributes[self.private_attribute_window:]
            ]
            title = "public - [reverse]private[/reverse]"
            footer = f"({self.private_attribute_index + 1}/{len(self.private_attributes)})"

        renderable_text = None
        for t in attribute_text:
            if not renderable_text:
                # Start with an empty text object, all following Text objects will steal the styles from this one
                renderable_text = Text("", overflow="elipses")
            renderable_text += t + '\n'

        panel = Panel(
            renderable_text,
            title=title,
            footer=footer,
            footer_align="right"
        )

        return panel

    def move_down(self, panel_height):
        """ Move the current selection down one """
        if self.attribute_type == PUBLIC:
            if self.public_attribute_index < len(self.cached_public_attributes) - 1:
                self.public_attribute_index += 1
                if self.public_attribute_index > self.public_attribute_window + panel_height:
                    self.public_attribute_window += 1

        elif self.attribute_type == PRIVATE:
            if self.private_attribute_index < len(self.cached_private_attributes) - 1:
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
            self.public_attribute_window = self.public_attribute_index - panel_height

        elif self.attribute_type == PRIVATE:
            self.private_attribute_index = len(self.private_attributes) - 1
            self.private_attribute_window = self.private_attribute_index - panel_height


class Explorer:
    def __init__(self, obj):
        obj = CachedObject(obj)
        obj.cache_attributes()
        self.head_obj = obj
        self.current_obj = obj
        self.obj_stack = []
        self.term = _term

    @property
    def private_attributes(self):
        return self.current_obj.private_attributes

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

                # Enter
                elif key == "\n":
                    if self.current_obj.attribute_type == PUBLIC:
                        self.obj_stack.append(self.current_obj)
                        self.current_obj = self.current_obj.public_attribute

                    elif self.current_obj.attribute_type == PRIVATE:
                        self.obj_stack.append(self.current_obj)
                        self.current_obj = self.current_obj.private_attribute

                # Escape
                elif key == "\x1b" and self.obj_stack:
                    self.current_obj = self.obj_stack.pop()

    def draw(self):
        print(self.term.home)
        layout = Layout()
        layout.split_column(
            Layout(name="head", size=1),
            Layout(name="body")
        )

        layout["head"].update(Text(repr(self.current_obj), style="italic"))

        layout["body"].split_row(
            Layout(name="explorer"),
            Layout(name="preview")
        )
        layout["body"]["explorer"].split_row(
            Layout(name="current_obj_attributes"),
            Layout(name="selected_obj_attributes")
        )
        layout["body"]["explorer"]["current_obj_attributes"].update(
            self.current_obj.get_panel()
            # self.get_current_obj_panel()
        )
        object_explorer = Panel(
            layout,
            padding=0,
            title="Object Explorer",
            height=self.term.height - 2
        )
        rprint(object_explorer, end='')



def ox(obj):
    explorer = Explorer(obj)
    explorer.explore()


if __name__ == "__main__":
    ox(locals)
