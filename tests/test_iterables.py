
from unittest.mock import MagicMock

# class MyIterable(list):
#     def __init__(self) -> None:
#         self.a = 'a'
#         self.b = 'b'
#         self.c = 'c'
        
#     def __iter__(self):
#         yield self.a
#         yield self.b
#         yield self.c
        
#     def __repr__(self) -> str:
#         return f"MyIterable([{self.a}, {self.b}, {self.c})"


class Wrapper:
    def __init__(self) -> None:
        self.thing = ...
    
    def foo(self):
        print('foo')


if __name__ == "__main__":
    import objexplore
    abc = Wrapper()
    abc.foo = MagicMock()
    abc.foo('hello', 'world')
    abc.foo('goodbye', 'world')
    wrapper = Wrapper()
    wrapper.foo = MagicMock()
    wrapper.foo('hello', 'world')
    wrapper.foo('goodbye', 'world')
    objexplore.explore(abc)