
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from .cached_object import CachedObject


class ExplorerState:
    public, private = 0, 1


class ExplorerLayout(Layout):
    def __init__(self, cached_obj: CachedObject, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cached_obj = cached_obj
        self.state = ExplorerState.public
        self.public_index = self.private_index = 0
        self.public_window = self.private_window = 0

    def selected_cached_object(self, cached_obj) -> CachedObject:
        if self.state == ExplorerState.public:
            attr = cached_obj.plain_public_attributes[self.public_index]
            return cached_obj[attr]

        elif self.state == ExplorerState.private:
            attr = cached_obj.plain_private_attributes[self.private_index]
            return cached_obj[attr]

    def update_selected_cached_object(self):
        if self.state == ExplorerState.public and self.cached_obj.plain_public_attributes:
            attr = self.cached_obj.plain_public_attributes[self.public_index]
            self.cached_obj.selected_cached_obj = self.cached_obj[attr]
            pass

        elif self.state == ExplorerState.private and self.cached_obj.plain_private_attributes:
            attr = self.cached_obj.plain_private_attributes[self.private_index]
            self.cached_obj.selected_cached_obj = self.cached_obj[attr]

    def __call__(self, cached_obj: CachedObject, term_width: int) -> Layout:
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

            title = "[i][cyan]dir[/cyan]()[/i] | [u]public[/u] [dim]private[/dim]"
            subtitle = (
                f"[white]([/white][magenta]{self.public_index + 1 if cached_obj.plain_public_attributes else 0}"
                f"[/magenta][white]/[/white][magenta]{len(cached_obj.plain_public_attributes)}[/magenta][white])"
            )

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

            title = "[i][cyan]dir[/cyan]()[/i] | [dim]public[/dim] [u]private[/u]"
            subtitle = (
                f"[white]([/white][magenta]{self.private_index + 1}"
                f"[/magenta][white]/[/white][magenta]{len(cached_obj.plain_private_attributes)}[/magenta][white])"
            )

        # If terminal is too small don't show the 'dir()' part of the title
        if term_width / 4 < 28:
            title = title.split('|')[-1].strip()

        # Start with an empty text object, all following Text objects will steal the styles from this one
        renderable_text = Text("", overflow="elipses")
        for t in attribute_text:
            renderable_text += t + '\n'

        panel = Panel(
            renderable_text,
            title=title,
            title_align="right",
            subtitle=subtitle,
            subtitle_align="right",
            style="white"
        )
        self.update(panel)
        return self

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
        self.update_selected_cached_object()

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
        self.update_selected_cached_object()

    def move_top(self):
        if self.state == ExplorerState.public:
            self.public_index = 0
            self.public_window = 0

        elif self.state == ExplorerState.private:
            self.private_index = 0
            self.private_window = 0
        self.update_selected_cached_object()

    def move_bottom(self, panel_height: int, cached_obj: CachedObject):
        if self.state == ExplorerState.public:
            self.public_index = len(cached_obj.plain_public_attributes) - 1
            self.public_window = max(0, self.public_index - panel_height)

        elif self.state == ExplorerState.private:
            self.private_index = len(cached_obj.plain_private_attributes) - 1
            self.private_window = max(0, self.private_index - panel_height)
        self.update_selected_cached_object()
