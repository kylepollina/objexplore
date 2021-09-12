
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from .cached_object import CachedObject


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

                if attr == cached_obj.plain_private_attributes[self.private_index]:
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
        """ Move the current selection up one """
        if self.state == ExplorerState.public:
            if self.public_index > 0:
                self.public_index -= 1
                if self.public_index < self.public_window:
                    self.public_window -= 1

        elif self.state == ExplorerState.private:
            if self.private_index > 0:
                self.private_index -= 1
                if self.private_index < self.private_window:
                    self.private_window -= 1

    def move_top(self):
        if self.state == ExplorerState.public:
            self.public_index = 0
            self.public_window = 0

        elif self.state == ExplorerState.private:
            self.private_index = 0
            self.private_window = 0

    def move_bottom(self, panel_height: int, cached_obj: CachedObject):
        if self.state == ExplorerState.public:
            self.public_index = len(cached_obj.plain_public_attributes) - 1
            self.public_window = max(0, self.public_index - panel_height)

        elif self.state == ExplorerState.private:
            self.private_index = len(cached_obj.plain_private_attributes) - 1
            self.private_window = max(0, cached_obj.private_attribute_index - panel_height)
