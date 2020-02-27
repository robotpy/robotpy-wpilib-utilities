import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MagicInjectError(ValueError):
    pass


def get_injection_requests(
    type_hints: Dict[str, type], cname: str, component: Optional[Any] = None
) -> Dict[str, type]:
    """
    Given a dict of type hints, filter it to the requested injection types.

    :param type_hints: The type hints to inspect.
    :param cname: The component name.
    :param component: The component if it has been instantiated.
    """
    requests = {}

    for n, inject_type in type_hints.items():
        # If the variable is private ignore it
        if n.startswith("_"):
            continue

        # If the variable has been set, skip it
        if hasattr(component, n):
            continue

        # Check for generic types from the typing module
        origin = getattr(inject_type, "__origin__", None)
        if origin is not None:
            inject_type = origin

        # If the type is not actually a type, give a meaningful error
        if not isinstance(inject_type, type):
            raise TypeError(
                f"Component {cname} has a non-type annotation {n}: {inject_type}\n"
                "Lone non-injection variable annotations are disallowed, did you want to assign a static variable?"
            )

        requests[n] = inject_type

    return requests


def find_injections(
    requests: Dict[str, type], injectables: Dict[str, Any], cname: str
) -> Dict[str, Any]:
    """
    Get a dict of the variables to inject into a given component.

    :param requests: The mapping of requested variables to types,
                     as returned by :func:`get_injection_requests`.
    :param injectables: The available variables to inject.
    :param cname: The name of the component.
    """
    to_inject = {}

    for n, inject_type in requests.items():
        injectable = injectables.get(n)
        if injectable is None:
            # Try prefixing the component name
            injectable = injectables.get(f"{cname}_{n}")

        # Raise error if injectable syntax used but no injectable was found.
        if injectable is None:
            raise MagicInjectError(
                "Component %s has variable %s (type %s), which is absent from robot"
                % (cname, n, inject_type)
            )

        # Raise error if injectable declared with type different than the initial type
        if not isinstance(injectable, inject_type):
            raise MagicInjectError(
                "Component %s variable %s does not match type in robot! (Got %s, expected %s)"
                % (cname, n, type(injectable), inject_type)
            )

        to_inject[n] = injectable
        logger.debug("-> %s.%s = %s", cname, n, injectable)

    return to_inject
