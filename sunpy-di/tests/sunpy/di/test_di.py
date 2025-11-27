from sunpy.di.context import DIContext


class _Dep:
    pass


class _DepChild(_Dep):
    pass


class _DepOtherChild(_Dep):
    pass


class _FuncDep:
    pass


def dep() -> _FuncDep:
    return _FuncDep()


class _ComplexDep:
    def __init__(self, dep_single: _DepOtherChild, dep_list: list[_Dep], dep_func: _FuncDep):
        self._dep_single = dep_single
        self._dep_list = dep_list
        self._dep_func = dep_func


class _Config:

    @staticmethod
    def static_dep() -> _FuncDep:
        return _FuncDep()

    @classmethod
    def class_dep(cls) -> _FuncDep:
        return _FuncDep()


def test_single() -> None:
    context = DIContext()
    context.register(_Dep)
    instance = context.resolve(_Dep)
    assert instance


def test_single_resolve_child_from_parent() -> None:
    context = DIContext()
    context.register(_DepChild)
    instance = context.resolve(_Dep)
    assert instance


def test_method() -> None:
    context = DIContext()
    context.register(dep)
    assert context.resolve(_FuncDep)


def test_list() -> None:
    context = DIContext()
    context.register(_Dep, name='z')
    context.register(_DepChild)
    context.register(_DepOtherChild)
    instances = context.resolve(list[_Dep])
    assert len(instances) == 3


def test_set() -> None:
    context = DIContext()
    context.register(_Dep)
    context.register(_DepChild)
    context.register(_DepOtherChild)
    instances = context.resolve(set[_Dep])
    assert len(instances) == 3


def test_dict() -> None:
    context = DIContext()
    context.register(_Dep)
    context.register(_DepChild)
    context.register(_DepOtherChild)
    instances = context.resolve(dict[str, _Dep])
    assert len(instances) == 3


def test_single_with_many_registered_and_primary() -> None:
    context = DIContext()
    context.register(_DepChild)
    context.register(_DepOtherChild, primary=True)
    instance = context.resolve(_Dep)
    assert isinstance(instance, _DepOtherChild)


def test_complex_dep() -> None:
    context = DIContext()
    context.register(_FuncDep)
    context.register(_Dep)
    context.register(_DepChild)
    context.register(_DepOtherChild)
    context.register(_ComplexDep)
    instance = context.resolve(_ComplexDep)
    assert instance
    assert instance._dep_single
    assert len(instance._dep_list) == 3
    assert isinstance(instance._dep_func, _FuncDep)


def test_static_method_dep() -> None:
    context = DIContext()
    context.register(_Config.static_dep)
    instance = context.resolve(_FuncDep)
    assert instance


def test_class_method_dep() -> None:
    context = DIContext()
    context.register(_Config.class_dep)
    instance = context.resolve(_FuncDep)
    assert instance
