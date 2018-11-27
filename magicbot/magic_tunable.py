import functools
import inspect

from networktables import NetworkTables
from ntcore.value import Value

# Only used as a marker
class _TunableProperty(property):
    pass


class _AutosendProperty(_TunableProperty):
    pass


def tunable(default, *, writeDefault=True, subtable=None, doc=None):
    """
        This allows you to define simple properties that allow you to easily
        communicate with other programs via NetworkTables.
    
        The following example will define a NetworkTable variable at
        ``/components/my_component/foo``::
        
            class MyRobot(magicbot.MagicRobot):
            
                my_component = MyComponent
        
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
    """

    # the way this works is we use a special class to indicate that it
    # is a tunable, and MagicRobot adds _ntattr and _global_table variables
    # to the class property

    # The tricky bit is that you need to do late binding on these, because
    # the networktables key is not known when the object is created. Instead,
    # the name of the key is related to the name of the variable name in the
    # robot class

    nt = NetworkTables
    mkv = Value.getFactory(default)

    def _get(self):
        return getattr(self, prop._ntattr).value

    def _set(self, value):
        v = getattr(self, prop._ntattr)
        nt._api.setEntryValueById(v._local_id, mkv(value))

    prop = _TunableProperty(fget=_get, fset=_set, doc=doc)
    prop._ntdefault = default
    prop._ntsubtable = subtable
    prop._ntwritedefault = writeDefault

    return prop


def setup_tunables(component, cname, prefix="components"):
    """
        Connects the tunables on an object to NetworkTables.

        :param component:   Component object
        :param cname:       Name of component
        :type cname: str
        :param prefix:      Prefix to use, or no prefix if None
        :type prefix: str    
    
        .. note:: This is not needed in normal use, only useful
                  for testing
    """

    cls = component.__class__

    if prefix is None:
        prefix = "/%s" % cname
    else:
        prefix = "/%s/%s" % (prefix, cname)

    for n in dir(cls):
        if n.startswith("_"):
            continue

        prop = getattr(cls, n)
        if not isinstance(prop, _TunableProperty):
            continue

        if prop._ntsubtable:
            key = "%s/%s/%s" % (prefix, prop._ntsubtable, n)
        else:
            key = "%s/%s" % (prefix, n)

        ntattr = "_Tunable__%s" % n

        ntvalue = NetworkTables.getGlobalAutoUpdateValue(
            key, prop._ntdefault, prop._ntwritedefault
        )
        # double indirection
        setattr(component, ntattr, ntvalue)
        prop._ntattr = ntattr


def feedback(f=None, *, key: str = None):
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

    .. seealso:: :class:`~wpilib.livewindow.LiveWindow` may suit your needs,
                 especially if you wish to monitor WPILib objects.

    .. versionadded:: 2018.1.0
    """
    if f is None:
        return functools.partial(feedback, key=key)

    if not callable(f):
        raise TypeError(
            "Illegal use of feedback decorator on non-callable {!r}".format(f)
        )
    sig = inspect.signature(f)
    name = f.__name__

    if len(sig.parameters) != 1:
        raise ValueError(
            "{} may not take arguments other than 'self' (must be a simple getter method)".format(
                name
            )
        )

    # Set attributes to be checked during injection
    f._magic_feedback = True
    f._magic_feedback_key = key

    return f


def collect_feedbacks(component, cname: str, prefix="components"):
    """
    Finds all methods decorated with :func:`feedback` on an object
    and returns a list of 2-tuples (method, NetworkTables entry).

    .. note:: This isn't useful for normal use.
    """
    if prefix is None:
        prefix = "/%s" % cname
    else:
        prefix = "/%s/%s" % (prefix, cname)

    nt = NetworkTables.getTable(prefix)
    feedbacks = []

    for name, method in inspect.getmembers(component, inspect.ismethod):
        if getattr(method, "_magic_feedback", False):
            key = method._magic_feedback_key
            if key is None:
                if name.startswith("get_"):
                    key = name[4:]
                else:
                    key = name

            entry = nt.getEntry(key)
            feedbacks.append((method, entry))

    return feedbacks
