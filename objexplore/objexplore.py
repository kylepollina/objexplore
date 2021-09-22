import inspect
import pydoc
import signal
from typing import Any, Optional, Union

import blessed
import rich
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from .cached_object import CachedObject
from .explorer_layout import ExplorerLayout, ExplorerState
from .filter_layout import FilterLayout
from .help_layout import HelpLayout, HelpState, random_error_quote
from .overview_layout import OverviewLayout, OverviewState, PreviewState
from .stack_layout import StackFrame, StackLayout
from .terminal import Terminal
from .utils import is_selectable

version = "1.4.10"

# TODO object highlighted on stack view should be shown on the overview
# TODO Backspace exit help
# TODO support ctrl-a + (whatever emacs keybinding to go to end of line)
#  https://www.gnu.org/software/bash/manual/html_node/Commands-For-Moving.html
# TODO add () to text for builtin-methods
# TODO add a "searching..." title to search filter
# TODO move stack/filter into the explorer object
# TODO move help into the overview layout
# TODO truncate public/private -> pub priv -> just public/private
# TODO truncate explorer subtitle as well
# TODO +-_= to change the size of the explorer window
# TODO auto return on q or r
# TODO builtin frame/stack explorer? from objexplore import stackexplore
# TODO filter color the filters the same as the explorer
# TODO Fix window when searching, then G, window does not move all the way to the bottom

console = Console()


class ObjExploreApp:
    """ Main Application class """

    def __init__(self, obj: Any, name_of_obj: str):
        cached_obj = CachedObject(obj, attr_name=name_of_obj)
        # Figure out all the attributes of the current obj's attributes
        cached_obj.cache()

        self.cached_obj: CachedObject = cached_obj
        self.stack = StackLayout(head_obj=self.cached_obj, visible=False)
        self.help_layout = HelpLayout(version, visible=False, ratio=3)
        self.explorer_layout = ExplorerLayout(cached_obj=cached_obj)
        self.overview_layout = OverviewLayout(ratio=3)
        self.term = Terminal(stack=self.stack)
        self.filter_layout = FilterLayout(term=self.term, visible=False)

        self.stack.append(
            StackFrame(
                cached_obj=self.cached_obj,
                explorer_layout=self.explorer_layout,
                overview_layout=self.overview_layout,
            )
        )

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

                except StopIteration:
                    return None

        return res

    def process_key_event(self, key: blessed.keyboard.Keystroke) -> Any:
        """ Process the incoming key """

        if self.filter_layout.receiving_input:
            if key.code == self.term.KEY_BACKSPACE:
                self.filter_layout.backspace(self.cached_obj, self.explorer_layout)
            elif key.code == self.term.KEY_ESCAPE:
                self.filter_layout.cancel_search(self.cached_obj)
            elif key.code == self.term.KEY_ENTER:
                self.filter_layout.end_search(self.cached_obj)
            elif key.code == self.term.KEY_LEFT:
                self.filter_layout.cursor_left()
            elif key.code == self.term.KEY_RIGHT:
                self.filter_layout.cursor_right()
            elif key.code in (self.term.KEY_UP, self.term.KEY_DOWN):
                return
            else:
                self.filter_layout.add_search_char(
                    key, self.cached_obj, self.explorer_layout
                )
            return

        if key in ("q", "Q"):
            raise StopIteration

        # Help page ###########################################################

        if self.help_layout.visible:
            # Close help page
            if key == "?" or key.code == self.term.KEY_ESCAPE:
                self.help_layout.visible = False
                return

            # Fullscreen
            elif key == "f":
                with console.capture() as capture:
                    console.print(self.help_layout.text)
                str_out = capture.get()
                pydoc.pager(str_out)
                return

            # Switch panes
            elif key in ("{", "}", "[", "]"):
                if self.help_layout.state == HelpState.keybindings:
                    self.help_layout.state = HelpState.about
                elif self.help_layout.state == HelpState.about:
                    self.help_layout.state = HelpState.keybindings
                return

            elif key in ("j", "k", "o", "n") or key.code in (
                self.term.KEY_UP,
                self.term.KEY_DOWN,
            ):
                # Continue on and process these keys as normal
                self.help_layout.visible = False

            else:
                return

        if key == "?" and self.help_layout.visible is False:
            self.help_layout.visible = True
            return

        # Stack ###############################################################

        if key == "o":
            if self.stack.visible:
                self.stack.visible = False
            elif self.filter_layout.visible:
                self.filter_layout.visible = False
                self.stack.set_visible()
            else:
                self.stack.set_visible()

        elif (
            key.code in (self.term.KEY_BACKSPACE, self.term.KEY_ESCAPE)
            and self.stack.visible
        ):
            self.stack.visible = False

        elif (key == " " or key.code == self.term.KEY_ENTER) and self.stack.visible:
            # If you are choosing the same frame as the current obj, then don't do anything
            if self.stack[self.stack.index].cached_obj == self.cached_obj:
                return
            new_cached_obj = self.stack.select()
            # TODO abstract the following
            if not is_selectable(new_cached_obj.obj):
                return
            self.explorer_layout = ExplorerLayout(cached_obj=new_cached_obj)
            self.cached_obj = new_cached_obj
            self.cached_obj.cache()
            self.filter_layout.cancel_search(self.cached_obj)
            self.stack.append(
                StackFrame(
                    cached_obj=self.cached_obj,
                    explorer_layout=self.explorer_layout,
                    overview_layout=self.overview_layout,
                )
            )

        elif (key == "j" or key.code == self.term.KEY_DOWN) and self.stack.visible:
            self.stack.move_down(self.term.explorer_panel_height)

        elif (key == "k" or key.code == self.term.KEY_UP) and self.stack.visible:
            self.stack.move_up()

        elif key == "g" and self.stack.visible:
            self.stack.move_top()

        elif key == "G" and self.stack.visible:
            self.stack.move_bottom()

        # Filter ##############################################################

        elif key == "n":
            if self.filter_layout.visible:
                self.filter_layout.visible = False
            elif self.stack.visible:
                self.stack.visible = False
                self.filter_layout.visible = True
            else:
                self.filter_layout.visible = True

        elif key == "/" and not self.filter_layout.receiving_input:
            self.stack.visible = False
            self.filter_layout.receiving_input = True
            self.filter_layout.visible = True

        elif (
            key == " " or key.code == self.term.KEY_ENTER
        ) and self.filter_layout.visible:
            self.filter_layout.toggle(cached_obj=self.cached_obj)

        elif (
            key.code in (self.term.KEY_ESCAPE, self.term.KEY_BACKSPACE)
        ) and self.filter_layout.visible:
            self.filter_layout.visible = False

        elif (
            key == "j" or key.code == self.term.KEY_DOWN
        ) and self.filter_layout.visible:
            self.filter_layout.move_down()

        elif (
            key == "k" or key.code == self.term.KEY_CODE
        ) and self.filter_layout.visible:
            self.filter_layout.move_up()

        elif key == "g" and self.filter_layout.visible:
            self.filter_layout.move_top()

        elif key == "G" and self.filter_layout.visible:
            self.filter_layout.move_bottom()

        elif key == "c":
            self.filter_layout.clear_filters(self.cached_obj)

        # Explorer ############################################################

        elif key == "k" or key.code == self.term.KEY_UP:
            self.explorer_layout.move_up()

        elif key == "j" or key.code == self.term.KEY_DOWN:
            self.explorer_layout.move_down(
                self.term.explorer_panel_height, self.cached_obj
            )

        elif key in ("l", " ") or key.code in (
            self.term.KEY_ENTER,
            self.term.KEY_RIGHT,
            self.term.KEY,
        ):
            new_cached_obj = self.explorer_layout.selected_object
            # TODO abstract the following
            if not is_selectable(new_cached_obj.obj):
                return

            self.explorer_layout = ExplorerLayout(cached_obj=new_cached_obj)
            self.cached_obj = new_cached_obj
            self.cached_obj.cache()
            self.filter_layout.cancel_search(self.cached_obj)
            self.stack.append(
                StackFrame(
                    cached_obj=self.cached_obj,
                    explorer_layout=self.explorer_layout,
                    overview_layout=self.overview_layout,
                )
            )

        # Go back to parent
        elif (key == "h" or key.code == self.term.KEY_LEFT) and self.stack.stack:
            self.stack.pop()
            self.cached_obj = self.stack[-1].cached_obj
            self.filter_layout.clear_filters(self.cached_obj)
            self.explorer_layout = self.stack[-1].explorer_layout
            self.overview_layout = self.stack[-1].overview_layout

        elif key == "g":
            self.explorer_layout.move_top()

        elif key == "G":
            self.explorer_layout.move_bottom(
                self.term.explorer_panel_height, self.cached_obj
            )

        # Overview ############################################################

        # Switch between public and private attributes
        elif key in ("[", "]"):
            if self.explorer_layout.state == ExplorerState.public:
                self.explorer_layout.state = ExplorerState.private

            elif self.explorer_layout.state == ExplorerState.private:
                self.explorer_layout.state = ExplorerState.public

        elif key in ("{", "}"):
            if not callable(self.explorer_layout.selected_object.obj):
                return

            if self.overview_layout.preview_state == PreviewState.repr:
                self.overview_layout.preview_state = PreviewState.source
            elif self.overview_layout.preview_state == PreviewState.source:
                self.overview_layout.preview_state = PreviewState.repr

        # Toggle docstring view
        elif key == "d":
            self.overview_layout.state = (
                OverviewState.docstring
                if self.overview_layout.state != OverviewState.docstring
                else OverviewState.all
            )

        # Toggle value view
        elif key == "p":
            self.overview_layout.state = (
                OverviewState.value
                if self.overview_layout.state != OverviewState.value
                else OverviewState.all
            )

        # Fullscreen
        elif key == "f":
            printable: Union[str, Syntax, Text]

            if self.overview_layout.state == OverviewState.docstring:
                printable = self.explorer_layout.selected_object.docstring

            elif self.overview_layout.preview_state == PreviewState.repr:
                printable = self.explorer_layout.selected_object.obj

            elif self.overview_layout.preview_state == PreviewState.source:
                printable = self.explorer_layout.selected_object.get_source(
                    fullscreen=True
                )

            with console.capture() as capture:
                console.print(printable)

            str_out = capture.get()
            pydoc.pager(str_out)

        elif key == "H":
            help(self.explorer_layout.selected_object.obj)

        elif key == "i":
            with console.capture() as capture:
                rich.inspect(
                    self.explorer_layout.selected_object.obj,
                    console=console,
                    methods=True,
                )
            str_out = capture.get()
            pydoc.pager(str_out)

        elif key == "I":
            with console.capture() as capture:
                rich.inspect(
                    self.explorer_layout.selected_object.obj, console=console, all=True
                )
            str_out = capture.get()
            pydoc.pager(str_out)

        # Other ################################################################

        # Return selected object
        elif key == "r":
            return self.explorer_layout.selected_object.obj

    def get_explorer_layout(self) -> Layout:
        if self.stack.visible:
            layout = Layout()
            layout.split_column(
                self.explorer_layout(
                    term_width=self.term.width,
                    term_height=self.term.height,
                ),
                self.stack(term_width=self.term.width),
            )
            return layout
        elif self.filter_layout.visible:
            layout = Layout()
            layout.split_column(
                self.explorer_layout(
                    term_width=self.term.width,
                    term_height=self.term.height,
                ),
                self.filter_layout(),
            )
            return layout
        else:
            return self.explorer_layout(
                term_width=self.term.width,
                term_height=self.term.height,
            )

    def get_overview_layout(self) -> Layout:
        if self.help_layout.visible:
            return self.help_layout()
        else:
            return self.overview_layout(
                cached_obj=self.explorer_layout.selected_object,
                term_height=self.term.height,
                console=console,
            )

    def draw(self, *args):
        """ Draw the application. the *args argument is due to resize events and are unused """
        print(self.term.home, end="")
        layout = Layout()

        layout.split_row(self.get_explorer_layout(), self.get_overview_layout())

        title = (
            self.cached_obj.dotpath
            + Text(" | ", style="white")
            + self.cached_obj.typeof
        )

        object_explorer = Panel(
            layout,
            title=title,
            subtitle=(
                "[red][u]q[/u]:quit[/red] "
                f"[cyan][u]?[/u]:{'exit ' if self.help_layout.visible else ''}help[/] "
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
