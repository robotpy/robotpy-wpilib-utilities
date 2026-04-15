import typing
from typing import ClassVar

import pytest

from magicbot.inject import get_injection_requests
from magicbot.magic_tunable import tunable


def test_ctor_invalid_type_hint_message():
    """
    class Component:
        def __init__(self, foo: 1): ...
    """
    type_hints = {
        "foo": typing.cast(type, 1),
    }

    with pytest.raises(TypeError) as exc_info:
        get_injection_requests(type_hints, "bar")

    assert exc_info.value.args[0] == "Component bar has a non-type annotation foo: 1"


def test_component_classvar_annotation_is_not_treated_as_injection_request():
    class Component:
        injected: int
        state_names: ClassVar[int]

    requests = get_injection_requests(
        typing.get_type_hints(Component), "component", Component()
    )

    assert requests == {"injected": int}


def test_component_tunable_annotation_is_not_treated_as_injection_request():
    class Component:
        injected: int
        speed: tunable[float] = tunable(0.0)

    requests = get_injection_requests(
        typing.get_type_hints(Component), "component", Component()
    )

    assert requests == {"injected": int}
