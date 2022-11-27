from typing import Any, Generic, TypeVar, overload

_V = TypeVar("_V")

class will_reset_to(Generic[_V]):
    default: _V

    def __init__(self, default: _V) -> None: ...
    # we don't really have __get__, but this makes code in methods using these
    # to type-check, whilst giving correct behaviour for code at the class level
    @overload
    def __get__(self, instance: None, owner=...) -> will_reset_to: ...
    @overload
    def __get__(self, instance, owner=...) -> _V: ...
    def __set__(self, instance, value: _V) -> None: ...

def collect_resets(cls: type) -> dict[str, Any]: ...
