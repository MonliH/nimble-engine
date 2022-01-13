from typing import Callable, List, TypeVar


T = TypeVar("T")


def custom_index(l: List[T], f: Callable[[T], bool]) -> int:
    return next((i for i, e in enumerate(l) if f(e)), -1)
