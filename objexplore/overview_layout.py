
from typing import Optional
from rich.panel import Panel
from rich.pretty import Pretty
from rich.layout import Layout
from .cached_object import CachedObject


class OverviewState:
    all, docstring, value = range(3)

class ValueState:
    repr, source = range(2)


class OverviewLayout(Layout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = OverviewState.all
        self.value_state = ValueState.repr

    def __call__(self, cached_obj: CachedObject, term_height: int) -> Layout:
        if self.state == OverviewState.docstring:
            return Layout(
                self.get_docstring_panel(
                    cached_obj=cached_obj,
                    term_height=term_height,
                    fullscreen=True
                ),
                ratio=3
            )

        elif self.state == OverviewState.value:
            return Layout(self.get_value_panel(cached_obj, term_height), ratio=3)

        else:
            layout = Layout(ratio=3)
            layout.split_column(
                Layout(
                    self.get_value_panel(cached_obj, term_height),
                    name="obj_value"
                ),
                Layout(
                    self.get_type_panel(cached_obj),
                    name="obj_type",
                    size=3
                ),
                Layout(
                    self.get_docstring_panel(cached_obj),
                    name="obj_doc",
                )
            )
            return layout

    def get_value_panel(self, cached_obj: CachedObject, term_height: int):
        if self.value_state == ValueState.repr:
            title="[i]preview[/i] | [cyan]repr[/cyan]() [dim]source"

        elif self.value_state == ValueState.source:
            title="[i]preview[/i] | [dim][cyan]repr[/cyan]()[/dim] source"

        if self.state == OverviewState.all:
            renderable = Pretty(cached_obj.obj, max_length=term_height // 3)
        elif self.state == OverviewState.value:
            renderable = Pretty(cached_obj.obj, max_length=term_height - 8)

        return Panel(
            renderable,
            title=title,
            title_align="left",
            style="white"
        )

    def get_type_panel(self, cached_obj: CachedObject):
        return Panel(
            cached_obj.typeof,
            title="[i][cyan]type[/cyan]()[/i]",
            title_align="left",
            style="white"
        )

    def get_docstring_panel(self, cached_obj: CachedObject, term_height: Optional[int] = None, fullscreen: bool = False) -> Panel:
        """ Build the docstring panel """
        title = "[i]docstring"
        docstring = '\n'.join(cached_obj.docstring.splitlines()[:term_height])
        if fullscreen:
            return Panel(
                docstring,
                title=title,
                title_align="left",
                subtitle="[dim][u]f[/u]:fullscreen [u]d[/u]:toggle",
                subtitle_align="left",
                style="white",
            )
        else:
            # Only need to show the lines of the docstring that would be visible by
            # the terminal
            return Panel(
                docstring,
                title=title,
                title_align="left",
                subtitle="[dim][u]d[/u]:toggle",
                subtitle_align="left",
                style="white"
            )
