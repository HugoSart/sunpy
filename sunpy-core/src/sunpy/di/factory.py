import inspect
from collections.abc import Callable
from typing import Type, TypeVar, Any, cast

from sunpy.di.context import DIContext

# Refs
T = TypeVar("T")


class DIObjectFactory:

    def __init__(self, context: DIContext) -> None:
        self._context = context

    def create(self, clazz: Type[T] | Callable[[...], T]) -> T:
        params = self.__real_params(clazz.__init__ if clazz is type else clazz)
        if len(params) == 0:
            return cast(Callable[[], T], clazz)()

        # Positional args
        args = []
        kwargs = {}
        for name, t in params:
            arg = self._context.resolve(t)
            kwargs[name] = arg
        return clazz(*args, **kwargs)

    @staticmethod
    def __real_params(factory: Callable[[...], T]) -> list[tuple[str, Any]]:
        sig = inspect.signature(factory)
        params = list(sig.parameters.values())  # remove self
        result = []
        for p in params:
            if p.kind in (p.POSITIONAL_OR_KEYWORD,):
                result.append((p.name, p.annotation))
        return result