from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from collections import namedtuple

from .cached_object import CachedObject
from rich.highlighter import ReprHighlighter

ExplorerState = namedtuple('ExplorerState', ['public', 'private', 'dict'])

highlighter = ReprHighlighter()

class ExplorerLayout(Layout):
    def __init__(self, cached_obj: CachedObject, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cached_obj = cached_obj
        if type(cached_obj.obj) == dict:
            self.state = ExplorerState.dict
        else:
            self.state = ExplorerState.public
        self.public_index = self.private_index = 0
        self.public_window = self.private_window = 0
        self.dict_index = self.dict_window = 0

    def selected_cached_object(self, cached_obj) -> CachedObject:
        if self.state == ExplorerState.public:
            attr = cached_obj.plain_public_attributes[self.public_index]
            return cached_obj[attr]

        else:  # ExplorerState.private
            attr = cached_obj.plain_private_attributes[self.private_index]
            return cached_obj[attr]

    def update_selected_cached_object(self):
        if (
            self.state == ExplorerState.public
            and self.cached_obj.plain_public_attributes
        ):
            attr = self.cached_obj.plain_public_attributes[self.public_index]
            self.cached_obj.selected_cached_obj = self.cached_obj[attr]
            pass

        elif (
            self.state == ExplorerState.private
            and self.cached_obj.plain_private_attributes
        ):
            attr = self.cached_obj.plain_private_attributes[self.private_index]
            self.cached_obj.selected_cached_obj = self.cached_obj[attr]

        elif self.state == ExplorerState.dict:
            # have to create a cached object every time to not infinitely recurse
            # TODO add more details
            key = list(self.cached_obj.obj.keys())[self.dict_index]
            self.cached_obj.selected_cached_obj = CachedObject(self.cached_obj.obj[key], attr_name=key)

    def dict_layout(self, cached_obj: CachedObject, term_width: int) -> Layout:
        lines = [Text('{', style="none")]
        panel_width = (term_width - 4) // 4 - 4
        for index, line in enumerate(cached_obj.repr_dict_lines):
            new_line = line.copy()

            if index == self.dict_index:
                new_line.style = "reverse"

            new_line.truncate(panel_width)
            lines.append(new_line)

        lines.append(Text('}'))

        text = Text('\n').join(lines[self.dict_window:])

        return Layout(
            Panel(
                text,
                style="white"
            )
        )

    def __call__(self, cached_obj: CachedObject, term_width: int) -> Layout:
        if self.state == ExplorerState.dict:
            return self.dict_layout(cached_obj, term_width)

        lines = []

        if self.state == ExplorerState.public:
            for index, line in enumerate(cached_obj.repr_public_lines):
                new_line = line.copy()
                if index == self.public_index:
                    new_line.style += " reverse"
                lines.append(new_line)

            title = "[i][cyan]dir[/cyan]()[/i] | [u]public[/u] [dim]private[/dim]"
            subtitle = (
                "[dim][u][][/u]:switch pane [/dim]"
                f"[white]([/white][magenta]{self.public_index + 1 if cached_obj.plain_public_attributes else 0}"
                f"[/magenta][white]/[/white][magenta]{len(cached_obj.plain_public_attributes)}[/magenta][white])"
            )


        elif self.state == ExplorerState.private:
            for index, line in enumerate(cached_obj.repr_private_lines):
                new_line = line.copy()
                if index == self.private_index:
                    new_line.style += " reverse"
                lines.append(new_line)

            title = "[i][cyan]dir[/cyan]()[/i] | [dim]public[/dim] [u]private[/u]"
            subtitle = (
                "[dim][u][][/u]:switch pane [/dim]"
                f"[white]([/white][magenta]{self.private_index + 1}"
                f"[/magenta][white]/[/white][magenta]{len(cached_obj.plain_private_attributes)}[/magenta][white])"
            )


        renderable = Text('\n').join(lines[self.public_window:])

        # If terminal is too small don't show the 'dir()' part of the title
        if term_width / 4 < 28:
            title = title.split("|")[-1].strip()

        self.update(
            Panel(
                renderable,
                title=title,
                title_align="right",
                subtitle=subtitle,
                subtitle_align="right",
                style="white",
            )
        )
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

        elif self.state == ExplorerState.dict:
            if self.dict_index > 0:
                self.dict_index -= 1
                if self.dict_index < self.dict_window - 1:
                    self.dict_window -= 1
            elif self.dict_window == 1:
                self.dict_window -= 1

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

        elif self.state == ExplorerState.dict:
            if self.dict_index < len(cached_obj.obj.keys()) - 1:
                self.dict_index += 1
                if self.dict_index > self.dict_window + panel_height - 1:
                    self.dict_window += 1
            elif self.dict_window == len(cached_obj.obj.keys()) - panel_height:
                self.dict_window += 1

        self.update_selected_cached_object()

    def move_top(self):
        if self.state == ExplorerState.public:
            self.public_index = 0
            self.public_window = 0

        elif self.state == ExplorerState.private:
            self.private_index = 0
            self.private_window = 0

        elif self.state == ExplorerState.dict:
            self.dict_index = self.dict_window = 0

        self.update_selected_cached_object()

    def move_bottom(self, panel_height: int, cached_obj: CachedObject):
        if self.state == ExplorerState.public:
            self.public_index = len(cached_obj.plain_public_attributes) - 1
            self.public_window = max(0, self.public_index - panel_height)

        elif self.state == ExplorerState.private:
            self.private_index = len(cached_obj.plain_private_attributes) - 1
            self.private_window = max(0, self.private_index - panel_height)

        elif self.state == ExplorerState.dict:
            self.dict_index = len(cached_obj.obj.keys()) - 1
            self.dict_window = max(0, self.dict_index - panel_height + 2)

        self.update_selected_cached_object()
