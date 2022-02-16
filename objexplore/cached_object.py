from dataclasses import dataclass
import importlib
import inspect
import pkgutil
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.pretty import Pretty
from rich.style import Style
from rich.syntax import Syntax
from rich.text import Text

from .utils import is_empty

highlighter = ReprHighlighter()


PUBLIC = "PUBLIC"
PRIVATE = "PRIVATE"

console = Console()


def safegetattr(obj, attr):
    try:
        return getattr(obj, attr)
    except Exception:
        return None


class CachedObject:
    """Internal representation of every object that is being inspected/explored by objexplore

    TODO add documentation on all the attributes of this object
    TODO look up how other libraries document thier attributes
    """

    def __init__(
        self,
        obj: Any,
        parent_path: Text = None,
        attr_name: str = None,
        index: Any = None,
        hidden: bool = False,
    ):
        self.obj = obj
        self.is_callable = callable(obj)
        self.attr_name = attr_name if attr_name else repr(self.obj)

        if self.obj is None:
            # TODO this doesn't seem like the right choice but removing it causes a crash. Investigate!
            self.dotpath = highlighter("None")

        elif attr_name is not None:
            if not parent_path:
                self.dotpath = Text(attr_name, style=Style(color="cyan"))
            else:
                self.dotpath = (
                    parent_path
                    + Text(".", style=Style(color="white"))
                    + Text(attr_name, style=Style(color="cyan"))
                )

        elif index is not None:
            if type(index) == str:
                repr_index = console.render_str(f'"{index}"')
            else:
                repr_index = console.render_str(str(index))
            if not parent_path:
                self.dotpath = (
                    Text("[", style=Style(color="white"))
                    + repr_index
                    + Text("]", style=Style(color="white"))
                )
            else:
                self.dotpath = (
                    parent_path
                    + Text("[", style=Style(color="white"))
                    + repr_index
                    + Text("]", style=Style(color="white"))
                )
        else:
            raise ValueError("Need to specify an attribute name or an index")

        self.plain_attrs = dir(self.obj)

        if "__weakref__" in self.plain_attrs:
            # Ignore weakrefs
            # Why??? I don't remember
            self.plain_attrs.remove("__weakref__")

        self.plain_public_attributes = sorted(
            attr for attr in self.plain_attrs if not attr.startswith("_")
        )
        self.plain_private_attributes = sorted(
            attr for attr in self.plain_attrs if attr.startswith("_")
        )

        self.public_attributes: Dict[str, CachedObject] = {}
        self.private_attributes: Dict[str, CachedObject] = {}
        self.filtered_public_attributes: Dict[str, CachedObject] = {}
        self.filtered_private_attributes: Dict[str, CachedObject] = {}

        try:
            self._source = inspect.getsource(self.obj)  # type: ignore
        except Exception:
            self._source = ""

        self.length: Optional[int]

        try:
            self.length = len(self.obj)  # type: ignore
        except TypeError:
            self.length = None

        self.isbuiltin: bool = inspect.isbuiltin(self.obj)
        self.isclass: bool = inspect.isclass(self.obj)
        self.isfunction: bool = inspect.isfunction(self.obj)
        self.ismethod: bool = inspect.ismethod(self.obj)
        self.ismethoddescriptor: bool = inspect.ismethoddescriptor(self.obj)
        self.ismodule: bool = inspect.ismodule(self.obj)

        self.filters: List[Union[bool, Callable[[Any], Any]]] = []
        self.search_filter: str = ""

        # Highlighted attributes
        self.typeof: Text = highlighter(str(type(self.obj)))
        self.docstring: Text = console.render_str(inspect.getdoc(self.obj) or "None")
        self.docstring_lines = self.docstring.split()
        self.repr = highlighter(repr(self.obj))
        if "\n" in self.repr:
            self.repr = self.repr.split("\n")[0]
        self.repr.overflow = "ellipsis"
        self.pretty = Pretty(self.obj)

        self.text = Text(self.attr_name, style=Style(), overflow="ellipsis")

        if self.ismodule:
            self.text.style = Style(color="blue")
        elif self.isclass:
            self.text.style = Style(color="magenta")
        elif (
            self.isfunction
            or self.ismethod
            or self.ismethoddescriptor
            # builtin_function_or_method type. Don't know where this is defined
            or isinstance(self.obj, type("".capitalize))
        ):
            self.text.style = Style(color="cyan", italic=True)
            self.text += Text("()", style=Style(color="white"))
        elif type(self.obj) == dict:
            self.text.style = Style(color="light_sea_green")
            self.text = (
                Text("{**", style=Style(color="white"))
                + self.text
                + Text("}", style=Style(color="white"))
            )
        elif type(self.obj) == list:
            self.text.style = Style(color="indian_red1")
            self.text = (
                Text("[*", style=Style(color="white"))
                + self.text
                + Text("]", style=Style(color="white"))
            )
        elif type(self.obj) == tuple:
            self.text.style = Style(color="pale_violet_red1")
            self.text = (
                Text("(*", style=Style(color="white"))
                + self.text
                + Text(")", style=Style(color="white"))
            )
        elif type(self.obj) == set:
            self.text.style = Style(color="light_goldenrod3")
            self.text = (
                Text("{*", style=Style(color="white"))
                + self.text
                + Text("}", style=Style(color="white"))
            )

        if not is_empty(self.obj):
            self.text.style += Style(dim=True, strike=True)  # type: ignore

        if hidden:
            self.text.style += Style(dim=True)  # type: ignore

    @property
    def title(self):
        """ TODO """
        # for cases when the object is a huge dictionary we shouldnt try to render the whole dict
        if len(self.repr.plain) > console.width - 4:
            return Text(self.attr_name) + Text(" ") + self.typeof
        title = self.repr.copy()
        title.truncate(console.width - 4)
        return title

    def cache(self):
        """ Cache any attributes that are useful to this object for easy access later """

        if not self.public_attributes:
            for attr in self.plain_public_attributes:
                self.public_attributes[attr] = CachedObject(
                    safegetattr(self.obj, attr),
                    parent_path=self.dotpath,
                    attr_name=attr,
                )

        if not self.private_attributes:
            for attr in self.plain_private_attributes:
                self.private_attributes[attr] = CachedObject(
                    safegetattr(self.obj, attr),
                    parent_path=self.dotpath,
                    attr_name=attr,
                )

        # Sometimes a module will have submodules that are not referenced from a call to `dir()`
        # This check will look through all submodules that are not referenced by `dir()` and add
        # them to the cached attributes
        if self.ismodule:
            prefix = safegetattr(self.obj, "__name__") + "."
            path = safegetattr(self.obj, "__path__")
            for importer, full_module_name, ispkg in pkgutil.iter_modules(path, prefix):
                name = full_module_name.rsplit(".")[-1]
                if name in self.public_attributes or name in self.private_attributes:
                    # Skip over submodules that have already been indexed
                    continue

                try:
                    # If we have not encountered this module, try to import it
                    module = importlib.import_module(full_module_name)
                except Exception:
                    continue

                if not name.startswith("_"):
                    self.public_attributes[name] = CachedObject(
                        module, parent_path=self.dotpath, attr_name=name, hidden=True
                    )
                else:
                    self.private_attributes[name] = CachedObject(
                        module, parent_path=self.dotpath, attr_name=name, hidden=True
                    )

        self.num_public_attributes: int = len(self.public_attributes)
        self.num_private_attributes: int = len(self.private_attributes)

        self.filter()

    def set_filters(
        self, filters: List[Union[bool, Callable[[Any], Any]]], search_filter: str = ""
    ):
        """ Reset the filters associated with this object, and rerun the filtering process again with the new filters """
        self.filters = filters
        self.search_filter = search_filter.lower()
        self.filter()

    def filter(self):
        """ Run the filters on all of this objects attributes """
        self.filtered_public_attributes = {}
        for attr, cached_obj in self.public_attributes.items():
            if self.search_filter not in attr.lower():
                continue
            if not self.filters:
                self.filtered_public_attributes[attr] = cached_obj
            else:
                # Only keep objects that match the filter
                for _filter in self.filters:
                    if _filter(cached_obj):
                        self.filtered_public_attributes[attr] = cached_obj
                        break
        self.num_filtered_public_attributes = len(self.filtered_public_attributes)

        self.filtered_private_attributes = {}
        for attr, cached_obj in self.private_attributes.items():
            if self.search_filter not in attr.lower():
                continue
            if not self.filters:
                self.filtered_private_attributes[attr] = cached_obj
            else:
                # Only keep objects that match the filter
                for _filter in self.filters:
                    if _filter(cached_obj):
                        self.filtered_private_attributes[attr] = cached_obj
                        break
        self.num_filtered_private_attributes = len(self.filtered_private_attributes)

        self.filtered_dict: Dict[str, FilteredDictKey] = {}
        if type(self.obj) == dict:
            for key, val in self.obj.items():
                repr_key: Text
                repr_val: Text

                if type(key) == str:
                    repr_key = console.render_str(f'"{key}"')
                elif type(key) in (int, float, dict, list, set, tuple, bool, None):
                    repr_key = console.render_str(str(key))
                else:
                    repr_key = highlighter(str(key))

                repr_val = highlighter(str(type(val)))

                if not is_empty(val):
                    repr_val.style += " dim"
                    repr_val.style = repr_val.style.strip()

                line = Text(" ") + repr_key + Text(": ") + repr_val
                line.overflow = "ellipsis"

                cached_obj = CachedObject(val, parent_path=self.dotpath, index=key)

                if type(key) == str and self.search_filter not in key.lower():
                    continue
                if self.filters:
                    for _filter in self.filters:
                        if _filter(cached_obj):
                            self.filtered_dict[key] = FilteredDictKey(
                                text=line, cached_object=cached_obj
                            )
                            break
                else:
                    self.filtered_dict[key] = FilteredDictKey(
                        text=line, cached_object=cached_obj
                    )

        self.num_filtered_dict_keys = len(self.filtered_dict)

        self.filtered_list: List[Tuple[Text, CachedObject]] = []
        if isinstance(self.obj, (list, tuple, set)):
            for index, item in enumerate(self.obj):
                line = (
                    Text(" [", style=Style(color="white"))
                    + Text(str(index), style=Style(color="blue"))
                    + Text("] ", style=Style(color="white"))
                    + highlighter(str(type(item)))
                )
                if not is_empty(item):
                    line.style += Style(dim=True)

                self.filtered_list.append(
                    (line, CachedObject(item, parent_path=self.dotpath, index=index))
                )
            if self.filters:
                new_filtered_list: List[Tuple[Text, CachedObject]] = []
                for line, cached_obj in self.filtered_list:
                    for _filter in self.filters:
                        if _filter(cached_obj):
                            new_filtered_list.append((line, cached_obj))
                            break
                self.filtered_list = new_filtered_list
        self.num_filtered_list_items = len(self.filtered_list)

    def current_visible_attributes(self):
        """ TODO """
        if self.filtered_dict:
            return self.filtered_dict
        elif self.filtered_list:
            return self.filtered_list

    def get_source(
        self, term_height: int = 0, fullscreen: bool = False
    ) -> Union[Syntax, str]:
        """ TODO """
        if not fullscreen and not term_height:
            raise ValueError("Need a terminal height")

        if not self._source:
            return "[red italic]Source code unavailable"

        if fullscreen:
            return Syntax(
                self._source, "python", line_numbers=True, background_color="default"
            )
        else:
            return Syntax(
                self._source,
                "python",
                line_numbers=True,
                line_range=(0, term_height),
                background_color="default",
            )


@dataclass
class FilteredDictKey:
    """ TODO """

    text: Text
    cached_object: CachedObject

    def __iter__(self):
        # return [self.text, self.cached_object]
        yield self.text
        yield self.cached_object
