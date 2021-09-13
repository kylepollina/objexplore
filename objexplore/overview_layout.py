
from typing import Optional
from rich.panel import Panel
from rich.pretty import Pretty
from rich.layout import Layout
from .cached_object import CachedObject


class OverviewState:
    all, docstring, value = range(3)

class PreviewState:
    repr, source = range(2)


class OverviewLayout(Layout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = OverviewState.all
        self.preview_state = PreviewState.repr

    def __call__(self, cached_obj: CachedObject, term_height: int, console) -> Layout:
        if self.state == OverviewState.docstring:
            return Layout(
                self.get_docstring_panel(
                    cached_obj=cached_obj,
                    console=console,
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
                    self.get_docstring_panel(cached_obj, console),
                    name="obj_doc",
                )
            )
            return layout

    def get_value_panel(self, cached_obj: CachedObject, term_height: int):
        if cached_obj.is_callable:
            if self.preview_state == PreviewState.repr:
                title = "[i]preview[/i] | [u][cyan]repr[/cyan]()[/u] [dim]source"
                renderable = cached_obj.obj

                if self.state == OverviewState.all:
                    renderable = Pretty(renderable, max_length=(max((term_height - 6) // 2 - 7, 1)))
                else:
                    renderable = Pretty(renderable, max_length=(max(term_height - 9, 1)))

            elif self.preview_state == PreviewState.source:
                title = "[i]preview[/i] | [dim][cyan]repr[/cyan]()[/dim] [u]source[/u]"
                renderable = cached_obj.get_source(term_height)
            else:
                pass

            subtitle = "[dim][u]f[/u]:fullscreen [u]p[/u]:toggle [u]{}[/u]:switch pane"

        else:
            title = "[i]preview[/i] | [u][cyan]repr[/cyan]()[/u]"
            subtitle = "[dim][u]f[/u]:fullscreen [u]p[/u]:toggle"
            renderable = cached_obj.obj

            if self.state == OverviewState.all:
                renderable = Pretty(renderable, max_length=(max((term_height - 6) // 2 - 7, 1)))
            else:
                renderable = Pretty(renderable, max_length=(max(term_height - 9, 1)))

        return Panel(
            renderable,
            title=title,
            title_align="left",
            subtitle=subtitle,
            subtitle_align="left",
            style="white"
        )

    def get_type_panel(self, cached_obj: CachedObject):
        return Panel(
            cached_obj.typeof,
            title="[i]info[/i] | [u][cyan]type[/cyan]()[/u]",
            title_align="left",
            style="white"
        )

    def get_docstring_panel(self, cached_obj: CachedObject, console, term_height: Optional[int] = None, fullscreen: bool = False) -> Panel:
        """ Build the docstring panel """
        title = "[i]docstring"
        docstring = console.render_str('\n'.join(cached_obj.docstring.splitlines()[:term_height]))
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
