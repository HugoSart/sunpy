from dataclasses import dataclass
from typing import TypeVar, Type, Generic

from sunpy.di.scopes import DIScope

# Refs
T = TypeVar("T")


@dataclass(frozen=True)
class DIRegistryEntry(Generic[T]):
    clazz: Type[T]
    scope: DIScope
    name: str
    primary: bool = False


class DIContext:

    def __init__(self):
        self._registry: dict[Type, DIRegistryEntry] = {}
        self._singleton_instances: dict[Type, object] = {}
        from sunpy.di.factory import DIObjectFactory
        self._factory = DIObjectFactory(self)

    @property
    def registry(self) -> dict[Type, DIRegistryEntry]:
        return self._registry

    def register(self, clazz: Type[T], scope: DIScope = DIScope.SINGLETON, primary: bool = False,
                 name: str | None = None) -> None:
        if clazz in self._registry:
            raise ValueError('Bean already registered')
        entry = DIRegistryEntry(
            clazz=clazz,
            scope=scope,
            name=name or clazz.__name__,
            primary=primary,
        )
        self._registry[clazz] = entry

    def find_all_classes_assignable_from(self, clazz: Type[T]) -> list[Type[T]]:
        try:
            return [entry.clazz for entry in self._registry.values() if issubclass(entry.clazz, clazz)]
        except Exception as e:
            print('Failed to find classes for type "%s"' % clazz.__name__)
            raise

    def resolve_single(self, clazz: Type[T], scope: DIScope | None = None) -> T:

        # Find entry or fallback to a parent entry
        entry = self._registry.get(clazz)
        if entry is None:
            classes = self.find_all_classes_assignable_from(clazz)
            if len(classes) == 0:
                raise ValueError('Bean not registered')
            elif len(classes) == 1:
                entry = self._registry.get(classes[0])
            else:
                primary = [entry for entry in classes if self._registry.get(entry).primary]
                if len(primary) == 0:
                    raise ValueError('No primary bean found')
                if len(primary) > 1:
                    raise ValueError('Multiple primary beans found')
                entry = self._registry.get(primary[0])

        # Instantiate
        return self.__instantiate_based_on_scope(entry, scope)

    def resolve_many(self, clazz: Type[T], scope: DIScope | None = None) -> list[T]:
        classes = self.find_all_classes_assignable_from(clazz)
        return [self.resolve_single(clazz, scope) for clazz in classes]

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
