from typing import Any, Dict, Generic, TypeVar, overload

V = TypeVar("V")

class will_reset_to(Generic[V]):
    def __init__(self, default: V) -> None: ...
    # we don't really have __get__, but this makes code in methods using these
    # to type-check, whilst giving correct behaviour for code at the class level
    @overload
    def __get__(self, instance: None, owner=None) -> will_reset_to: ...
    @overload
    def __get__(self, instance, owner=None) -> V: ...

def collect_resets(cls: type) -> Dict[str, Any]: ...
