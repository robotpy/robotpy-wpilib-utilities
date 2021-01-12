"""
    Taken from the python documentation, distributed under
    that same license
"""

import collections


class OrderedClass(type):
    """
    Metaclass that stores class attributes in a member called
    'members'. If you subclass something that uses this metaclass,
    the base class members will be listed before the subclass
    """

    # TODO: this isn't required in Python 3.6 due to PEP 520

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        return collections.OrderedDict()

    def __new__(cls, name, bases, namespace, **kwds):
        result = type.__new__(cls, name, bases, dict(namespace))

        members = []
        members.extend(getattr(result, "members", ()))

        # because of the potential of multiple inheritance/mixins, need
        # to grab members list from all bases
        for base in bases:
            members.extend(getattr(base, "members", ()))

        members.extend(namespace)

        seen = set()
        result.members = tuple(m for m in members if not (m in seen or seen.add(m)))
        return result
