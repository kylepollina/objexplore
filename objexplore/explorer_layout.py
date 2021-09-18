from collections import namedtuple
import types
from typing import List

from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from .cached_object import CachedObject

console = Console()

ExplorerState = namedtuple(
    "ExplorerState", ["public", "private", "dict", "list", "tuple"]
)

highlighter = ReprHighlighter()


class ExplorerLayout(Layout):
    def __init__(self, cached_obj: CachedObject, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cached_obj = cached_obj
        _type = type(cached_obj.obj)
        if _type == dict:
            self.state = ExplorerState.dict
        elif _type == list:
            self.state = ExplorerState.list
        elif _type == tuple:
            self.state = ExplorerState.tuple
        else:
            self.state = ExplorerState.public
        self.public_index = self.private_index = 0
        self.public_window = self.private_window = 0
        self.dict_index = self.dict_window = 0
        self.list_index = self.list_window = 0

    def selected_cached_object(self) -> CachedObject:
        try:
            if self.state == ExplorerState.public:
                attr = list(self.cached_obj.filtered_public_attributes.keys())[self.public_index]
                return self.cached_obj.filtered_public_attributes[attr]

            elif self.state == ExplorerState.private:
                attr = list(self.cached_obj.filtered_private_attributes.keys())[self.private_index]
                return self.cached_obj.filtered_private_attributes[attr]

        except IndexError:
            return CachedObject(None)

    @staticmethod
    def get_panel_width(term_width: int) -> int:
        return (term_width - 4) // 4 - 4

    @staticmethod
    def get_panel_height(term_height: int) -> int:
        return term_height - 5

    def __call__(self, term_width: int, term_height: int) -> Layout:
        """ Return the layout of the object explorer. This will be a list of lines representing the object attributes/keys/vals we are exploring """
        # TODO change to just accept term object
        # TODO use [] to switch between public/private/dict layout?

        if self.state == ExplorerState.dict:
            return self.dict_layout(term_width, term_height)

        elif self.state in (ExplorerState.list, ExplorerState.tuple):
            return self.list_layout(term_width, term_height)

        else:
            return self.dir_layout(term_width, term_height)

    @property
    def selected_object(self) -> CachedObject:
        """ Return the currently selected cached object """
        if self.state == ExplorerState.public:
            attr = list(self.cached_obj.filtered_public_attributes.keys())[self.public_index]
            return self.cached_obj.filtered_public_attributes[attr]

        elif self.state == ExplorerState.private:
            attr = list(self.cached_obj.filtered_private_attributes.keys())[self.private_index]
            return self.cached_obj.filtered_private_attributes[attr]

        elif self.state == ExplorerState.dict:
            attr = list(self.cached_obj.filtered_dict)[self.dict_index]
            return self.cached_obj.filterd_dict[attr]

        elif self.state in (ExplorerState.list, ExplorerState.tuple):
            return self.cached_obj.filtered_list[self.list_index]

    def dict_layout(self, term_width: int, term_height: int) -> Layout:
        """ Return the dictionary explorer layout """
        # TODO support filters
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
            lines.append(Text("[" if self.state == ExplorerState.list else "("))
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

        lines.append(Text("]" if self.state == ExplorerState.list else ")"))

        text = Text("\n").join(lines)

        self.update(
            Panel(
                text,
                title=f"[i][cyan]{'list' if self.state == ExplorerState.list else 'tuple'}[/cyan]()",
                title_align="right",
                subtitle=f"([magenta]{self.list_index + 1}[/magenta]/[magenta]{self.cached_obj.length}[/magenta])",
                subtitle_align="right",
                style="white",
            )
        )
        return self

    def dir_layout(self, term_width: int, term_height: int) -> Layout:
        lines = []

        if self.state == ExplorerState.public:
            # Reset the public index / window in case applying a filter has now moved the index
            # farther down than it can access on the filtered attributes
            if self.public_index >= len(self.cached_obj.filtered_public_attributes):
                self.public_index = max(0, len(self.cached_obj.filtered_public_attributes) - 1)
                self.public_window = max(0, self.public_index - self.get_panel_height(term_height))

            for index, (attr, cached_obj) in enumerate(self.cached_obj.filtered_public_attributes.items()):
                line = cached_obj.text.copy()
                if index == self.public_index:
                    line.style += Style(reverse=True)
                lines.append(line)

            title = "[i][cyan]dir[/cyan]()[/i] | [u]public[/u] [dim]private[/dim]"
            subtitle = (
                "[dim][u][][/u]:switch pane [/dim]"
                f"[white]([/white][magenta]{self.public_index + 1 if self.cached_obj.filtered_public_attributes else 0}"
                f"[/magenta][white]/[/white][magenta]{len(self.cached_obj.filtered_public_attributes)}[/magenta][white])"
            )

        elif self.state == ExplorerState.private:
            # Reset the private index / window in case applying a filter has now moved the index
            # farther down than it can access on the filtered attributes
            if self.private_index >= len(self.cached_obj.filtered_private_attributes):
                self.private_index = max(0, len(self.cached_obj.filtered_private_attributes) - 1)
                self.private_window = max(0, self.private_index - self.get_panel_height(term_height))

            for index, (attr, cached_obj) in enumerate(self.cached_obj.filtered_private_attributes.items()):
                line = cached_obj.text.copy()
                if index == self.private_index:
                    line.style += Style(reverse=True)
                lines.append(line)

            title = "[i][cyan]dir[/cyan]()[/i] | [dim]public[/dim] [u]private[/u]"
            subtitle = (
                "[dim][u][][/u]:switch pane [/dim]"
                f"[white]([/white][magenta]{self.private_index + 1 if self.cached_obj.filtered_private_attributes else 0}"
                f"[/magenta][white]/[/white][magenta]{len(self.cached_obj.filtered_private_attributes)}[/magenta][white])"
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

        elif self.state in (ExplorerState.list, ExplorerState.tuple):
            if self.list_index > 0:
                self.list_index -= 1
                if self.list_index < self.list_window - 1:
                    self.list_window -= 1
            elif self.list_window == 1:
                self.list_window -= 1

    def move_down(self, panel_height: int, cached_obj: CachedObject):
        """ Move the current selection down one """
        if self.state == ExplorerState.public:
            if self.public_index < len(cached_obj.filtered_public_attributes) - 1:
                self.public_index += 1
                if self.public_index > self.public_window + panel_height:
                    self.public_window += 1

        elif self.state == ExplorerState.private:
            if self.private_index < len(cached_obj.filtered_private_attributes) - 1:
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

        elif self.state in (ExplorerState.list, ExplorerState.tuple):
            if self.list_index < len(cached_obj.obj) - 1:
                self.list_index += 1
                if self.list_index > self.list_window + panel_height - 1:
                    self.list_window += 1
            elif self.list_window == len(cached_obj.obj) - panel_height:
                self.list_window += 1

    def move_top(self):
        if self.state == ExplorerState.public:
            self.public_index = 0
            self.public_window = 0

        elif self.state == ExplorerState.private:
            self.private_index = 0
            self.private_window = 0

        elif self.state == ExplorerState.dict:
            self.dict_index = self.dict_window = 0

        elif self.state in (ExplorerState.list, ExplorerState.tuple):
            self.list_index = self.list_window = 0

    def move_bottom(self, panel_height: int, cached_obj: CachedObject):
        if self.state == ExplorerState.public:
            self.public_index = len(cached_obj.filtered_public_attributes) - 1
            self.public_window = max(0, self.public_index - panel_height)

        elif self.state == ExplorerState.private:
            self.private_index = len(cached_obj.filtered_private_attributes) - 1
            self.private_window = max(0, self.private_index - panel_height)

        elif self.state == ExplorerState.dict:
            self.dict_index = len(cached_obj.obj.keys()) - 1
            self.dict_window = max(0, self.dict_index - panel_height + 2)

        elif self.state in (ExplorerState.list, ExplorerState.tuple):
            self.list_index = len(cached_obj.obj) - 1
            self.list_window = max(0, self.list_index - panel_height + 2)
