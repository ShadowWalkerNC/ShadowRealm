"""
C95 — Data Transformer
Provides map, filter, and reduce operations for standard data structures.
"""
from __future__ import annotations
from typing import Callable, Iterable, List, TypeVar

T = TypeVar('T')
U = TypeVar('U')

class DataTransformer:
    @staticmethod
    def map(fn: Callable[[T], U], items: Iterable[T]) -> List[U]:
        return [fn(item) for item in items]

    @staticmethod
    def filter(fn: Callable[[T], bool], items: Iterable[T]) -> List[T]:
        return [item for item in items if fn(item)]
