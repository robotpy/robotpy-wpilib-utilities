from __future__ import annotations

import collections.abc
import inspect
import typing
import warnings
from collections.abc import Mapping, Sequence
from typing import Callable, Generic, TypeVar, overload

if typing.TYPE_CHECKING:
    try:
        from typing import Self
    except ImportError:
        from typing_extensions import Self

import ntcore
from ntcore import NetworkTableInstance
from ntcore.types import ValueT
from wpiutil.wpistruct.typing import StructSerializable, is_wpistruct_type

T = TypeVar("T")
V = TypeVar("V", bound=ValueT | StructSerializable | Sequence[StructSerializable])
JsonPrimitive = bool | float | str
JsonValue = JsonPrimitive | list[JsonPrimitive] | tuple[JsonPrimitive, ...]


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

    .. versionchanged:: 2026.1.0
       Added support for publishing JSON topic properties.
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
        "_topic_properties",
        # "__doc__",
        "__orig_class__",
        "_topic_type",
        "_nt",
    )

    def __init__(
        self,
        default: V,
        *,
        writeDefault: bool = True,
        subtable: str | None = None,
        properties: Mapping[str, JsonValue] | None = None,
        doc=None,
    ) -> None:
        if doc is not None:
            warnings.warn("tunable no longer uses the doc argument", stacklevel=2)

        self._ntdefault = default
        self._ntsubtable = subtable
        self._ntwritedefault = writeDefault
        self._topic_properties = properties
        # self.__doc__ = doc

        # Defer checks for empty sequences to check type hints.
        # Report errors here when we can so the error points to the tunable line.
        if default or not isinstance(default, collections.abc.Sequence):
            topic_type = _get_topic_type_for_value(default)
            if topic_type is None:
                checked_type: type = type(default)
                raise TypeError(
                    f"tunable is not publishable to NetworkTables, type: {checked_type.__name__}"
                )
            self._topic_type = topic_type

    def with_properties(self, **kwargs: JsonValue) -> Self:
        self._topic_properties = kwargs
        return self

    def __set_name__(self, owner: type, name: str) -> None:
        type_hint: type | None = None
        # __orig_class__ is set after __init__, check it here.
        orig_class = getattr(self, "__orig_class__", None)
        if orig_class is not None:
            # Accept field = tunable[Sequence[int]]([])
            type_hint = typing.get_args(orig_class)[0]
        else:
            type_hint = typing.get_type_hints(owner).get(name)
            origin = typing.get_origin(type_hint)
            if origin is typing.ClassVar:
                # Accept field: ClassVar[tunable[Sequence[int]]] = tunable([])
                type_hint = typing.get_args(type_hint)[0]
                origin = typing.get_origin(type_hint)
            if origin is tunable:
                # Accept field: tunable[Sequence[int]] = tunable([])
                type_hint = typing.get_args(type_hint)[0]

        if type_hint is not None:
            topic_type = _get_topic_type(type_hint)
        else:
            topic_type = _get_topic_type_for_value(self._ntdefault)

        if topic_type is None:
            checked_type: type = type_hint or type(self._ntdefault)
            raise TypeError(
                f"tunable is not publishable to NetworkTables, type: {checked_type.__name__}"
            )

        self._topic_type = topic_type

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


def _get_topic_type_for_value(value) -> Callable[[ntcore.Topic], typing.Any] | None:
    topic_type = _get_topic_type(type(value))
    # bytes and str are Sequences. They must be checked before Sequence.
    if topic_type is None and isinstance(value, collections.abc.Sequence):
        if not value:
            raise ValueError(
                f"tunable default cannot be an empty sequence, got {value}"
            )
        topic_type = _get_topic_type(Sequence[type(value[0])])  # type: ignore [misc]
    return topic_type


def setup_tunables(component, cname: str, prefix: str | None = "components") -> None:
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
        prefix = f"/{cname}"
    else:
        prefix = f"/{prefix}/{cname}"

    NetworkTables = NetworkTableInstance.getDefault()

    tunables: dict[tunable, ntcore.Topic] = {}

    for n in dir(cls):
        if n.startswith("_"):
            continue

        prop = getattr(cls, n)
        if not isinstance(prop, tunable):
            continue

        if prop._ntsubtable:
            key = f"{prefix}/{prop._ntsubtable}/{n}"
        else:
            key = f"{prefix}/{n}"

        topic = NetworkTables.getTopic(key)
        typed_topic = prop._topic_type(topic)
        ntvalue = typed_topic.getEntry(prop._ntdefault)
        if prop._ntwritedefault:
            ntvalue.set(prop._ntdefault)
        else:
            ntvalue.setDefault(prop._ntdefault)
        if prop._topic_properties is not None:
            topic.setProperties(prop._topic_properties)
        tunables[prop] = ntvalue

    component._tunables = tunables


class _FeedbackDecorator:
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
            def get_angle(self) -> float:
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

    .. versionchanged:: 2026.1.0
       Added support for JSON topic properties for type hinted feedback methods.
    """

    __slots__ = ("_key", "_properties")

    def __init__(
        self,
        *,
        key: str | None = None,
        properties: Mapping[str, JsonValue] | None = None,
    ) -> None:
        self._key = key
        self._properties = properties

    @overload
    def __call__(self, f: Callable[[T], V]) -> Callable[[T], V]: ...

    @overload
    def __call__(
        self,
        *,
        key: str | None = None,
        properties: Mapping[str, JsonValue] | None = None,
    ) -> _FeedbackDecorator: ...

    def __call__(
        self,
        f=None,
        *,
        key: str | None = None,
        properties: Mapping[str, JsonValue] | None = None,
    ) -> Callable:
        if f is None:
            return _FeedbackDecorator(key=key, properties=properties)

        if not callable(f):
            raise TypeError(
                f"Illegal use of feedback decorator on non-callable {f!r}"
            )
        sig = inspect.signature(f)
        name = f.__name__

        if len(sig.parameters) != 1:
            raise ValueError(
                f"{name} may not take arguments other than 'self' (must be a simple getter method)"
            )

        f._magic_feedback = (self._key, self._properties)
        return f

    def with_properties(self, **kwargs: JsonValue) -> _FeedbackDecorator:
        return _FeedbackDecorator(key=self._key, properties=kwargs)


feedback = _FeedbackDecorator()


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


def _get_topic_type(return_annotation) -> Callable[[ntcore.Topic], typing.Any] | None:
    if return_annotation in _topic_types:
        return _topic_types[return_annotation]
    if is_wpistruct_type(return_annotation):
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
        if is_wpistruct_type(inner_type):
            return lambda topic: ntcore.StructArrayTopic(topic, inner_type)

    return None


def collect_feedbacks(component, cname: str, prefix: str | None = "components"):
    """
    Finds all methods decorated with :func:`feedback` on an object
    and returns a list of 2-tuples (method, NetworkTables entry setter).

    .. note:: This isn't useful for normal use.
    """
    if prefix is None:
        prefix = f"/{cname}"
    else:
        prefix = f"/{prefix}/{cname}"

    nt = NetworkTableInstance.getDefault().getTable(prefix)
    feedbacks = []

    for name, method in inspect.getmembers(component, inspect.ismethod):
        feedback_params = getattr(method, "_magic_feedback", None)
        if feedback_params is not None:
            key, topic_properties = feedback_params
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
                topic = nt.getTopic(key)
                publisher = topic_type(topic).publish()
                setter = publisher.set
                if topic_properties is not None:
                    topic.setProperties(topic_properties)

            feedbacks.append((method, setter))

    return feedbacks
