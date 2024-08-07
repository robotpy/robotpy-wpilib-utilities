import collections.abc
import functools
import inspect
import typing
import warnings
from typing import Callable, Generic, Optional, Sequence, TypeVar, Union, overload

import ntcore
from ntcore import NetworkTableInstance
from ntcore.types import ValueT


class StructSerializable(typing.Protocol):
    """Any type that is a wpiutil.wpistruct."""

    WPIStruct: typing.ClassVar


T = TypeVar("T")
V = TypeVar("V", bound=Union[ValueT, StructSerializable, Sequence[StructSerializable]])


class tunable(Generic[V]):
    """
    This allows you to define simple properties that allow you to easily
    communicate with other programs via NetworkTables.

    The following example will define a NetworkTable variable at
    ``/components/my_component/foo``::

        class MyRobot(magicbot.MagicRobot):

            my_component: MyComponent

        ...

        from magicbot import tunable

        class MyComponent:

            # define the tunable property
            foo = tunable(True)

            def execute(self):

                # set the variable
                self.foo = True

                # get the variable
                foo = self.foo

    The key of the NetworkTables variable will vary based on what kind of
    object the decorated method belongs to:

    * A component: ``/components/COMPONENTNAME/VARNAME``
    * An autonomous mode: ``/autonomous/MODENAME/VARNAME``
    * Your main robot class: ``/robot/VARNAME``

    .. note:: When executing unit tests on objects that create tunables,
              you will want to use setup_tunables to set the object up.
              In normal usage, MagicRobot does this for you, so you don't
              have to do anything special.

    .. versionchanged:: 2024.1.0
       Added support for WPILib Struct serializable types.
       Integer defaults now create integer topics instead of double topics.
    """

    # the way this works is we use a special class to indicate that it
    # is a tunable, and MagicRobot adds _ntattr and _global_table variables
    # to the class property

    # The tricky bit is that you need to do late binding on these, because
    # the networktables key is not known when the object is created. Instead,
    # the name of the key is related to the name of the variable name in the
    # robot class

    __slots__ = (
        "_ntdefault",
        "_ntsubtable",
        "_ntwritedefault",
        # "__doc__",
        "_topic_type",
        "_nt",
    )

    def __init__(
        self,
        default: V,
        *,
        writeDefault: bool = True,
        subtable: Optional[str] = None,
        doc=None,
    ) -> None:
        if doc is not None:
            warnings.warn("tunable no longer uses the doc argument", stacklevel=2)

        self._ntdefault = default
        self._ntsubtable = subtable
        self._ntwritedefault = writeDefault
        # self.__doc__ = doc

        self._topic_type = _get_topic_type_for_value(self._ntdefault)
        if self._topic_type is None:
            checked_type: type = type(self._ntdefault)
            raise TypeError(
                f"tunable is not publishable to NetworkTables, type: {checked_type.__name__}"
            )

    @overload
    def __get__(self, instance: None, owner=None) -> "tunable[V]": ...

    @overload
    def __get__(self, instance, owner=None) -> V: ...

    def __get__(self, instance, owner=None):
        if instance is not None:
            return instance._tunables[self].get()
        return self

    def __set__(self, instance, value: V) -> None:
        instance._tunables[self].set(value)


def _get_topic_type_for_value(value) -> Optional[Callable[[ntcore.Topic], typing.Any]]:
    topic_type = _get_topic_type(type(value))
    # bytes and str are Sequences. They must be checked before Sequence.
    if topic_type is None and isinstance(value, collections.abc.Sequence):
        if not value:
            raise ValueError(
                f"tunable default cannot be an empty sequence, got {value}"
            )
        topic_type = _get_topic_type(Sequence[type(value[0])])  # type: ignore [misc]
    return topic_type


def setup_tunables(component, cname: str, prefix: Optional[str] = "components") -> None:
    """
    Connects the tunables on an object to NetworkTables.

    :param component:   Component object
    :param cname:       Name of component
    :param prefix:      Prefix to use, or no prefix if None

    .. note:: This is not needed in normal use, only useful
              for testing
    """

    cls = component.__class__

    if prefix is None:
        prefix = "/%s" % cname
    else:
        prefix = "/%s/%s" % (prefix, cname)

    NetworkTables = NetworkTableInstance.getDefault()

    tunables: dict[tunable, ntcore.Topic] = {}

    for n in dir(cls):
        if n.startswith("_"):
            continue

        prop = getattr(cls, n)
        if not isinstance(prop, tunable):
            continue

        if prop._ntsubtable:
            key = "%s/%s/%s" % (prefix, prop._ntsubtable, n)
        else:
            key = "%s/%s" % (prefix, n)

        topic = prop._topic_type(NetworkTables.getTopic(key))
        ntvalue = topic.getEntry(prop._ntdefault)
        if prop._ntwritedefault:
            ntvalue.set(prop._ntdefault)
        else:
            ntvalue.setDefault(prop._ntdefault)
        tunables[prop] = ntvalue

    component._tunables = tunables


@overload
def feedback(f: Callable[[T], V]) -> Callable[[T], V]: ...


@overload
def feedback(*, key: str) -> Callable[[Callable[[T], V]], Callable[[T], V]]: ...


def feedback(f=None, *, key: Optional[str] = None) -> Callable:
    """
    This decorator allows you to create NetworkTables values that are
    automatically updated with the return value of a method.

    ``key`` is an optional parameter, and if it is not supplied,
    the key will default to the method name with a leading ``get_`` removed.
    If the method does not start with ``get_``, the key will be the full
    name of the method.

    The key of the NetworkTables value will vary based on what kind of
    object the decorated method belongs to:

    * A component: ``/components/COMPONENTNAME/VARNAME``
    * Your main robot class: ``/robot/VARNAME``

    The NetworkTables value will be auto-updated in all modes.

    .. warning:: The function should only act as a getter, and must not
                 take any arguments (other than self).

    Example::

        from magicbot import feedback

        class MyComponent:
            navx: ...

            @feedback
            def get_angle(self):
                return self.navx.getYaw()

        class MyRobot(magicbot.MagicRobot):
            my_component: MyComponent

            ...

    In this example, the NetworkTable key is stored at
    ``/components/my_component/angle``.

    .. seealso:: :class:`~wpilib.LiveWindow` may suit your needs,
                 especially if you wish to monitor WPILib objects.

    .. versionadded:: 2018.1.0

    .. versionchanged:: 2024.1.0
       WPILib Struct serializable types are supported when the return type is type hinted.
       An ``int`` return type hint now creates an integer topic.
    """
    if f is None:
        return functools.partial(feedback, key=key)

    if not callable(f):
        raise TypeError(f"Illegal use of feedback decorator on non-callable {f!r}")
    sig = inspect.signature(f)
    name = f.__name__

    if len(sig.parameters) != 1:
        raise ValueError(
            f"{name} may not take arguments other than 'self' (must be a simple getter method)"
        )

    # Set attributes to be checked during injection
    f._magic_feedback = True
    f._magic_feedback_key = key

    return f


_topic_types = {
    bool: ntcore.BooleanTopic,
    int: ntcore.IntegerTopic,
    float: ntcore.DoubleTopic,
    str: ntcore.StringTopic,
    bytes: ntcore.RawTopic,
}
_array_topic_types = {
    bool: ntcore.BooleanArrayTopic,
    int: ntcore.IntegerArrayTopic,
    float: ntcore.DoubleArrayTopic,
    str: ntcore.StringArrayTopic,
}


def _get_topic_type(
    return_annotation,
) -> Optional[Callable[[ntcore.Topic], typing.Any]]:
    if return_annotation in _topic_types:
        return _topic_types[return_annotation]
    if hasattr(return_annotation, "WPIStruct"):
        return lambda topic: ntcore.StructTopic(topic, return_annotation)

    # Check for PEP 484 generic types
    origin = getattr(return_annotation, "__origin__", None)
    args = typing.get_args(return_annotation)
    if origin in (list, tuple, collections.abc.Sequence) and args:
        # Ensure tuples are tuple[T, ...] or homogenous
        if origin is tuple and not (
            (len(args) == 2 and args[1] is Ellipsis) or len(set(args)) == 1
        ):
            return None

        inner_type = args[0]
        if inner_type in _array_topic_types:
            return _array_topic_types[inner_type]
        if hasattr(inner_type, "WPIStruct"):
            return lambda topic: ntcore.StructArrayTopic(topic, inner_type)


def collect_feedbacks(component, cname: str, prefix: Optional[str] = "components"):
    """
    Finds all methods decorated with :func:`feedback` on an object
    and returns a list of 2-tuples (method, NetworkTables entry setter).

    .. note:: This isn't useful for normal use.
    """
    if prefix is None:
        prefix = "/%s" % cname
    else:
        prefix = "/%s/%s" % (prefix, cname)

    nt = NetworkTableInstance.getDefault().getTable(prefix)
    feedbacks = []

    for name, method in inspect.getmembers(component, inspect.ismethod):
        if getattr(method, "_magic_feedback", False):
            key = method._magic_feedback_key
            if key is None:
                if name.startswith("get_"):
                    key = name[4:]
                else:
                    key = name

            return_annotation = typing.get_type_hints(method).get("return", None)
            if return_annotation is not None:
                topic_type = _get_topic_type(return_annotation)
            else:
                topic_type = None

            if topic_type is None:
                entry = nt.getEntry(key)
                setter = entry.setValue
            else:
                publisher = topic_type(nt.getTopic(key)).publish()
                setter = publisher.set

            feedbacks.append((method, setter))

    return feedbacks
