
from networktables import NetworkTable

# Only used as a marker
class _TunableProperty(property):
    pass

class _AutosendProperty(_TunableProperty):
    pass

def tunable(default, *, writeDefault=True, subtable=None):
    '''
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
    '''
    
    # the way this works is we use a special class to indicate that it
    # is a tunable, and MagicRobot adds _ntattr and _global_table variables
    # to the class property
    
    # The tricky bit is that you need to do late binding on these, because
    # the networktables key is not known when the object is created. Instead,
    # the name of the key is related to the name of the variable name in the
    # robot class
    
    def _get(self):
        return getattr(self, prop._ntattr).value
    
    def _set(self, value):
        v = getattr(self, prop._ntattr)
        prop._global_table.putValue(v.key, value)
        v._AutoUpdateValue__value = value
    
    prop = _TunableProperty(fget=_get, fset=_set)
    prop._ntdefault = default
    prop._ntsubtable = subtable
    prop._ntwritedefault = writeDefault
    
    return prop 


def setup_tunables(component, cname, prefix='components'):
    '''
        Connects the tunables on an object to NetworkTables.

        :param component:   Component object
        :param cname:       Name of component
        :type cname: str
        :param prefix:      Prefix to use, or no prefix if None
        :type prefix: str    
    
        .. note:: This is not needed in normal use, only useful
                  for testing
    '''
    
    gtable = NetworkTable.getGlobalTable()
    cls = component.__class__

    if prefix is None:
        prefix = '/%s' % cname
    else:
        prefix = '/%s/%s' % (prefix, cname)
    
    for n in dir(cls):
        if n.startswith('_'):
            continue
    
        prop = getattr(cls, n)
        if not isinstance(prop, _TunableProperty):
            continue
        
        if prop._ntsubtable:
            key = '%s/%s/%s' % (prefix, prop._ntsubtable, n)
        else:
            key = '%s/%s' % (prefix, n)
        
        ntattr = '_Tunable__%s' % n
        
        ntvalue = NetworkTable.getGlobalAutoUpdateValue(key,
                                                        prop._ntdefault,
                                                        prop._ntwritedefault)
        # double indirection
        setattr(component, ntattr, ntvalue)
        prop._ntattr = ntattr
        prop._global_table = gtable


# TODO
#def autosend(f=None):
#    '''
#        Decorator used to send variables to DS::
#        
#            
#        
#            class MyComponent:
#            
#                @autosend
#                def my_sensor(self):
#                    return self.limit_switch.get()
#                    
#                ...
#                    
#            class MyRobot:
#            
#                mine = MyComponent 
#                
#        This will cause the output of this function to be sent
#        to ``/components/mine/my_sensor``
#    '''
#    
#    
#    def _get(self):
#        return self._Magicbot__autosend.get(f)
#    
#    prop = _AutosendProperty(fget=_get)
#    prop.f = f
#    
#    return prop
