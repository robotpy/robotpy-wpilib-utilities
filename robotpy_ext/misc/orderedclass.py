'''
    Taken from the python documentation, distributed under
    that same license
'''

import collections

class OrderedClass(type):
    '''
        Metaclass that stores class attributes in a member called
        'members'. If you subclass something that uses this metaclass,
        the base class members will be listed before the subclass
    '''

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        return collections.OrderedDict()

    def __new__(cls, name, bases, namespace, **kwds):
        result = type.__new__(cls, name, bases, dict(namespace))
        members = getattr(result, 'members', ())
        result.members = members + tuple(namespace)
        return result
