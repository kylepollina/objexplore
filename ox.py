
from blessed import Terminal
import rich.print as rprint
from rich.layout import Layout
from rich.panel import Panel

PUBLIC = "public"
PRIVATE = "private"


# TODO methods filter
# TODO cache on startup and entering new objs

class Explorer:
    def __init__(self, obj):
        self.head_obj = obj
        self.current_obj = obj
        self.object_stact = []
        self.term = Terminal()

        self.update_attributes()

    def update_attributes(self):
        """ Update the public and private attributes based on the current object """
        self.public_attributes = sorted(
            attr for attr in dir(self.current_obj) if not attr.startswith('_')
        )
        self.private_attributes = sorted(
            attr for attr in dir(self.current_obj) if attr.startswith('_')
        )

        self.attribute_type = PUBLIC
        self.public_attribute_index = 0
        self.private_attribute_index = 0

        # TODO try/except in case one or both of the lists are empty?
        self.selected_public_attribute = self.public_attributes[0]
        self.selected_private_attribute = self.private_attributes[0]

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

                    elif self.attribute_type == PRIVATE:
                        if self.private_attribute_index < len(self.private_attributes) - 1:
                            self.private_attribute_index += 1
                            self.selected_private_attribute = self.private_attributes[self.private_attribute_index]

                # move selected attribute up
                if key == "k":
                    if self.attribute_type == PUBLIC:
                        if self.public_attribute_index > 0:
                            self.public_attribute_index -= 1
                            self.selected_public_attribute = self.public_attributes[self.public_attribute_index]

                    elif self.attribute_type == PRIVATE:
                        if self.private_attribute_index > 0:
                            self.private_attribute_index -= 1
                            self.selected_private_attribute = self.private_attributes[self.private_attribute_index]

    def draw(self):
        print(self.term.home)
        layout = Layout()
        layout.split_row(
            Layout(name="explorer"),
            Layout(name="preview")
        )
        layout["explorer"].split_row(
            Layout(name="current_obj_attributes"),
            Layout(name="selected_obj_attributes")
        )
        layout["explorer"]["current_obj_attributes"].update(
            self.get_current_obj_panel(layout)
        )
        object_explorer = Panel(
            layout,
            title="Object Explorer",
            height=self.term.height - 2
        )
        rprint(object_explorer, end='')

    def get_current_obj_panel(self, layout) -> Panel:
        if self.attribute_type == PUBLIC:
            public_attributes = sorted([attr for attr in dir(self.current_obj) if not attr.startswith('_')])

            # TODO fix the rendering of the selected attribute
            h = self.term.height - 8
            panel = Panel(
                "temp",
                title="[reverse]public[/reverse] - private"
            )
            x = max(self.public_attribute_index - h, 0)

            attribute_text = "\n".join(
                attr if attr != self.selected_public_attribute
                else "[reverse]" + attr + "[/reverse]"
                for attr in public_attributes[x:x+h]
            )
            panel.renderable = attribute_text

            return panel

        # Private
        elif self.attribute_type == PRIVATE:
            private_attributes = sorted([attr for attr in dir(self.current_obj) if attr.startswith('_')])

            attribute_text = "\n".join(
                attr if attr != self.selected_private_attribute
                else "[reverse]" + attr + "[/reverse]"
                for attr in private_attributes
            )

            panel = Panel(
                attribute_text,
                title="public - [reverse]private[/reverse]"
            )
            return panel


def ox(obj):
    explorer = Explorer(obj)
    explorer.explore()


if __name__ == "__main__":
    ox(locals)
