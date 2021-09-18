import inspect
from typing import Any, Dict, Optional, Union, List

from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.syntax import Syntax
from rich.text import Text

highlighter = ReprHighlighter()


PUBLIC = "PUBLIC"
PRIVATE = "PRIVATE"

console = Console()


class CachedObject:
    def __init__(
        self,
        obj: Any,
        dotpath: str = "",
        attr_name=None,
    ):
        self.obj = obj
        self.dotpath = dotpath
        self.attr_name = attr_name
        self.is_callable = callable(obj)
        self.selected_cached_obj: CachedObject

        self.typeof: Text = highlighter(str(type(self.obj)))
        self.docstring: str = inspect.getdoc(self.obj) or "[magenta italic]None"

        self.plain_attrs = dir(self.obj)

        self.repr = highlighter(repr(self.obj))
        self.repr.overflow = "ellipsis"

        if "__weakref__" in self.plain_attrs:
            # Ignore weakrefs
            self.plain_attrs.remove("__weakref__")

        self.plain_public_attributes = sorted(
            attr for attr in self.plain_attrs if not attr.startswith("_")
        )
        self.plain_private_attributes = sorted(
            attr for attr in self.plain_attrs if attr.startswith("_")
        )
        self.public_attribute_width = (
            max(map(len, self.plain_public_attributes))
            if self.plain_public_attributes
            else 0
        )
        self.private_attribute_width = (
            max(map(len, self.plain_private_attributes))
            if self.plain_private_attributes
            else 0
        )
        # TODO rename?
        self.repr_public_lines = [
            Text(
                attr,
                style=(
                    "white" if not callable(getattr(self.obj, attr))
                    else "dim white italic"
                )
            )
            for attr in self.plain_public_attributes
        ]
        self.repr_private_lines = [
            Text(
                attr,
                style=(
                    "white" if not callable(getattr(self.obj, attr))
                    else "dim white italic"
                )
            )
            for attr in self.plain_private_attributes
        ]
        # Key:val pair of attribute name and the cached object associated with it
        self.cached_attributes: Dict[str, CachedObject] = {}

        try:
            self._source = inspect.getsource(self.obj)
        except Exception:
            self._source = ""

        self.length: Optional[str]

        try:
            self.length = str(len(self.obj))
        except TypeError:
            self.length = None

        if type(self.obj) == dict:
            self.repr_dict_lines: List[Text] = []
            for key, val in self.obj.items():
                if type(key) is str:
                    repr_key = highlighter(f'"{key}"')
                else:
                    repr_key = highlighter(key)
                repr_val = highlighter(str(type(val)))

                if callable(val):
                    repr_val.style = "dim"

                line = Text('  ') + repr_key + Text(': ') + repr_val
                line.overflow = "ellipsis"
                self.repr_dict_lines.append(line)

    def cache_attributes(self):
        """ Create a CachedObject for each attribute of the self.obj """
        if not self.cached_attributes:
            for attr in self.plain_attrs:
                self.cached_attributes[attr] = CachedObject(
                    getattr(self.obj, attr),
                    dotpath=f"{self.dotpath}.{attr}",
                    attr_name=attr,
                )

        # Set the default selected cached attribute
        if self.plain_public_attributes:
            self.selected_cached_obj = self.cached_attributes[
                self.plain_public_attributes[0]
            ]
        else:
            self.selected_cached_obj = self.cached_attributes[
                self.plain_private_attributes[0]
            ]

    def __getitem__(self, key) -> "CachedObject":
        return self.cached_attributes[key]

    def get_source(
        self, term_height: int = 0, fullscreen: bool = False
    ) -> Union[Syntax, str]:
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
