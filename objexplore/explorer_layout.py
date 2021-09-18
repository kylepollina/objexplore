from collections import namedtuple

from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from .cached_object import CachedObject

console = Console()

ExplorerState = namedtuple("ExplorerState", ["public", "private", "dict", "list"])

highlighter = ReprHighlighter()


class ExplorerLayout(Layout):
    def __init__(self, cached_obj: CachedObject, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cached_obj = cached_obj
        if type(cached_obj.obj) == dict:
            self.state = ExplorerState.dict
        elif type(cached_obj.obj) == list:
            self.state = ExplorerState.list
        else:
            self.state = ExplorerState.public
        self.public_index = self.private_index = 0
        self.public_window = self.private_window = 0
        self.dict_index = self.dict_window = 0
        self.list_index = self.list_window = 0

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
            self.cached_obj.selected_cached_obj = CachedObject(
                self.cached_obj.obj[key], attr_name=key
            )

        elif self.state == ExplorerState.list:
            item = self.cached_obj.obj[self.list_index]
            self.cached_obj.selected_cached_obj = CachedObject(item)

    @staticmethod
    def get_panel_width(term_width: int) -> int:
        return (term_width - 4) // 4 - 4

    @staticmethod
    def get_panel_height(term_height: int) -> int:
        return term_height - 5

    def dict_layout(self, term_width: int, term_height: int) -> Layout:
        """ Return the dictionary explorer layout """
        panel_width = self.get_panel_width(term_width)
        panel_height = self.get_panel_height(term_height)
        lines = []

        if self.dict_window == 0:
            lines.append(Text("{"))
            start = 0
            num_lines = panel_height - 1
        elif self.dict_window == 1:
            start = 0
            num_lines = panel_height
        else:
            start = self.dict_window - 1
            num_lines = panel_height

        end = start + num_lines
        index = start

        for line in self.cached_obj.dict_lines[start:end]:
            new_line = line.copy()

            if index == self.dict_index:
                new_line.style = "reverse"

            new_line.truncate(panel_width)
            lines.append(new_line)
            index += 1

        # Always add the } to the end, if it is out of view it won't be printed anyways
        lines.append(Text("}"))

        text = Text("\n").join(lines)

        self.update(
            Panel(
                text,
                title="[i][cyan]dict[/cyan]()",
                title_align="right",
                subtitle=f"([magenta]{self.dict_index + 1}[/magenta]/[magenta]{self.cached_obj.length}[/magenta])",
                subtitle_align="right",
                style="white",
            )
        )
        return self

    def list_layout(self, term_width: int, term_height: int) -> Layout:
        panel_width = self.get_panel_width(term_width)
        panel_height = self.get_panel_height(term_height)
        lines = []

        if self.list_window == 0:
            lines.append(Text("["))
            start = 0
            num_lines = panel_height - 1
        elif self.list_window == 1:
            start = 0
            num_lines = panel_height
        else:
            start = self.list_window - 1
            num_lines = panel_height

        end = start + num_lines
        index = start

        for line in self.cached_obj.list_lines[start:end]:
            new_line = line.copy()

            if index == self.list_index:
                new_line.style = "reverse"

            new_line.truncate(panel_width)
            lines.append(new_line)
            index += 1

        lines.append(Text("]"))

        text = Text("\n").join(lines)

        self.update(
            Panel(
                text,
                title="[i][cyan]list[/cyan]()",
                title_align="right",
                subtitle=f"([magenta]{self.list_index + 1}[/magenta]/[magenta]{self.cached_obj.length}[/magenta])",
                subtitle_align="right",
                style="white",
            )
        )
        return self

    def __call__(self, term_width: int, term_height: int) -> Layout:
        # TODO change to just accept term object
        """ Return the layout of the object explorer. This will be a list of lines representing the object attributes/keys/vals we are exploring """
        # TODO use [] to switch between public/private/dict layout?

        if self.state == ExplorerState.dict:
            return self.dict_layout(term_width, term_height)

        elif self.state == ExplorerState.list:
            return self.list_layout(term_width, term_height)

        else:
            return self.dir_layout(term_width)

    def dir_layout(self, term_width: int) -> Layout:
        lines = []

        if self.state == ExplorerState.public:
            for index, line in enumerate(self.cached_obj.public_lines):
                _line = line.copy()
                if index == self.public_index:
                    _line.style += Style(reverse=True)  # type: ignore
                lines.append(_line)

            title = "[i][cyan]dir[/cyan]()[/i] | [u]public[/u] [dim]private[/dim]"
            subtitle = (
                "[dim][u][][/u]:switch pane [/dim]"
                f"[white]([/white][magenta]{self.public_index + 1 if self.cached_obj.plain_public_attributes else 0}"
                f"[/magenta][white]/[/white][magenta]{len(self.cached_obj.plain_public_attributes)}[/magenta][white])"
            )

        elif self.state == ExplorerState.private:
            for index, line in enumerate(self.cached_obj.private_lines):
                _line = line.copy()
                if index == self.private_index:
                    _line.style += Style(reverse=True)  # type: ignore
                lines.append(_line)

            title = "[i][cyan]dir[/cyan]()[/i] | [dim]public[/dim] [u]private[/u]"
            subtitle = (
                "[dim][u][][/u]:switch pane [/dim]"
                f"[white]([/white][magenta]{self.private_index + 1}"
                f"[/magenta][white]/[/white][magenta]{len(self.cached_obj.plain_private_attributes)}[/magenta][white])"
            )

        renderable = Text("\n").join(lines[self.public_window :])

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

        elif self.state == ExplorerState.list:
            if self.list_index > 0:
                self.list_index -= 1
                if self.list_index < self.list_window - 1:
                    self.list_window -= 1
            elif self.list_window == 1:
                self.list_window -= 1

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

        elif self.state == ExplorerState.list:
            if self.list_index < len(cached_obj.obj) - 1:
                self.list_index += 1
                if self.list_index > self.list_window + panel_height - 1:
                    self.list_window += 1
            elif self.list_window == len(cached_obj.obj) - panel_height:
                self.list_window += 1

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

        elif self.state == ExplorerState.list:
            self.list_index = self.list_window = 0

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

        elif self.state == ExplorerState.list:
            self.list_index = len(cached_obj.obj) - 1
            self.list_window = max(0, self.list_index - panel_height + 2)

        self.update_selected_cached_object()
