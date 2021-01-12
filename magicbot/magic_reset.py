from typing import Any, Dict


class will_reset_to:
    """
    This marker indicates that this variable on a component will
    be reset to a default value after each time that execute is
    called.

    Example usage::

        class Component:

            foo = will_reset_to(False)

            def control_fn(self):
                self.foo = True

            def execute(self):
                if self.foo:
                    # ...

                # after this function is executed, foo is reset
                # back to the default value (False)


    .. note:: This will only work for MagicRobot components

    .. warning:: This will not work on classes that set ``__slots__``.
    """

    __slots__ = ("default",)

    def __init__(self, default):
        self.default = default


def collect_resets(cls: type) -> Dict[str, Any]:
    """
    Get all the ``will_reset_to`` variables and their values from a class.

    .. note:: This isn't useful for normal use.
    """

    result = {}

    for n in dir(cls):
        v = getattr(cls, n)
        if isinstance(v, will_reset_to):
            result[n] = v.default

    return result
