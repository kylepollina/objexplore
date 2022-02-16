from typing import Union

from blessed import Terminal
from rich.layout import Layout
from rich.panel import Panel
from rich.pretty import Pretty
from rich.style import Style
from rich.syntax import Syntax
from rich.text import Text

from .cached_object import CachedObject
from .help_layout import HelpLayout
from .config import box_type


class OverviewState:
    all, docstring, value = range(3)


class PreviewState:
    repr, source = range(2)


class Overview:
    def __init__(self, term: Terminal, version: str):
        self.term = term
        self.layout = Layout()
        self.help_layout = HelpLayout(version, visible=False, ratio=3)
        self.state = OverviewState.all
        self.preview_state = PreviewState.repr

    @property
    def layout_width(self):
        return (self.term.width - 2) // 4 * 3

    def get_layout(self, cached_obj: CachedObject) -> Layout:
        """
        :param cached_obj: The selected cached object given by the explorer layout
        """
        if self.help_layout.visible:
            return self.help_layout(self.term.height)

        elif self.state == OverviewState.docstring:
            self.layout.update(
                self.get_docstring_panel(
                    cached_obj=cached_obj,
                    term_height=self.term.height,
                )
            )
            return self.layout

        elif self.state == OverviewState.value:
            self.layout.update(self.get_value_panel(cached_obj))
            return self.layout

        elif self.state == OverviewState.all:
            layout = Layout()
            layout.split_column(
                Layout(self.get_value_panel(cached_obj)),
                self.get_info_layout(cached_obj),
                Layout(
                    self.get_docstring_panel(
                        cached_obj=cached_obj, term_height=self.term.height
                    ),
                ),
            )
            return layout
        else:
            raise ValueError("Unexpected overview state")

    def get_value_panel(self, cached_obj: CachedObject):
        renderable: Union[str, Pretty, Syntax]
        if not callable(cached_obj.obj):
            title = "[i]preview[/i] | [i][cyan]repr[/cyan]()[/i]"
            subtitle = "[dim][u]p[/u]:toggle [u]f[/u]:fullscreen [u]{}[/u]:switch pane"
            renderable = cached_obj.pretty

            if self.state == OverviewState.all:
                renderable.max_length = max((self.term.height - 6) // 2 - 7, 1)
            else:
                renderable.max_length = max(self.term.height - 9, 1)

        else:
            if self.preview_state == PreviewState.repr:
                renderable = cached_obj.pretty
                title = "[i]preview[/i] | [i][cyan]repr[/cyan]()[/i] [dim]source"

            if self.preview_state == PreviewState.source:
                renderable = cached_obj.get_source(self.term.height)
                title = (
                    "[i]preview[/i] | [dim][cyan]repr[/cyan]()[/dim] [underline]source"
                )

            subtitle = "[dim][u]p[/u]:toggle [u]f[/u]:fullscreen [u]{}[/u]:switch pane"

        return Panel(
            renderable,
            title=title,
            title_align="left",
            subtitle=subtitle,
            subtitle_align="left",
            style=Style(color="white"),
            box=box_type,
        )

    def get_info_layout(self, cached_obj: CachedObject):
        if cached_obj.length is not None:
            layout = Layout(size=3)
            layout.split_row(
                Layout(self.get_type_panel(cached_obj)),
                Layout(
                    Panel(
                        str(cached_obj.length),
                        title="[i][cyan]len[/cyan]()[/i]",
                        title_align="left",
                        style="white",
                        box=box_type,
                    )
                ),
            )
            return layout

        else:
            return self.get_type_panel(cached_obj)

    def get_type_panel(self, cached_obj: CachedObject):
        return Layout(
            Panel(
                cached_obj.typeof,
                title="[i][cyan]type[/cyan]()[/i]",
                title_align="left",
                style="white",
                box=box_type,
            ),
            size=3,
        )

    def get_docstring_panel(
        self,
        cached_obj: CachedObject,
        term_height: int,
    ) -> Panel:
        """ Build the docstring panel """
        title = "[i]docstring"
        if self.state == OverviewState.docstring:
            subtitle = "[dim][u]d[/u]:toggle [u]f[/u]:fullscreen"
        else:
            subtitle = "[dim][u]d[/u]:toggle"
        docstring = Text("\n").join(cached_obj.docstring_lines[:term_height])
        return Panel(
            docstring,
            title=title,
            title_align="left",
            subtitle=subtitle,
            subtitle_align="left",
            style="white",
            box=box_type,
        )
