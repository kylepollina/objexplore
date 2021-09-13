
from typing import Optional
from rich.panel import Panel
from rich.pretty import Pretty
from rich.layout import Layout
from .cached_object import CachedObject


class PreviewState:
    all, docstring, value = range(3)

class ValueState:
    repr, source = range(2)


class PreviewLayout(Layout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = PreviewState.all
        self.value_state = ValueState.repr

    def __call__(self, cached_obj: CachedObject, term_height: int) -> Layout:
        if self.state == PreviewState.docstring:
            return Layout(
                self.get_docstring_panel(
                    cached_obj=cached_obj,
                    term_height=term_height,
                    fullscreen=True
                ),
                ratio=3
            )

        elif self.state == PreviewState.value:
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

        if self.state == PreviewState.all:
            renderable = Pretty(cached_obj.obj, max_length=term_height // 3)
        elif self.state == PreviewState.value:
            renderable = Pretty(cached_obj.obj, max_length=term_height - 8)

        return Panel(
            renderable,
            title=title,
            title_align="left",
            style="white"
        )

        # return Panel(
        #     "hello",
        #     title="[i]preview[/i] | [dim]value source",
        #     title_align="left",
        #     subtitle="[dim][u]v[/u]:toggle [u]{}[/u]:switch pane",
        #     subtitle_align="left",
        #     style="white"
        # )


    # def get_value_panel(self):
    #     return Panel(
    #         self.value_panel_text(),
    #         title=(
    #             "[u]value[/u]"
    #             if not self.cached_obj.selected_cached_obj or not callable(self.cached_obj.selected_cached_obj.obj)
    #             else (
    #                 "[u]value[/u] [dim]source[/dim]"
    #                 if self.preview_layout.state != PreviewState.source
    #                 else "[dim]value[/dim] [u]source[/u]"
    #             )
    #         ),
    #         title_align="left",
    #         subtitle=f"[dim][u]f[/u]:fullscreen [u]v[/u]:toggle{' [u]{}[/u]:switch pane' if self.cached_obj.selected_cached_obj and callable(self.cached_obj.selected_cached_obj.obj) else ''}",
    #         subtitle_align="left",
    #         style="white"
    #     )

    # def value_panel_text(self, fullscreen=False):
    #     # sometimes the current obj will have no public/private attributes in which selected_cached_obj
    #     # will be `None`
    #     if self.cached_obj.selected_cached_obj:
    #         return (
    #             self.cached_obj.selected_cached_obj.get_preview(self.term, fullscreen)
    #             if not callable(self.cached_obj.selected_cached_obj.obj)
    #             else (
    #                 self.cached_obj.selected_cached_obj.get_preview(self.term, fullscreen)
    #                 if self.preview_layout.state == PreviewState.value
    #                 else self.cached_obj.selected_cached_obj.get_source(self.term, fullscreen)
    #             )
    #         )
    #     # if that is the case then return an empty string
    #     else:
    #         return ""


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
