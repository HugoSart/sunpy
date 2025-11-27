import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar, Type, Generic, get_origin, get_args, Self, get_type_hints

from sunpy.di import utils
from sunpy.di.scopes import DIScope

# Refs
T = TypeVar("T")


@dataclass(frozen=True)
class DIRegistryEntry(Generic[T]):
    clazz: Type[T]
    factory: Callable[[...], T]
    scope: DIScope
    name: str
    lazy: bool = False
    primary: bool = False
    order: int | None = None

    def __eq__(self, other: Self) -> bool:
        return (self.order, self.name) == (other.order, other.name)

    def __lt__(self, other: Self) -> bool:
        if self.order == other.order:
            return self.name < other.name
        return self.order < other.order


class DIContext:

    def __init__(self):
        self._registry: dict[str, DIRegistryEntry] = {}
        self._ordered_registry: list[DIRegistryEntry] = []
        self._singleton_instances: dict[Type, object] = {}

        from sunpy.di.factory import DIObjectFactory
        self._factory = DIObjectFactory(self)

    @property
    def registry(self) -> dict[str, DIRegistryEntry]:
        return self._registry

    def register(self, clazz: Type[T], scope: DIScope = DIScope.SINGLETON, primary: bool = False,
                 order: int | None = None, lazy: bool = False, name: str | None = None) -> None:
        is_method = inspect.isfunction(clazz) or inspect.ismethod(clazz)
        actual_name = name or clazz.__name__
        covered_type = get_type_hints(clazz).get('return', None) if is_method else clazz
        entry = DIRegistryEntry(
            clazz=covered_type,
            factory=clazz if is_method else clazz.__init__,
            scope=scope,
            name=actual_name,
            primary=primary,
            order=order,
            lazy=lazy,
        )

        # Validate entry
        if actual_name in self._registry:
            raise ValueError('Component "%s" already registered' % actual_name)

        # Register entry
        self._registry[actual_name] = entry
        self._ordered_registry.append(entry)
        self._ordered_registry.sort()

    def find_all_entries_assignable_from(self, clazz: Type[T]) -> list[DIRegistryEntry[T]]:
        try:
            return [entry for entry in self._ordered_registry if utils.is_assignable(entry.clazz, clazz)]
        except Exception:
            print('Failed to find components for type "%s"' % clazz.__name__)
            raise

    def resolve(self, clazz: Type[T], scope: DIScope | None = None, name: str | None = None) -> T:
        if get_origin(clazz) == list:
            t = get_args(clazz)[0]
            return [self.resolve(e.clazz, scope=scope, name=e.name)
                    for e in self.find_all_entries_assignable_from(t)]
        if get_origin(clazz) == set:
            t = get_args(clazz)[0]
            return {self.resolve(e.clazz, scope=scope, name=e.name)
                    for e in self.find_all_entries_assignable_from(t)}
        if get_origin(clazz) == dict:
            kt = get_args(clazz)[0]
            if not kt is str:
                raise ValueError('Dict injection should have string keys, but found: %s' % kt.__name__)
            vt = get_args(clazz)[1]
            return {e.name: self.resolve(e.clazz, scope=scope, name=e.name)
                    for e in self.find_all_entries_assignable_from(vt)}

        # Find entry or fallback to a parent entry
        name = name or self.__sunpy_name(clazz)
        entry = self._registry.get(name)
        if entry is None:
            entries = self.find_all_entries_assignable_from(clazz)
            if len(entries) == 0:
                raise ValueError('Component "%s" not registered' % name)
            elif len(entries) == 1:
                entry = self._registry.get(entries[0].name)
            else:
                primary = [entry for entry in entries if self._registry.get(entry.name).primary]
                if len(primary) == 0:
                    raise ValueError('%s components were found, but none of them is primary of "%s"'
                                     % (len(entries), name))
                if len(primary) > 1:
                    raise ValueError('Multiple primary components found for "%s"' % name)
                entry = self._registry.get(primary[0].name)

        # Instantiate
        if not entry:
            raise ValueError('Bean not found for type %s' % name)
        return self.__instantiate_based_on_scope(entry, scope)

    def __instantiate_based_on_scope(self, entry: DIRegistryEntry, scope: DIScope | None = None) -> T:
        clazz = entry.clazz
        scope = scope or entry.scope

        # Singleton impl
        if scope == DIScope.SINGLETON:
            if clazz not in self._singleton_instances:
                self._singleton_instances[clazz] = self._factory.create(clazz)
            return self._singleton_instances[clazz]

        # Prototype impl
        if scope == DIScope.PROTOTYPE:
            return self._factory.create(clazz)

        # Unknown scope impl
        raise ValueError('Unknown scope')

    def __sunpy_name(self, clazz: Type[T]) -> str:
        return ('' if not hasattr(clazz, '__sunpy__name__') else clazz.__sunpy_name__) or clazz.__name__
