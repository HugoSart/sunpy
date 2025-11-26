import inspect
from typing import Type, TypeVar, Any, get_origin, get_args

from sunpy.di import utils
from sunpy.di.context import DIContext

# Refs
T = TypeVar("T")


class DIObjectFactory:

    def __init__(self, context: DIContext) -> None:
        self._context = context

    def create(self, clazz: Type[T]) -> T:
        params = self.__real_params(clazz)
        if len(params) == 0:
            return clazz()

        # Positional args
        args = []
        kwargs = {}
        for name, t in params:
            arg = self._context.resolve_many(get_args(t)[0]) if get_origin(t) == list \
                else self._context.resolve_single(t)
            kwargs[name] = arg
        return clazz(*args, **kwargs)

    @staticmethod
    def __real_params(clazz: Type[T]) -> list[tuple[str, Any]]:
        sig = inspect.signature(clazz.__init__)
        params = list(sig.parameters.values())[1:]  # remove self
        result = []
        for p in params:
            if p.kind in (p.POSITIONAL_OR_KEYWORD,):
                result.append((p.name, p.annotation))
        return result