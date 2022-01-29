from typing import Callable, List, TypeVar


T = TypeVar("T")


def custom_index(lst: List[T], predicate: Callable[[T], bool]) -> int:
    """Like `list.index`, but uses custom function to determine equality."""
    return next((i for i, e in enumerate(lst) if predicate(e)), -1)
