
from blessed import Terminal
from rich import print as rprint
from rich.text import Text
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console

console = Console()

PUBLIC = "public"
PRIVATE = "private"
_term = Terminal()

# TODO methods filter
# TODO cache on startup and entering new objs
# TODO G/g for moving attribute window


class Explorer:
    def __init__(self, obj):
        self.head_obj = obj
        self.current_obj = obj
        self.object_stact = []
        self.term = _term

        self.update_attributes()

    def update_attributes(self):
        """ Update the public and private attributes based on the current object """
        self.public_attributes = sorted(
            attr for attr in dir(self.current_obj) if not attr.startswith('_')
        )
        self.private_attributes = sorted(
            attr for attr in dir(self.current_obj) if attr.startswith('_')
        )

        # TODO make public/private attributes some kind of dataclass?
        self.attribute_type = PUBLIC
        self.public_attribute_index = 0
        self.private_attribute_index = 0
        self.public_attribute_window = 0
        self.private_attribute_window = 0

        # TODO try/except in case one or both of the lists are empty?
        self.selected_public_attribute = self.public_attributes[0]
        self.selected_private_attribute = self.private_attributes[0]

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
                    if self.attribute_type == PUBLIC:
                        self.attribute_type = PRIVATE

                    elif self.attribute_type == PRIVATE:
                        self.attribute_type = PUBLIC

                # move selected attribute down
                if key == "j":
                    if self.attribute_type == PUBLIC:
                        if self.public_attribute_index < len(self.public_attributes) - 1:
                            self.public_attribute_index += 1
                            self.selected_public_attribute = self.public_attributes[self.public_attribute_index]
                            if self.public_attribute_index > self.public_attribute_window + self.panel_height:
                                self.public_attribute_window += 1

                    elif self.attribute_type == PRIVATE:
                        if self.private_attribute_index < len(self.private_attributes) - 1:
                            self.private_attribute_index += 1
                            self.selected_private_attribute = self.private_attributes[self.private_attribute_index]
                            if self.private_attribute_index > self.private_attribute_window + self.panel_height:
                                self.private_attribute_window += 1

                # move selected attribute up
                if key == "k":
                    if self.attribute_type == PUBLIC:
                        if self.public_attribute_index > 0:
                            self.public_attribute_index -= 1
                            self.selected_public_attribute = self.public_attributes[self.public_attribute_index]
                            if self.public_attribute_index < self.public_attribute_window:
                                self.public_attribute_window -= 1

                    elif self.attribute_type == PRIVATE:
                        if self.private_attribute_index > 0:
                            self.private_attribute_index -= 1
                            self.selected_private_attribute = self.private_attributes[self.private_attribute_index]
                            if self.private_attribute_index < self.private_attribute_window:
                                self.private_attribute_window -= 1

                if key == "g":
                    if self.attribute_type == PUBLIC:
                        self.public_attribute_index = 0
                        self.public_attribute_window = 0
                        self.selected_public_attribute = self.public_attributes[self.public_attribute_index]

                    elif self.attribute_type == PRIVATE:
                        self.private_attribute_index = 0
                        self.private_attribute_window = 0
                        self.selected_private_attribute = self.private_attributes[self.private_attribute_index]

                if key == "G":
                    if self.attribute_type == PUBLIC:
                        self.public_attribute_index = len(self.public_attributes) - 1
                        self.public_attribute_window = self.public_attribute_index - self.panel_height
                        self.selected_public_attribute = self.public_attributes[self.public_attribute_index]

                    elif self.attribute_type == PRIVATE:
                        self.private_attribute_index = len(self.private_attributes) - 1
                        self.private_attribute_window = self.private_attribute_index - self.panel_height
                        self.selected_private_attribute = self.private_attributes[self.private_attribute_index]

    def draw(self):
        print(self.term.home)
        layout = Layout()
        layout.split_column(
            Layout(name="head", size=1),
            Layout(name="body")
        )
        layout["head"].update("something goes here")

        layout["body"].split_row(
            Layout(name="explorer"),
            Layout(name="preview")
        )
        layout["body"]["explorer"].split_row(
            Layout(name="current_obj_attributes"),
            Layout(name="selected_obj_attributes")
        )
        layout["body"]["explorer"]["current_obj_attributes"].update(
            self.get_current_obj_panel()
        )
        object_explorer = Panel(
            layout,
            padding=0,
            title="Object Explorer",
            height=self.term.height - 2
        )
        rprint(object_explorer, end='')

    def get_current_obj_panel(self) -> Panel:
        """ TODO """
        if self.attribute_type == PUBLIC:
            attribute_text = [
                Text(attr, overflow="elipses", style="reverse") if attr == self.selected_public_attribute
                else Text(attr, overflow="elipses")
                for attr in self.public_attributes[self.public_attribute_window:]
            ]
            title = "[reverse]public[/reverse] - private"
            footer = f"({self.public_attribute_index + 1}/{len(self.public_attributes)})"

        elif self.attribute_type == PRIVATE:
            attribute_text = [
                Text(attr, overflow="elipses", style="reverse") if attr == self.selected_private_attribute
                else Text(attr, overflow="elipses")
                for attr in self.private_attributes[self.private_attribute_window:]
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


def ox(obj):
    explorer = Explorer(obj)
    explorer.explore()


if __name__ == "__main__":
    ox(locals)
