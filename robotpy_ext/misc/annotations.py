def get_class_annotations(cls):
    """Get variable annotations in a class, inheriting from superclasses."""
    result = {}
    for base in reversed(cls.__mro__):
        result.update(getattr(base, "__annotations__", {}))
    return result
