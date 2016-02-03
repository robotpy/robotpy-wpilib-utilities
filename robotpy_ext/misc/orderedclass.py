'''
    Taken from the python documentation, distributed under
    that same license
'''

import collections

class OrderedClass(type):
    '''
        Metaclass that stores class attributes in a member called
        'members'
    '''

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        return collections.OrderedDict()

    def __new__(cls, name, bases, namespace, **kwds):
        result = type.__new__(cls, name, bases, dict(namespace))
        result.members = tuple(namespace)
        return result