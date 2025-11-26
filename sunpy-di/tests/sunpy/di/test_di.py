from sunpy.di.context import DIContext


class _Dep:
    pass


class _DepChild(_Dep):
    pass


class _DepOtherChild(_Dep):
    pass


class _ComplexDep:
    def __init__(self, dep_single: _DepOtherChild, dep_list: list[_Dep]):
        self._dep_single = dep_single
        self._dep_list = dep_list


def test_single() -> None:
    context = DIContext()
    context.register(_Dep)
    instance = context.resolve_single(_Dep)
    assert instance


def test_single_resolve_child_from_parent() -> None:
    context = DIContext()
    context.register(_DepChild)
    instance = context.resolve_single(_Dep)
    assert instance


def test_many() -> None:
    context = DIContext()
    context.register(_Dep)
    context.register(_DepChild)
    context.register(_DepOtherChild)
    instances = context.resolve_many(_Dep)
    assert len(instances) == 3


def test_single_with_many_registered_and_primary() -> None:
    context = DIContext()
    context.register(_DepChild)
    context.register(_DepOtherChild, primary=True)
    instance = context.resolve_single(_Dep)
    assert isinstance(instance, _DepOtherChild)


def test_complex_dep() -> None:
    context = DIContext()
    context.register(_Dep)
    context.register(_DepChild)
    context.register(_DepOtherChild)
    context.register(_ComplexDep)
    instance = context.resolve_single(_ComplexDep)
    assert instance
    assert instance._dep_single
    assert len(instance._dep_list) == 3
