from typing import Union, Any, Dict
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from .cached_object import CachedObject

console = Console()


class ExplorerState:
    public = "ExplorerState.public"
    private = "ExplorerState.private"
    dict = "ExplorerState.dict"
    list = "ExplorerState.list"
    tuple = "ExplorerState.tuple"
    set = "ExplorerState.set"


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
        elif _type == set:
            self.state = ExplorerState.set
        else:
            self.state = ExplorerState.public
        self.public_index = self.private_index = 0
        self.public_window = self.private_window = 0
        self.dict_index = self.dict_window = 0
        self.list_index = self.list_window = 0

    @staticmethod
    def get_panel_width(term_width: int) -> int:
        return (term_width - 4) // 4 - 4

    @staticmethod
    def get_panel_height(term_height: int) -> int:
        return term_height - 5

    def __call__(self, term_width: int, term_height: int) -> Layout:
        """ Return the layout of the object explorer. This will be a list of lines representing the object attributes/keys/vals we are exploring """
        # TODO change to just accept term object

        if self.state == ExplorerState.dict:
            return self.dict_layout(term_width, term_height)

        elif self.state in (ExplorerState.list, ExplorerState.tuple, ExplorerState.set):
            return self.list_layout(term_width, term_height)

        else:
            return self.dir_layout(term_width, term_height)

    @property
    def selected_object(self) -> CachedObject:  # type: ignore
        """ Return the currently selected cached object """
        try:
            if self.state == ExplorerState.public:
                attr = list(self.cached_obj.filtered_public_attributes.keys())[
                    self.public_index
                ]
                return self.cached_obj.filtered_public_attributes[attr]

            elif self.state == ExplorerState.private:
                attr = list(self.cached_obj.filtered_private_attributes.keys())[
                    self.private_index
                ]
                return self.cached_obj.filtered_private_attributes[attr]

            elif self.state == ExplorerState.dict:
                attr = list(self.cached_obj.filtered_dict)[self.dict_index]
                return self.cached_obj.filtered_dict[attr][1]

            elif self.state in (
                ExplorerState.list,
                ExplorerState.tuple,
                ExplorerState.set,
            ):
                return self.cached_obj.filtered_list[self.list_index][1]

        except (KeyError, IndexError):
            return CachedObject(None)

    def get_all_attributes(self) -> Union[Dict[str, CachedObject], Any]:
        if self.state == ExplorerState.public:
            return self.cached_obj.public_attributes
        elif self.state == ExplorerState.private:
            return self.cached_obj.private_attributes
        else:
            return self.cached_obj.obj

    def dict_layout(self, term_width: int, term_height: int) -> Layout:
        """ Return the dictionary explorer layout """

        # Reset the dict index / window in case applying a filter has now moved the index
        # farther down than it can access on the filtered attributes
        if self.dict_index >= len(self.cached_obj.filtered_dict):
            self.dict_index = max(0, len(self.cached_obj.filtered_dict) - 1)
            self.dict_window = max(
                0, self.dict_index - self.get_panel_height(term_height)
            )

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

        for attr, (line, cached_obj) in list(self.cached_obj.filtered_dict.items())[
            start:end
        ]:
            new_line = line.copy()
            if index == self.dict_index:
                new_line.style = Style(reverse=True)

            new_line.truncate(panel_width)
            lines.append(new_line)
            index += 1

        lines.append(Text("}"))

        text = Text("\n").join(lines)

        self.update(
            Panel(
                text,
                title="[i][cyan]dict[/cyan]()",
                title_align="right",
                subtitle=f"([magenta]{self.dict_index + 1}[/magenta]/[magenta]{len(self.cached_obj.filtered_dict)}[/magenta])",
                subtitle_align="right",
                style="white",
            )
        )
        return self

    def list_layout(self, term_width: int, term_height: int) -> Layout:

        # Reset the list index / window in case applying a filter has now moved the index
        # farther down than it can access on the filtered attributes
        if self.list_index >= len(self.cached_obj.filtered_list):
            self.list_index = max(0, len(self.cached_obj.filtered_list) - 1)
            self.list_window = max(
                0, self.list_index - self.get_panel_height(term_height)
            )

        panel_width = self.get_panel_width(term_width)
        panel_height = self.get_panel_height(term_height)
        lines = []

        type_map = {
            ExplorerState.list: ["[", "]", "list"],
            ExplorerState.tuple: ["(", ")", "tuple"],
            ExplorerState.set: ["{", "}", "set"],
        }

        if self.list_window == 0:
            lines.append(Text(type_map[self.state][0]))
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

        for line, cached_obj in self.cached_obj.filtered_list[start:end]:
            new_line = line.copy()

            if index == self.list_index:
                new_line.style = Style(reverse=True)

            new_line.truncate(panel_width)
            lines.append(new_line)
            index += 1

        lines.append(Text(type_map[self.state][1]))

        text = Text("\n").join(lines)

        self.update(
            Panel(
                text,
                title=f"[i][cyan]{type_map[self.state][2]}[/cyan]()",
                title_align="right",
                subtitle=f"([magenta]{self.list_index + 1}[/magenta]/[magenta]{len(self.cached_obj.filtered_list)}[/magenta])",
                subtitle_align="right",
                style="white",
            )
        )
        return self

    def dir_layout(self, term_width: int, term_height: int) -> Layout:
        lines = []
        panel_width = self.get_panel_width(term_width)

        if self.state == ExplorerState.public:
            # Reset the public index / window in case applying a filter has now moved the index
            # farther down than it can access on the filtered attributes
            if self.public_index >= len(self.cached_obj.filtered_public_attributes):
                self.public_index = max(
                    0, len(self.cached_obj.filtered_public_attributes) - 1
                )
                self.public_window = max(
                    0, self.public_index - self.get_panel_height(term_height)
                )

            for index, (attr, cached_obj) in enumerate(
                self.cached_obj.filtered_public_attributes.items()
            ):
                line = cached_obj.text.copy()
                if index == self.public_index:
                    line.style += Style(reverse=True)  # type: ignore

                # dim_typeof = cached_obj.typeof.copy()
                # dim_typeof.style = Style(dim=True)
                # line = (
                #     line
                #     + Text(" " * max(2, panel_width - (len(line) + len(cached_obj.typeof))))
                #     + dim_typeof
                # )

                line.truncate(panel_width)
                lines.append(line)

            title = "[i][cyan]dir[/cyan]()[/i] | [u]public[/u] [dim]private[/dim]"
            subtitle = (
                "[dim][u][][/u]:switch pane [/dim]"
                f"[white]([/white][magenta]{self.public_index + 1 if self.cached_obj.filtered_public_attributes else 0}"
                f"[/magenta][white]/[/white][magenta]{len(self.cached_obj.filtered_public_attributes)}[/magenta][white])"
            )
            if lines == []:
                lines.append(
                    Text("No public attributes", style=Style(color="red", italic=True))
                )

            renderable = Text("\n").join(
                lines[self.public_window : self.public_window + term_height]
            )

        elif self.state == ExplorerState.private:
            # Reset the private index / window in case applying a filter has now moved the index
            # farther down than it can access on the filtered attributes
            if self.private_index >= len(self.cached_obj.filtered_private_attributes):
                self.private_index = max(
                    0, len(self.cached_obj.filtered_private_attributes) - 1
                )
                self.private_window = max(
                    0, self.private_index - self.get_panel_height(term_height)
                )

            for index, (attr, cached_obj) in enumerate(
                self.cached_obj.filtered_private_attributes.items()
            ):
                line = cached_obj.text.copy()
                if index == self.private_index:
                    line.style += Style(reverse=True)  # type: ignore

                # TODO add a toggle able feature for this
                # dim_typeof = cached_obj.typeof.copy()
                # dim_typeof.style = Style(dim=True)
                # line = (
                #     line
                #     + Text(" " * max(2, panel_width - (len(line) + len(cached_obj.typeof))))
                #     + dim_typeof
                # )

                line.truncate(panel_width)
                lines.append(line)

            title = "[i][cyan]dir[/cyan]()[/i] | [dim]public[/dim] [u]private[/u]"
            subtitle = (
                "[dim][u][][/u]:switch pane [/dim]"
                f"[white]([/white][magenta]{self.private_index + 1 if self.cached_obj.filtered_private_attributes else 0}"
                f"[/magenta][white]/[/white][magenta]{len(self.cached_obj.filtered_private_attributes)}[/magenta][white])"
            )
            if lines == []:
                lines.append(
                    Text("No private attributes", style=Style(color="red", italic=True))
                )

            renderable = Text("\n").join(
                lines[self.private_window : self.private_window + term_height]
            )

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

        elif self.state in (ExplorerState.list, ExplorerState.tuple, ExplorerState.set):
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
            if self.dict_index < len(cached_obj.filtered_dict.keys()) - 1:
                self.dict_index += 1
                if self.dict_index > self.dict_window + panel_height - 1:
                    self.dict_window += 1
            elif (
                self.dict_window == len(cached_obj.filtered_dict.keys()) - panel_height
            ):
                self.dict_window += 1

        elif self.state in (ExplorerState.list, ExplorerState.tuple, ExplorerState.set):
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

        elif self.state in (ExplorerState.list, ExplorerState.tuple, ExplorerState.set):
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

        elif self.state in (ExplorerState.list, ExplorerState.tuple, ExplorerState.set):
            self.list_index = len(cached_obj.obj) - 1
            self.list_window = max(0, self.list_index - panel_height + 2)
