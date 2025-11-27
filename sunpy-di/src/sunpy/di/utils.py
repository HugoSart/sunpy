from typing import get_origin, get_args, Any, Callable, Union
import inspect
import collections.abc


def is_assignable(entry_cls: type, target) -> bool:
    # Any accepts everything
    if target is Any:
        return True

    origin = get_origin(target)
    # Union[T1, T2, ...]
    if origin is Union:
        return any(is_assignable(entry_cls, t) for t in get_args(target))

    # Callable[..., R] or collections.abc.Callable
    if origin is Callable or target is collections.abc.Callable:
        # entry can be a plain function or a class that is callable
        return inspect.isfunction(entry_cls) or inspect.ismethod(entry_cls) \
            or issubclass_safe(entry_cls, collections.abc.Callable)

    # Parameterized containers like list[T], set[T], dict[K, V]
    # In most DI containers you want the element type, so handle element types specially:
    if origin in {list, set, dict, tuple}:
        # we'll treat a request for list[T] as "find beans assignable to T"
        args = get_args(target)
        if not args:
            return False
        element_target = args[0]
        return is_assignable(entry_cls, element_target)

    # plain class / typing.Type
    if isinstance(target, type):
        return issubclass_safe(entry_cls, target)

    # fallback: for things like typing.Protocol without runtime checks, return False
    return False

def issubclass_safe(cls, klass) -> bool:
    """issubclass but guard against non-class arguments raising TypeError."""
    try:
        return issubclass(cls, klass)
    except Exception:
        return False
