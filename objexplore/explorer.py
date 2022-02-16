from typing import Optional

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
from .config import box_type

console = Console()

highlighter = ReprHighlighter()


class ExplorerState:
    public = "ExplorerState.public"
    private = "ExplorerState.private"
    dict = "ExplorerState.dict"
    list = "ExplorerState.list"
    tuple = "ExplorerState.tuple"
    set = "ExplorerState.set"


def get_state(cached_obj: CachedObject):
    if isinstance(cached_obj.obj, dict):
        return ExplorerState.dict
    elif isinstance(cached_obj.obj, list):
        return ExplorerState.list
    elif isinstance(cached_obj.obj, tuple):
        return ExplorerState.tuple
    elif isinstance(cached_obj.obj, set):
        return ExplorerState.set
    else:
        return ExplorerState.public


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
        cached_obj: CachedObject,
        term: Terminal,
        filter: Optional[Filter] = None,
        stack: Optional[Stack] = None,
        state: Optional[str] = None,
        public_index: int = 0,
        public_window: int = 0,
        private_index: int = 0,
        private_window: int = 0,
        dict_index: int = 0,
        dict_window: int = 0,
        list_index: int = 0,
        list_window: int = 0,
    ):
        self.cached_obj = cached_obj
        self.term = term
        self.filter = Filter(term=self.term) if not filter else filter
        self.stack = Stack(head_obj=cached_obj) if not stack else stack
        self.public_index = public_index
        self.public_window = public_window
        self.private_index = private_index
        self.private_window = private_window
        self.dict_index = dict_index
        self.dict_window = dict_window
        self.list_index = list_index
        self.list_window = list_window
        self.extra_width = 0

        if state:
            self.state = state
        else:
            self.state = get_state(self.cached_obj)

    def get_layout(self) -> Layout:
        """ Return the layout of the object explorer. This will be a list of lines representing the object attributes/keys/vals we are exploring """
        explorer_layout = Layout(size=self.layout_width)

        if self.state == ExplorerState.dict:
            top_panel = self.dict_panel

        elif self.state in (ExplorerState.list, ExplorerState.tuple, ExplorerState.set):
            top_panel = self.list_panel

        else:
            top_panel = self.dir_panel

        if self.filter.layout.visible:
            combined_layout = Layout()
            combined_layout.split_column(
                top_panel, self.filter.get_layout(self.text_width)
            )
            explorer_layout.update(combined_layout)
        elif self.stack.layout.visible:
            combined_layout = Layout()
            combined_layout.split_column(
                top_panel,
                self.stack.get_layout(
                    width=self.text_width, current_obj=self.cached_obj
                ),
            )
            explorer_layout.update(combined_layout)
        else:
            explorer_layout.update(top_panel)

        return explorer_layout

    @property
    def dir_panel(self) -> Panel:
        lines = []

        if self.state == ExplorerState.public:
            # Reset the public index / window in case applying a filter has now moved the index
            # farther down than it can access on the filtered attributes
            if self.public_index >= len(self.cached_obj.filtered_public_attributes):
                self.public_index = max(
                    0, len(self.cached_obj.filtered_public_attributes) - 1
                )
                self.public_window = max(0, self.public_index - self.num_lines)

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

                line.truncate(self.text_width)
                lines.append(line)

            title = "[i][cyan]dir[/cyan]()[/i] | [u]public[/u] [dim]private[/dim]"
            subtitle_help = "[dim][u][][/u]:switch pane [/dim]"
            subtitle_index = (
                f"[white]([/white][magenta]{self.public_index + 1 if self.cached_obj.filtered_public_attributes else 0}"
                f"[/magenta][white]/[/white][magenta]{len(self.cached_obj.filtered_public_attributes)}[/magenta][white])"
            )
            if (
                len(console.render_str(subtitle_help + subtitle_index))
                >= self.text_width - 2
            ):
                subtitle = subtitle_index
            else:
                subtitle = subtitle_help + subtitle_index
            if lines == []:
                lines.append(
                    Text("No public attributes", style=Style(color="red", italic=True))
                )

            lines = lines[self.public_window : self.public_window + self.num_lines + 1]

        elif self.state == ExplorerState.private:
            # Reset the private index / window in case applying a filter has now moved the index
            # farther down than it can access on the filtered attributes
            if self.private_index >= len(self.cached_obj.filtered_private_attributes):
                self.private_index = max(
                    0, len(self.cached_obj.filtered_private_attributes) - 1
                )
                self.private_window = max(0, self.private_index - self.num_lines)

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

                line.truncate(self.text_width)
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

            lines = lines[self.private_window : self.private_window + self.num_lines]

        if self.num_hidden_attributes:
            num_filtered_line = (
                Text(
                    "+",
                    style=Style(color="white", dim=True, italic=True, underline=True),
                )
                + Text(
                    str(self.num_hidden_attributes),
                    style=Style(color="cyan", dim=True, italic=True),
                )
                + Text(" filtered", style=Style(color="white", dim=True, italic=True))
            )
            num_filtered_line.truncate(self.text_width)
            lines.append(num_filtered_line)

        renderable = Text("\n").join(lines)

        # If terminal is too small don't show the 'dir()' part of the title
        if self.text_width < len(console.render_str(title)) + 3:
            title = title.split("|")[-1].strip()
        if len(console.render_str(title)) > self.text_width:
            if self.state == ExplorerState.public:
                title = "[u]public"
            elif self.state == ExplorerState.private:
                title = "[u]private"

        return Panel(
            renderable,
            title=title,
            title_align="right",
            subtitle=subtitle,
            subtitle_align="right",
            style="white",
            box=box_type,
        )

    @property
    def dict_panel(self) -> Panel:
        """ Return the dictionary explorer layout """

        # Reset the dict index / window in case applying a filter has now moved the index
        # farther down than it can access on the filtered attributes
        if self.dict_index >= len(self.cached_obj.filtered_dict):
            self.dict_index = max(0, len(self.cached_obj.filtered_dict) - 1)
            self.dict_window = max(0, self.dict_index - self.num_lines)

        lines = []

        if self.dict_window == 0:
            lines.append(Text("{"))
            start = 0
            num_lines = self.num_lines - 1
        elif self.dict_window == 1:
            start = 0
            num_lines = self.num_lines
        else:
            start = self.dict_window - 1
            num_lines = self.num_lines

        end = start + num_lines
        index = start

        for attr, (line, cached_obj) in list(self.cached_obj.filtered_dict.items())[
            start:end
        ]:
            new_line = line.copy()
            if index == self.dict_index:
                new_line.style = Style(reverse=True)

            new_line.truncate(self.text_width)
            lines.append(new_line)
            index += 1

        if len(lines) == 1:
            lines[0] = Text("{}")
        else:
            lines.append(Text("}"))
        if self.num_hidden_attributes:
            num_filtered_line = (
                Text(
                    "+",
                    style=Style(color="white", dim=True, italic=True, underline=True),
                )
                + Text(
                    str(self.num_hidden_attributes),
                    style=Style(color="cyan", dim=True, italic=True),
                )
                + Text(" filtered", style=Style(color="white", dim=True, italic=True))
            )
            num_filtered_line.truncate(self.text_width)
            lines.append(num_filtered_line)

        text = Text("\n").join(lines)

        return Panel(
            text,
            title="[i][cyan]dict[/cyan]()",
            title_align="right",
            subtitle=f"([magenta]{self.dict_index + 1}[/magenta]/[magenta]{len(self.cached_obj.filtered_dict)}[/magenta])",
            subtitle_align="right",
            style="white",
            box=box_type,
        )

    @property
    def list_panel(self) -> Panel:
        """ TODO """
        # Reset the list index / window in case applying a filter has now moved the index
        # farther down than it can access on the filtered attributes
        if self.list_index >= len(self.cached_obj.filtered_list):
            self.list_index = max(0, len(self.cached_obj.filtered_list) - 1)
            self.list_window = max(0, self.list_index - self.num_lines)

        lines = []

        bracket_map = {
            ExplorerState.list: ["[", "]", "list"],
            ExplorerState.tuple: ["(", ")", "tuple"],
            ExplorerState.set: ["{", "}", "set"],
        }

        if self.list_window == 0:
            lines.append(Text(bracket_map[self.state][0]))
            start = 0
            num_lines = self.num_lines - 1
        elif self.list_window == 1:
            start = 0
            num_lines = self.num_lines
        else:
            start = self.list_window - 1
            num_lines = self.num_lines

        end = start + num_lines
        index = start

        for line, cached_obj in self.cached_obj.filtered_list[start:end]:
            new_line = line.copy()

            if index == self.list_index:
                new_line.style = Style(reverse=True)

            new_line.truncate(self.text_width)
            lines.append(new_line)
            index += 1

        if len(lines) == 1:
            lines[0] = Text("".join(bracket_map[self.state][:-1]))
        else:
            lines.append(Text(bracket_map[self.state][1]))

        if self.num_hidden_attributes:
            num_filtered_line = (
                Text(
                    "+",
                    style=Style(color="white", dim=True, italic=True, underline=True),
                )
                + Text(
                    str(self.num_hidden_attributes),
                    style=Style(color="cyan", dim=True, italic=True),
                )
                + Text(" filtered", style=Style(color="white", dim=True, italic=True))
            )
            num_filtered_line.truncate(self.text_width)
            lines.append(num_filtered_line)

        text = Text("\n").join(lines)

        return Panel(
            text,
            title=f"[i][cyan]{bracket_map[self.state][2]}[/cyan]()",
            title_align="right",
            subtitle=f"([magenta]{self.list_index + 1}[/magenta]/[magenta]{len(self.cached_obj.filtered_list)}[/magenta])",
            subtitle_align="right",
            style="white",
            box=box_type,
        )

    def explore_selected_object(self) -> Optional[CachedObject]:
        """ TODO """

        # Save current stack as a frame
        current_frame = StackFrame(
            cached_obj=self.cached_obj,
            filter=self.filter,
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
        self.stack.push(current_frame)

        self.cached_obj = self.selected_object
        self.cached_obj.cache()
        self.state = get_state(self.cached_obj)
        self.filter = Filter(term=self.term)
        self.public_index = 0
        self.public_window = 0
        self.private_index = 0
        self.private_window = 0
        self.dict_index = 0
        self.dict_window = 0
        self.list_index = 0
        self.list_window = 0

        return None

    def explore_parent_obj(self):
        """ Go back to exploring the parent obj of the current obj """
        stack_frame = self.stack.pop()
        if stack_frame:
            self.cached_obj = stack_frame.cached_obj
            self.filter = stack_frame.filter
            self.state = stack_frame.state
            self.public_index = stack_frame.public_index
            self.public_window = stack_frame.public_window
            self.private_index = stack_frame.private_index
            self.private_window = stack_frame.private_window
            self.dict_index = stack_frame.dict_index
            self.dict_window = stack_frame.dict_window
            self.list_index = stack_frame.list_index
            self.list_window = stack_frame.list_window

        return self.cached_obj

    def explore_selected_stack_object(self):
        stack_frame = self.stack.select()
        if stack_frame:
            self.cached_obj = stack_frame.cached_obj
            self.filter = stack_frame.filter
            self.state = stack_frame.state
            self.public_index = stack_frame.public_index
            self.public_window = stack_frame.public_window
            self.private_index = stack_frame.private_index
            self.private_window = stack_frame.private_window
            self.dict_index = stack_frame.dict_index
            self.dict_window = stack_frame.dict_window
            self.list_index = stack_frame.list_index
            self.list_window = stack_frame.list_window

        return self.cached_obj

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

    def move_down(self):
        """ Move the current selection down one """
        if self.state == ExplorerState.public:
            if self.public_index < self.num_filtered_attributes - 1:
                self.public_index += 1
                if self.public_index >= self.public_window + self.num_lines:
                    self.public_window += 1
            elif (
                self.public_window == self.num_filtered_attributes - self.num_lines + 1
            ):
                self.public_window += 1

        elif self.state == ExplorerState.private:
            if self.private_index < self.num_filtered_attributes - 1:
                self.private_index += 1
                if self.private_index >= self.private_window + self.num_lines:
                    self.private_window += 1
            elif (
                self.private_window == self.num_filtered_attributes - self.num_lines + 1
            ):
                self.private_window += 1

        elif self.state == ExplorerState.dict:
            if self.dict_index < self.num_filtered_attributes - 1:
                self.dict_index += 1
                if self.dict_index >= self.dict_window + self.num_lines - 1:
                    self.dict_window += 1
            elif self.dict_window == self.num_filtered_attributes - self.num_lines + 1:
                self.dict_window += 1
            elif (
                self.dict_window == self.num_filtered_attributes - self.num_lines + 2
                and self.num_hidden_attributes > 0
            ):
                self.dict_window += 1

        elif self.state in (ExplorerState.list, ExplorerState.tuple, ExplorerState.set):
            if self.list_index < self.num_filtered_attributes - 1:
                self.list_index += 1
                if self.list_index >= self.list_window + self.num_lines - 1:
                    self.list_window += 1
            elif self.list_window == self.num_filtered_attributes - self.num_lines + 1:
                self.list_window += 1
            elif (
                self.list_window == self.num_filtered_attributes - self.num_lines + 2
                and self.num_hidden_attributes > 0
            ):
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

    def move_bottom(self):
        """Move all the way to the bottom. If there are hidden attributes, make sure to show that line by
        increasing the window index by 1"""
        if self.state == ExplorerState.public:
            self.public_index = self.num_filtered_attributes - 1
            self.public_window = max(
                0,
                self.public_index
                - self.num_lines
                + (1 if self.num_hidden_attributes == 0 else 2),
            )
        elif self.state == ExplorerState.private:
            self.private_index = self.num_filtered_attributes - 1
            self.private_window = max(
                0,
                self.private_index
                - self.num_lines
                + (1 if self.num_hidden_attributes == 0 else 2),
            )
        elif self.state == ExplorerState.dict:
            self.dict_index = self.num_filtered_attributes - 1
            self.dict_window = max(
                0,
                self.dict_index
                - self.num_lines
                + (3 if self.num_hidden_attributes == 0 else 4),
            )
        elif self.state in (ExplorerState.list, ExplorerState.tuple, ExplorerState.set):
            self.list_index = self.num_filtered_attributes - 1
            self.list_window = max(
                0,
                self.list_index
                - self.num_lines
                + (3 if self.num_hidden_attributes == 0 else 4),
            )

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

    def reset_index(self):
        if self.public_index >= self.num_filtered_attributes:
            self.public_index = self.num_filtered_attributes - 1
            self.public_window = max(0, self.public_index - self.num_lines + 2)
        elif self.public_index < 0:
            self.public_index = 0
        if self.private_index >= self.num_filtered_attributes:
            self.private_index = self.num_filtered_attributes - 1
            self.private_window = max(0, self.private_index - self.num_lines + 2)
        elif self.private_index < 0:
            self.private_index = 0
        if self.dict_index >= self.num_filtered_attributes:
            self.dict_index = self.num_filtered_attributes - 1
            self.dict_window = max(0, self.dict_index - self.num_lines + 4)
        elif self.dict_index < 0:
            self.dict_index = 0
        if self.list_index >= self.num_filtered_attributes:
            self.list_index = self.num_filtered_attributes - 1
            self.list_window = max(0, self.list_index - self.num_lines + 4)
        elif self.list_index < 0:
            self.list_index = 0

    @property
    def num_attributes(self) -> int:
        """ Return the number of attributes of the current cached object """
        if self.state == ExplorerState.public:
            return self.cached_obj.num_public_attributes
        elif self.state == ExplorerState.private:
            return self.cached_obj.num_private_attributes
        else:
            return self.cached_obj.length or 0

    @property
    def num_filtered_attributes(self) -> int:
        """ Return the number of filtered attributes """
        if self.state == ExplorerState.public:
            return self.cached_obj.num_filtered_public_attributes
        elif self.state == ExplorerState.private:
            return self.cached_obj.num_filtered_private_attributes
        elif self.state == ExplorerState.dict:
            return self.cached_obj.num_filtered_dict_keys
        else:
            return self.cached_obj.num_filtered_list_items

    @property
    def num_hidden_attributes(self) -> int:
        return self.num_attributes - self.num_filtered_attributes

    @property
    def num_lines(self):
        return self.term.height - 5

    @property
    def live_update(self) -> bool:
        """True/False value wheter to live update the filters of the cached object
        If the number of visible attributes is over a threshold we do not live update
        the search filter
        """
        return self.num_attributes < 130

    @property
    def selected_object(self) -> CachedObject:
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
                # Get the currently selected key
                key = list(self.cached_obj.filtered_dict)[self.dict_index]
                return self.cached_obj.filtered_dict[key].cached_object

            elif self.state in (
                ExplorerState.list,
                ExplorerState.tuple,
                ExplorerState.set,
            ):
                return self.cached_obj.filtered_list[self.list_index][1]
            else:
                raise ValueError("Unexpected explorer state")

        except (KeyError, IndexError):
            return CachedObject(None)

    @property
    def layout_width(self):
        layout_width = (self.term.width - 2) // 4 + self.extra_width
        if layout_width > self.term.width - 20:
            layout_width = self.term.width - 20
            self.extra_width = 0
        return layout_width

    @property
    def text_width(self):
        """ Return the width of text allowed within the panel """
        return self.layout_width - 4

    def increase_width(self):
        if self.layout_width < self.term.width - 20:
            self.extra_width += 1

    def decrease_width(self):
        if self.layout_width + self.extra_width > 11:
            self.extra_width -= 1
