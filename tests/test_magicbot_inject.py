import typing

import pytest

from magicbot.inject import get_injection_requests


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
