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

    def __call__(self, height: int):
        lines = self.text.splitlines()
        if len(lines) > height - 6:
            lines = lines[: height - 6] + ["        ..."]

        text = "\n".join(lines)
        self.update(
            Panel(
                text,
                title=(
                    "[i white]help[/i white] | [u]key bindings[/u] [dim]about"
                    if self.state == HelpState.keybindings
                    else "[i white]help[/i white] | [dim]key bindings[/dim] [u]about"
                ),
                title_align="left",
                subtitle="[dim white][u]f[/u]:fullscreen [u][][/u]:switch pane [u]?[/u]:exit help",
                subtitle_align="left",
                style="magenta",
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
                      k ↑ - [cyan]up[/cyan]
                      j ↓ - [cyan]down[/cyan]
                        g - [cyan]go to top[/cyan]
                        G - [cyan]go to bottom[/cyan]
                l → Enter - [cyan]select[/cyan]
                    Space - [cyan]select[/cyan]
                      h ← - [cyan]go back to parent object[/cyan]
                      [ ] - [cyan]switch attribute type (public/private)[/cyan]
                      { } - [cyan]switch pane[/cyan]
                        p - [cyan]toggle full preview[/cyan]
                        d - [cyan]toggle full docstring[/cyan]
                        n - [cyan]toggle filter view[/cyan]
                        / - [cyan]open search filter[/cyan]
                      Esc - [cyan]close[/cyan]
                        c - [cyan]clear filters[/cyan]
                        o - [cyan]toggle stack view[/cyan]
                        f - [cyan]open fullscreen view[/cyan]
                        + - [cyan]increase explorer layout[/cyan]
                        - - [cyan]decrease explorer layout[/cyan]
                        = - [cyan]return explorer layout size to default[/cyan]
                        O - [cyan]open source file in [i u]$EDITOR[/i u][/cyan]
                        H - [cyan]open help page on selected attribute[/cyan]
                        i - [cyan]run [magenta]rich[/magenta][white].[/white][magenta]inspect[/magenta][white](<[/white][bright_magenta]OBJECT[/bright_magenta]>, [yellow]methods[/yellow]=[italic bright_green]True[/italic bright_green][white])[/white][/cyan]
                        I - [cyan]run [magenta]rich[/magenta][white].[/white][magenta]inspect[/magenta][white](<[/white][bright_magenta]OBJECT[/bright_magenta]>, [yellow]all[/yellow]=[italic bright_green]True[/italic bright_green][white])[/white][/cyan]
                        r - [cyan]return the selected object[/cyan]
                        ? - [cyan]toggle help page[/cyan]
                      q Q - [cyan]quit[/cyan]
                """
            ).strip()

        elif self.state == HelpState.about:
            return (
                f"""
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
Report an issue[/yellow italic]: [cyan]https://github.com/kylepollina/objexplore/issues[/cyan]\n\n"""
                + "[i]"
                + self.random_quote()
            )

    def random_quote(self):
        return choice(
            [
                "Have a nice day!!",
                "You look rather dashing today!",
                ":)",
                ":earth_africa:",
                "<3",
                "Thanks for checking this out ;)",
                "Why, hello there!",
                "Oh well look who it is!",
                "Oh if a man tried\n"
                "To take his time on Earth\n"
                "And prove before he died\n"
                "What one man's life could be worth\n"
                "I wonder what would happen to this world\n"
                " - Harry Chapin",
                "In this world, people [u i]can[/u i] change it for the better,\n"
                "and that those people who are crazy enough to think that\n"
                "they can change the world are the ones that actually do.\n"
                " - Steve Jobs",
            ]
        )


def random_error_quote():
    quotes = [
        "Aw nuts!",
        "Uh oh...",
        "Foiled again!",
        "We've been bamboozled!",
        "Something ain't right here...",
        "$#%@!!",
        "BONK!",
        "[blink]",
        "Oh no!",
        "Whoopsies.",
        "Dag nabit",
        "👀",
        "Computer over.",
        "Virus = very yes.",
        "Oh Child!",
        "I used objexplore and all I got was this lousy error message.",
    ]
    q1 = choice(quotes)
    quotes.remove(q1)
    q2 = choice(quotes)
    return q1 + " " + q2
