import inspect
import types
from typing import Any, Dict, List, Optional, Union, Tuple

from rich.pretty import Pretty
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.style import Style
from rich.syntax import Syntax
from rich.text import Text

from .utils import is_selectable

highlighter = ReprHighlighter()


PUBLIC = "PUBLIC"
PRIVATE = "PRIVATE"

console = Console()


class CachedObject:
    def __init__(
        self,
        obj: Any,
        attr_name: str = None,
        dotpath: str = "",
    ):
        self.obj = obj
        self.dotpath = dotpath
        self.attr_name = attr_name if attr_name else repr(obj)
        self.is_callable = callable(obj)
        self.selected_cached_obj: CachedObject
        self.plain_attrs = dir(self.obj)

        # Highlighted attributes
        if not is_selectable(self.obj):
            style = Style(dim=True, italic=True)
        else:
            style = Style()
        self.text = Text(self.attr_name, style)

        self.typeof: Text = highlighter(str(type(self.obj)))
        self.docstring: Text = console.render_str(inspect.getdoc(self.obj) or "None")
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

        self.public_attributes = {}
        self.private_attributes = {}
        self.filtered_public_attributes = {}
        self.filtered_private_attributes = {}
        self._hidden_public_attributes = {}
        self._hidden_private_attributes = {}
        # TODO hidden for below
        self.cached_dict = {}
        self.cached_list = []

        try:
            self._source = inspect.getsource(self.obj)
        except Exception:
            self._source = ""

        self.length: Optional[str]

        try:
            self.length = str(len(self.obj))
        except TypeError:
            self.length = None

        self.isbuiltin = inspect.isbuiltin(self.obj)
        self.isclass = inspect.isclass(self.obj)
        self.isclass = inspect.isclass(self.obj)
        self.isfunction = inspect.isfunction(self.obj)
        self.ismethod = inspect.ismethod(self.obj)
        self.ismodule = inspect.ismodule(self.obj)
        self.filters: List[types.FunctionType] = []


        self.pretty = Pretty(self.obj)

    @property
    def title(self):
        # for cases when the object is a huge dictionary we shouldnt try to render the whole dict
        title = self.repr.copy()
        title.truncate(console.width - 4)
        return title

    def cache(self):
        if not self.public_attributes:
            for attr in self.plain_public_attributes:
                self.public_attributes[attr] = CachedObject(
                    getattr(self.obj, attr),
                    dotpath=f"{self.dotpath}.{attr}",
                    attr_name=attr
                )

        if not self.private_attributes:
            for attr in self.plain_private_attributes:
                self.private_attributes[attr] = CachedObject(
                    getattr(self.obj, attr),
                    dotpath=f"{self.dotpath}.{attr}",
                    attr_name=attr
                )

        # TODO filter
        if not self.cached_dict:
            if type(self.obj) == dict:
                for key, val in self.obj.items():
                    self.cached_dict[key] = CachedObject(
                        val,
                        dotpath=f"{self.dotpath}[{key}]",
                        attr_name=key
                    )
        if not self.cached_list:
            if type(self.obj) == list:
                for index, item in enumerate(self.obj):
                    self.cached_dict[index] = CachedObject(
                        item,
                        dotpath=f"{self.dotpath}[{index}]",
                        attr_name=key
                    )

        self.filter()

    def set_filters(self, filters: List[types.FunctionType]):
        self.filters = filters
        self.filter()

    def filter(self):
        self.filtered_public_attributes = {}
        if not self.filters:
            self.filtered_public_attributes = self.public_attributes
        else:
            for attr, cached_obj in self.public_attributes.items():
                # Only keep objects that match the filter
                for _filter in self.filters:
                    if _filter(cached_obj):
                        self.filtered_public_attributes[attr] = cached_obj
                        break

        self.filtered_private_attributes = {}
        if not self.filters:
            self.filtered_private_attributes = self.private_attributes
        else:
            for attr, cached_obj in self.private_attributes.items():
                # Only keep objects that match the filter
                for _filter in self.filters:
                    if _filter(cached_obj):
                        self.filtered_private_attributes[attr] = cached_obj
                        break

        self.filtered_dict: Dict[str, Tuple[Text, CachedObject]] = {}
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

                if not is_selectable(val):
                    repr_val.style += " dim italic"
                    repr_val.style = repr_val.style.strip()

                line = Text(" ") + repr_key + Text(": ") + repr_val
                line.overflow = "ellipsis"
                self.filtered_dict[key] = (
                    line, CachedObject(val, dotpath=f"{self.dotpath}[{key}]", attr_name=key)
                )
            if self.filters:
                for attr, (line, cached_obj) in self.filtered_dict.copy().items():
                    for _filter in self.filters:
                        if _filter(cached_obj):
                            self.filtered_dict[attr] = (line, cached_obj)
                            break
                    else:
                        del self.filtered_dict[attr]

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


        # # Pre-generated list of lines to render in the explorer layout when exploring public or private attributes of an object
        # self.public_lines: List[Text] = []
        # for plain_attr in self.plain_public_attributes:
        #     try:
        #         attr = getattr(self.obj, plain_attr)
        #     except AttributeError:
        #         # There is a possibility that an attribute returned by dir() will not be accessable via getattr
        #         # ex:
        #         # >>> dir(type)[0]
        #         # '__abstractmethods__'
        #         # >>> getattr(type, dir(type)[0])
        #         # Traceback (most recent call last):
        #         #   File "<stdin>", line 1, in <module>
        #         # AttributeError: __abstractmethods__
        #         self.public_lines.append(Text(plain_attr, style=Style()))
        #     if callable(attr) or attr is None:
        #         self.public_lines.append(
        #             Text(plain_attr, style=Style(dim=True, italic=True))
        #         )
        #     else:
        #         self.public_lines.append(Text(plain_attr, style=Style()))

        # self.private_lines: List[Text] = []
        # for plain_attr in self.plain_private_attributes:
        #     try:
        #         attr = getattr(self.obj, plain_attr)
        #     except AttributeError:
        #         # There is a possibility that an attribute returned by dir() will not be accessable via getattr
        #         # ex:
        #         # >>> dir(type)[0]
        #         # '__abstractmethods__'
        #         # >>> getattr(type, dir(type)[0])
        #         # Traceback (most recent call last):
        #         #   File "<stdin>", line 1, in <module>
        #         # AttributeError: __abstractmethods__
        #         self.private_lines.append(
        #             Text(plain_attr, style=Style(dim=True, italic=True))
        #         )
        #     else:
        #         if callable(attr) or attr is None:
        #             self.private_lines.append(
        #                 Text(plain_attr, style=Style(dim=True, italic=True))
        #             )
        #         else:
        #             self.private_lines.append(Text(plain_attr, style=Style()))

        # # Key:val pair of attribute name and the cached object associated with it
        # self.cached_attributes: Dict[str, CachedObject] = {}

