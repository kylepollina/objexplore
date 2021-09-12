
from random import choice
from textwrap import dedent

from rich.layout import Layout
from rich.panel import Panel


class HelpState:
    keybindings, about = 0, 1


class HelpLayout(Layout):
    def __init__(self, version, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version = version
        self.state = HelpState.keybindings

    def __call__(self):
        self.update(
            Panel(
                self.text,
                title=(
                    "[i white]help[/i white] | [u]key bindings[/u] [dim]about"
                    if self.state == HelpState.keybindings
                    else "[i white]help[/i white] | [dim]key bindings[/dim] [u]about"
                ),
                title_align="left",
                subtitle="[dim white][u]f[/u]:fullscreen [u][][/u]:switch pane [u]?[/u]:exit help",
                subtitle_align="left",
                style="magenta"
            )
        )
        return self

    @property
    def text(self):
        """ Return the text to be displayed on the help page """
        if self.state == HelpState.keybindings:
            return dedent(
                """
                [white]
                      k - [cyan]up[/cyan]
                      j - [cyan]down[/cyan]
                      g - [cyan]go to top[/cyan]
                      G - [cyan]go to bottom[/cyan]
                l Enter - [cyan]explore selected attribute[/cyan]
                  h Esc - [cyan]go back to parent object[/cyan]
                    [ ] - [cyan]switch attribute type (public/private)[/cyan]
                    { } - [cyan]switch pane[/cyan]
                      v - [cyan]toggle full preview[/cyan]
                      d - [cyan]toggle full docstring[/cyan]
                      f - [cyan]open fullscreen view[/cyan]
                      H - [cyan]open help page on selected attribute[/cyan]
                      p - [cyan]exit and print value of selected attribute[/cyan]
                      ? - [cyan]toggle help page[/cyan]
                    q Q - [cyan]quit[/cyan]
                """
            ).strip()

        elif self.state == HelpState.about:
            return f"""
[white]       _     _                 _
  ___ | |__ (_) _____  ___ __ | | ___  _ __ ___
 / _ \| '_ \| |/ _ \ \/ / '_ \| |/ _ \| '__/ _ \\
| (_) | |_) | |  __/>  <| |_) | | (_) | | |  __/
 \___/|_.__// |\___/_/\_\ .__/|_|\___/|_|  \___|
          |__/          |_|
Interactive Python Object Explorer

Author:          [cyan]Kyle Pollina[/cyan]
Version:         [cyan]{self.version}[/cyan]
PyPI:            [cyan]https://pypi.org/project/objexplore[/cyan]
Source:          [cyan]https://github.com/kylepollina/objexplore[/cyan][yellow italic]
Report an issue[/yellow italic]: [cyan]https://github.com/kylepollina/objexplore/issues[/cyan]\n\n""" + self.random_quote()

    def random_quote(self):
        return choice(
            [
                "[i]Have a nice day!![/i]",
                "[i]You look rather dashing today![/i]",
                "[i]:)[/i]",
                "[i]:earth_africa:[/i]",
                "[i]<3[/i]",
            ]
        )
