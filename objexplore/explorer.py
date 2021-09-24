from typing import Any, Dict, Optional, Union

from blessed import Terminal
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from .cached_object import CachedObject
from .filter import Filter
from .stack import Stack, StackFrame

console = Console()


# TODO fix truncating bug when width = 111
# TODO hide filter/stack/explorere subtitle if screen too small


class ExplorerState:
    public = "ExplorerState.public"
    private = "ExplorerState.private"
    dict = "ExplorerState.dict"
    list = "ExplorerState.list"
    tuple = "ExplorerState.tuple"
    set = "ExplorerState.set"


highlighter = ReprHighlighter()


class Explorer:
    """
    Class representing the explorer object on the left hand side
    This class contains references to the filter and stack objects

    ┌──────────┐ ┌──────────────────┐
    │          │ │                  │
    │          │ │                  │
    │ Explorer │ │     Overview     │
    │ (Filter) │ │                  │
    │ (Stack)  │ │                  │
    └──────────┘ └──────────────────┘
    """

    def __init__(
        self,
        term: Terminal,
        current_obj: CachedObject,
        filter: Optional[Filter] = None,
        stack: Optional[Stack] = None,
        state: Optional[ExplorerState] = None,
        public_index: int = 0,
        public_window: int = 0,
        private_index: int = 0,
        private_window: int = 0,
        dict_index: int = 0,
        dict_window: int = 0,
        list_index: int = 0,
        list_window: int = 0,
    ):
        self.term = term
        self.filter = Filter(term=self.term) if not filter else filter
        self.stack = (
            Stack(head_obj=current_obj, explorer=self, filter=self.filter)
            if not stack
            else stack
        )
        self.layout = Layout()
        self.public_index = public_index
        self.public_window = public_window
        self.private_index = private_index
        self.private_window = private_window
        self.dict_index = dict_index
        self.dict_window = dict_window
        self.list_index = list_index
        self.list_window = list_window

        if state:
            self.state = state
        else:
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

    def get_layout(self) -> Layout:
        """ Return the layout of the object explorer. This will be a list of lines representing the object attributes/keys/vals we are exploring """

        if self.state == ExplorerState.dict:
            explorer_layout = self.dict_layout(self.term.width, self.term.height)

        elif self.state in (ExplorerState.list, ExplorerState.tuple, ExplorerState.set):
            explorer_layout = self.list_layout(self.term.width, self.term.height)

        else:
            explorer_layout = self.dir_layout()

        if self.filter.layout.visible:
            layout = Layout()
            layout.split_column(
                explorer_layout, self.filter.get_layout(width=self.width)
            )
            return layout
        elif self.stack.layout.visible:
            layout = Layout()
            layout.split_column(
                explorer_layout, self.stack.get_layout(width=self.width)
            )
            return layout
        else:
            return explorer_layout

    def dir_layout(self) -> Layout:
        lines = []

        if self.state == ExplorerState.public:
            # Reset the public index / window in case applying a filter has now moved the index
            # farther down than it can access on the filtered attributes
            if self.public_index >= len(self.cached_obj.filtered_public_attributes):
                self.public_index = max(
                    0, len(self.cached_obj.filtered_public_attributes) - 1
                )
                self.public_window = max(0, self.public_index - self.height)

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

                line.truncate(self.width)
                lines.append(line)

            title = "[i][cyan]dir[/cyan]()[/i] | [u]public[/u] [dim]private[/dim]"
            subtitle_help = "[dim][u][][/u]:switch pane [/dim]"
            subtitle_index = (
                f"[white]([/white][magenta]{self.public_index + 1 if self.cached_obj.filtered_public_attributes else 0}"
                f"[/magenta][white]/[/white][magenta]{len(self.cached_obj.filtered_public_attributes)}[/magenta][white])"
            )
            if (
                len(console.render_str(subtitle_help + subtitle_index))
                >= self.width - 2
            ):
                subtitle = subtitle_index
            else:
                subtitle = subtitle_help + subtitle_index
            if lines == []:
                lines.append(
                    Text("No public attributes", style=Style(color="red", italic=True))
                )

            renderable = Text("\n").join(
                lines[self.public_window : self.public_window + self.height + 1]
            )

        elif self.state == ExplorerState.private:
            # Reset the private index / window in case applying a filter has now moved the index
            # farther down than it can access on the filtered attributes
            if self.private_index >= len(self.cached_obj.filtered_private_attributes):
                self.private_index = max(
                    0, len(self.cached_obj.filtered_private_attributes) - 1
                )
                self.private_window = max(0, self.private_index - self.height)

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

                line.truncate(self.width)
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
                lines[self.private_window : self.private_window + self.height]
            )

        # If terminal is too small don't show the 'dir()' part of the title
        if self.width < len(console.render_str(title)) + 3:
            title = title.split("|")[-1].strip()

        self.layout.update(
            Panel(
                renderable,
                title=title,
                title_align="right",
                subtitle=subtitle,
                subtitle_align="right",
                style="white",
            )
        )
        return self.layout

    def dict_layout(self) -> Layout:
        """ Return the dictionary explorer layout """

        # Reset the dict index / window in case applying a filter has now moved the index
        # farther down than it can access on the filtered attributes
        if self.dict_index >= len(self.cached_obj.filtered_dict):
            self.dict_index = max(0, len(self.cached_obj.filtered_dict) - 1)
            self.dict_window = max(0, self.dict_index - self.height)

        lines = []

        if self.dict_window == 0:
            lines.append(Text("{"))
            start = 0
            num_lines = self.height - 1
        elif self.dict_window == 1:
            start = 0
            num_lines = self.height
        else:
            start = self.dict_window - 1
            num_lines = self.height

        end = start + num_lines
        index = start

        for attr, (line, cached_obj) in list(self.cached_obj.filtered_dict.items())[
            start:end
        ]:
            new_line = line.copy()
            if index == self.dict_index:
                new_line.style = Style(reverse=True)

            new_line.truncate(self.width)
            lines.append(new_line)
            index += 1

        lines.append(Text("}"))

        text = Text("\n").join(lines)

        self.layout.update(
            Panel(
                text,
                title="[i][cyan]dict[/cyan]()",
                title_align="right",
                subtitle=f"([magenta]{self.dict_index + 1}[/magenta]/[magenta]{len(self.cached_obj.filtered_dict)}[/magenta])",
                subtitle_align="right",
                style="white",
            )
        )
        return self.layout

    def list_layout(self, term_width: int, term_height: int) -> Layout:
        # Reset the list index / window in case applying a filter has now moved the index
        # farther down than it can access on the filtered attributes
        if self.list_index >= len(self.cached_obj.filtered_list):
            self.list_index = max(0, len(self.cached_obj.filtered_list) - 1)
            self.list_window = max(
                0, self.list_index - self.get_panel_height(term_height)
            )

        panel_height = self.get_panel_height(term_height)
        lines = []

        bracket_map = {
            ExplorerState.list: ["[", "]", "list"],
            ExplorerState.tuple: ["(", ")", "tuple"],
            ExplorerState.set: ["{", "}", "set"],
        }

        if self.list_window == 0:
            lines.append(Text(bracket_map[self.state][0]))
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

            new_line.truncate(self.width)
            lines.append(new_line)
            index += 1

        lines.append(Text(bracket_map[self.state][1]))

        text = Text("\n").join(lines)

        self.layout.update(
            Panel(
                text,
                title=f"[i][cyan]{bracket_map[self.state][2]}[/cyan]()",
                title_align="right",
                subtitle=f"([magenta]{self.list_index + 1}[/magenta]/[magenta]{len(self.cached_obj.filtered_list)}[/magenta])",
                subtitle_align="right",
                style="white",
            )
        )
        return self.layout

    def explore_selected_object(self) -> CachedObject:
        """ TODO """
        self.cached_obj = self.selected_object
        self.cached_obj.cache()
        self.public_index = self.private_index = 0
        self.public_window = self.private_window = 0
        self.filter = Filter(term=self.term)
        self.stack.push(
            cached_obj=self.cached_obj, explorer=self.copy(), filter=self.filter
        )
        return self.cached_obj

    def explore_parent_obj(self):
        """ Go back to exploring the parent obj of the current obj """
        stack_frame = self.stack.pop()
        if stack_frame:
            explorer = stack_frame.explorer
            self.filter = stack_frame.filter
            self.state = explorer.state
            self.public_index = explorer.public_index
            self.private_index = explorer.private_index
            self.public_window = explorer.public_window
            self.private_window = explorer.private_window
            self.dict_index = explorer.dict_index
            self.list_index = explorer.list_index

            self.cached_obj = self.stack[-1].cached_obj
        return self.cached_obj

    def explore_selected_stack_object(self):
        stack_frame = self.stack.select()
        if stack_frame:
            explorer = stack_frame.explorer
            self.term = explorer.term
            self.cached_obj = explorer.cached_obj
            self.filter = stack_frame.filter
            self.state = explorer.state
            self.public_index = explorer.public_index
            self.private_index = explorer.private_index
            self.public_window = explorer.public_window
            self.private_window = explorer.private_window
            self.dict_index = explorer.dict_index
            self.list_index = explorer.list_index

            self.stack.push(
                cached_obj=self.cached_obj, explorer=self.copy(), filter=self.filter
            )

        return self.cached_obj

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

    @property
    def width(self):
        """ Return the width of text allowed within the panel """
        return (self.term.width - 2) // 4 - 4

    @property
    def height(self):
        return self.term.height - 6

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

    def move_down(self, cached_obj: CachedObject):
        """ Move the current selection down one """
        if self.state == ExplorerState.public:
            if self.public_index < len(cached_obj.filtered_public_attributes) - 1:
                self.public_index += 1
                if self.public_index > self.public_window + self.height:
                    self.public_window += 1

        elif self.state == ExplorerState.private:
            if self.private_index < len(cached_obj.filtered_private_attributes) - 1:
                self.private_index += 1
                if self.private_index > self.private_window + self.height:
                    self.private_window += 1

        elif self.state == ExplorerState.dict:
            if self.dict_index < len(cached_obj.filtered_dict.keys()) - 1:
                self.dict_index += 1
                if self.dict_index > self.dict_window + self.height - 1:
                    self.dict_window += 1
            elif self.dict_window == len(cached_obj.filtered_dict.keys()) - self.height:
                self.dict_window += 1

        elif self.state in (ExplorerState.list, ExplorerState.tuple, ExplorerState.set):
            if self.list_index < len(cached_obj.obj) - 1:
                self.list_index += 1
                if self.list_index > self.list_window + self.height - 1:
                    self.list_window += 1
            elif self.list_window == len(cached_obj.obj) - self.height:
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

    def move_bottom(self, cached_obj: CachedObject):
        if self.state == ExplorerState.public:
            self.public_index = len(cached_obj.filtered_public_attributes) - 1
            self.public_window = max(0, self.public_index - self.height)

        elif self.state == ExplorerState.private:
            self.private_index = len(cached_obj.filtered_private_attributes) - 1
            self.private_window = max(0, self.private_index - self.height)

        elif self.state == ExplorerState.dict:
            self.dict_index = len(cached_obj.obj.keys()) - 1
            self.dict_window = max(0, self.dict_index - self.height + 2)

        elif self.state in (ExplorerState.list, ExplorerState.tuple, ExplorerState.set):
            self.list_index = len(cached_obj.obj) - 1
            self.list_window = max(0, self.list_index - self.height + 2)

    def copy(self):
        return Explorer(
            term=self.term,
            cached_obj=self.cached_obj,
            filter=self.filter,
            stack=self.stack,
            state=self.state,
            public_index=self.public_index,
            public_window=self.public_window,
            private_index=self.private_index,
            private_window=self.private_window,
            dict_index=self.dict_index,
            dict_window=self.dict_window,
            list_index=self.list_index,
            list_window=self.list_window,
        )

    # TODO refactor this
    def get_all_attributes(self) -> Union[Dict[str, CachedObject], Any]:
        if self.state == ExplorerState.public:
            return self.cached_obj.public_attributes
        elif self.state == ExplorerState.private:
            return self.cached_obj.private_attributes
        else:
            return self.cached_obj.obj
