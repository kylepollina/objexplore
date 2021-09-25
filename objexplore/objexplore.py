import inspect
import pydoc
import signal
from typing import Any, Optional, Union

import blessed
import rich
from blessed import Terminal
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from .cached_object import CachedObject
from .explorer import Explorer, ExplorerState
from .help_layout import HelpState, random_error_quote
from .overview import Overview, OverviewState, PreviewState

version = "1.5.1"

# TODO object highlighted on stack view should be shown on the overview
# TODO support ctrl-a + (whatever emacs keybinding to go to end of line)
#  https://www.gnu.org/software/bash/manual/html_node/Commands-For-Moving.html
# TODO truncate public/private -> pub priv -> just public/private
# TODO truncate explorer subtitle as well
# TODO +-_= to change the size of the explorer window
# TODO builtin frame/stack explorer? from objexplore import stackexplore

console = Console()


class ObjExploreApp:
    """ Main Application class """

    def __init__(self, obj: Any, name_of_obj: str):
        cached_obj = CachedObject(obj, attr_name=name_of_obj)
        # Figure out all the attributes of the current obj's attributes
        cached_obj.cache()

        self.term = Terminal()
        self.explorer = Explorer(term=self.term, cached_obj=cached_obj)
        self.overview = Overview(term=self.term, version=version)

        # Run self.draw() whenever the win change signal is caught
        try:
            signal.signal(signal.SIGWINCH, self.draw)
        # Windows does not have SIGWINCH signal
        except AttributeError:
            pass

    def explore(self) -> Optional[Any]:
        """ Open the interactive explorer """

        key = None
        res = None

        # Clear the screen
        print(self.term.clear, end="")

        with self.term.cbreak(), self.term.hidden_cursor():
            while True:
                try:
                    self.draw()
                    key = self.term.inkey()
                    res = self.process_key_event(key)

                    # If the object is returned as a response then close the explorer and return the selected object
                    if res:
                        break

                except RuntimeError as err:
                    # Some kind of error during resizing events. Ignore and continue
                    if (
                        err.args[0]
                        == "reentrant call inside <_io.BufferedWriter name='<stdout>'>"
                    ):
                        pass
                    # Otherwise it is a new error. Raise
                    else:
                        raise err

        return res

    def process_key_event(self, key: blessed.keyboard.Keystroke) -> Any:
        """ Process the incoming key """

        if self.explorer.filter.receiving_input:
            if key.code == self.term.KEY_BACKSPACE:
                self.explorer.filter.backspace(
                    cached_obj=self.explorer.cached_obj,
                    live_update=self.explorer.live_update,
                )
            elif key.code == self.term.KEY_ESCAPE:
                self.explorer.filter.cancel_search(self.explorer.cached_obj)
            elif key.code == self.term.KEY_ENTER:
                self.explorer.filter.end_search(cached_obj=self.explorer.cached_obj)
            elif key.code == self.term.KEY_LEFT:
                self.explorer.filter.cursor_left()
            elif key.code == self.term.KEY_RIGHT:
                self.explorer.filter.cursor_right()
            elif key.code in (self.term.KEY_UP, self.term.KEY_DOWN):
                return
            else:
                self.explorer.filter.add_search_char(
                    key=key,
                    cached_obj=self.explorer.cached_obj,
                    live_update=self.explorer.live_update,
                )
            return

        if key in ("q", "Q", "r"):
            return self.explorer.selected_object.obj

        # Help page ###########################################################

        if self.overview.help_layout.visible:
            # Close help page
            if key == "?" or key.code in (
                self.term.KEY_ESCAPE,
                self.term.KEY_BACKSPACE,
            ):
                self.overview.help_layout.visible = False
                return

            # Fullscreen
            elif key == "f":
                with console.capture() as capture:
                    console.print(self.overview.help_layout.text)
                str_out = capture.get()
                pydoc.pager(str_out)
                return

            # Switch panes
            elif key in ("{", "}", "[", "]"):
                if self.overview.help_layout.state == HelpState.keybindings:
                    self.overview.help_layout.state = HelpState.about
                elif self.overview.help_layout.state == HelpState.about:
                    self.overview.help_layout.state = HelpState.keybindings
                return

            elif key in ("j", "k", "o", "n") or key.code in (
                self.term.KEY_UP,
                self.term.KEY_DOWN,
            ):
                # Continue on and process these keys as normal
                self.overview.help_layout.visible = False

            else:
                return

        if key == "?" and self.overview.help_layout.visible is False:
            self.overview.help_layout.visible = True
            return

        # Stack ###############################################################

        if key == "o":
            if self.explorer.stack.layout.visible:
                self.explorer.stack.layout.visible = False
            elif self.explorer.filter.layout.visible:
                self.explorer.filter.layout.visible = False
                self.explorer.stack.set_visible()
            else:
                self.explorer.stack.set_visible()

        elif (
            key.code in (self.term.KEY_BACKSPACE, self.term.KEY_ESCAPE)
            and self.explorer.stack.layout.visible
        ):
            self.explorer.stack.layout.visible = False

        elif (
            key == " " or key.code == self.term.KEY_ENTER
        ) and self.explorer.stack.layout.visible:
            self.explorer.explore_selected_stack_object()

        elif (
            key == "j" or key.code == self.term.KEY_DOWN
        ) and self.explorer.stack.layout.visible:
            self.explorer.stack.move_down()

        elif (
            key == "k" or key.code == self.term.KEY_UP
        ) and self.explorer.stack.layout.visible:
            self.explorer.stack.move_up()

        elif key == "g" and self.explorer.stack.layout.visible:
            self.explorer.stack.move_top()

        elif key == "G" and self.explorer.stack.layout.visible:
            self.explorer.stack.move_bottom()

        # disable these keys when the stack explorer is visible
        elif (
            key in ("l", "[", "]", "{", "}", "h") and self.explorer.stack.layout.visible
        ):
            return

        # Filter ##############################################################

        elif key == "n":
            if self.explorer.filter.layout.visible:
                self.explorer.filter.layout.visible = False
            elif self.explorer.stack.layout.visible:
                self.explorer.stack.layout.visible = False
                self.explorer.filter.layout.visible = True
            else:
                self.explorer.filter.layout.visible = True

        elif key == "/" and not self.explorer.filter.receiving_input:
            self.explorer.stack.layout.visible = False
            self.explorer.filter.receiving_input = True
            self.explorer.filter.layout.visible = True

        elif (
            key == " " or key.code == self.term.KEY_ENTER
        ) and self.explorer.filter.layout.visible:
            self.explorer.filter.toggle(self.explorer.cached_obj)

        elif (
            key.code in (self.term.KEY_ESCAPE, self.term.KEY_BACKSPACE)
        ) and self.explorer.filter.layout.visible:
            self.explorer.filter.layout.visible = False

        elif (
            key == "j" or key.code == self.term.KEY_DOWN
        ) and self.explorer.filter.layout.visible:
            self.explorer.filter.move_down()

        elif (
            key == "k" or key.code == self.term.KEY_CODE
        ) and self.explorer.filter.layout.visible:
            self.explorer.filter.move_up()

        elif key == "g" and self.explorer.filter.layout.visible:
            self.explorer.filter.move_top()

        elif key == "G" and self.explorer.filter.layout.visible:
            self.explorer.filter.move_bottom()

        elif key == "c":
            self.explorer.filter.clear_filters(self.explorer.cached_obj)

        # Explorer ############################################################

        elif key == "k" or key.code == self.term.KEY_UP:
            self.explorer.move_up()

        elif key == "j" or key.code == self.term.KEY_DOWN:
            self.explorer.move_down()

        elif key in ("l") or key.code in (
            self.term.KEY_ENTER,
            self.term.KEY_RIGHT,
            self.term.KEY,
        ):
            self.explorer.explore_selected_object()

        # Go back to parent
        elif (
            key == "h" or key.code == self.term.KEY_LEFT
        ) and self.explorer.stack.stack:
            self.explorer.explore_parent_obj()

        elif key == "g":
            self.explorer.move_top()

        elif key == "G":
            self.explorer.move_bottom()

        # Switch between public and private attributes
        elif key in ("[", "]"):
            if self.explorer.state == ExplorerState.public:
                self.explorer.state = ExplorerState.private

            elif self.explorer.state == ExplorerState.private:
                self.explorer.state = ExplorerState.public

        elif key == "+":
            self.explorer.increase_width()

        elif key in ("_", "-"):
            self.explorer.decrease_width()

        elif key == "=":
            self.explorer.extra_width = 0

        # Overview ############################################################

        elif key in ("{", "}"):
            if not callable(self.explorer.selected_object.obj):
                return

            if self.overview.preview_state == PreviewState.repr:
                self.overview.preview_state = PreviewState.source
            elif self.overview.preview_state == PreviewState.source:
                self.overview.preview_state = PreviewState.repr

        # Toggle docstring view
        elif key == "d":
            self.overview.state = (
                OverviewState.docstring
                if self.overview.state != OverviewState.docstring
                else OverviewState.all
            )

        # Toggle value view
        elif key == "p":
            self.overview.state = (
                OverviewState.value
                if self.overview.state != OverviewState.value
                else OverviewState.all
            )

        # Fullscreen
        elif key == "f":
            printable: Union[str, Syntax, Text]

            if self.overview.state == OverviewState.docstring:
                printable = self.explorer.selected_object.docstring

            elif self.overview.preview_state == PreviewState.repr:
                printable = self.explorer.selected_object.obj

            elif self.overview.preview_state == PreviewState.source:
                printable = self.explorer.selected_object.get_source(fullscreen=True)

            with console.capture() as capture:
                console.print(printable)

            str_out = capture.get()
            pydoc.pager(str_out)

        elif key == "H":
            help(self.explorer.selected_object.obj)

        elif key == "i":
            with console.capture() as capture:
                rich.inspect(
                    self.explorer.selected_object.obj,
                    console=console,
                    methods=True,
                )
            str_out = capture.get()
            pydoc.pager(str_out)

        elif key == "I":
            with console.capture() as capture:
                rich.inspect(
                    self.explorer.selected_object.obj, console=console, all=True
                )
            str_out = capture.get()
            pydoc.pager(str_out)

    def draw(self, *args):
        """ Draw the application. the *args argument is due to resize events and are unused """
        print(self.term.home, end="")
        layout = Layout()
        layout.split_row(
            self.explorer.get_layout(),
            self.overview.get_layout(self.explorer.selected_object),
        )

        title = (
            self.explorer.cached_obj.dotpath
            + Text(" | ", style="white")
            + self.explorer.cached_obj.typeof
        )

        object_explorer = Panel(
            layout,
            title=title,
            subtitle=(
                "[red][u]q[/u]:quit[/red] "
                f"[cyan][u]?[/u]:{'exit ' if self.overview.help_layout.visible else ''}help[/] "
                "[bright_blue][u]o[/u]:stack [/bright_blue][bright_magenta][u]n[/u]:filter [/bright_magenta][aquamarine1][u]/[/u]:search [/aquamarine1][u]r[/u]:return"
            ),
            subtitle_align="left",
            height=self.term.height - 1,
            style="blue",
        )
        rich.print(object_explorer, end="")


def explore(obj: Any) -> Any:
    """ Run the explorer on the given object """
    # Get the name of the variable sent to this function
    # If someone calls this function like:
    # >>> df = pandas.DataFrame()
    # >>> explore(df)
    # Then we want to extract `name` == 'df'
    frame = inspect.currentframe()
    name = frame.f_back.f_code.co_names[1]  # type: ignore
    app = ObjExploreApp(obj, name_of_obj=name)
    try:
        return app.explore()
    except Exception as err:
        print(app.term.move_down(app.term.height))
        console.print_exception(show_locals=True)
        print()
        rich.print(f"[red]{random_error_quote()}")
        formatted_link = f"https://github.com/kylepollina/objexplore/issues/new?assignees=&labels=&template=bug_report.md&title={err}".replace(
            " ", "+"
        )
        print("Please report the issue here:")
        rich.print(f"   [link={formatted_link}][u]{formatted_link}[/u][/link]")
        print()
        rich.print(
            "[yellow italic]Make sure to copy/paste the above traceback to the issue page to make this quicker to fix :)"
        )
