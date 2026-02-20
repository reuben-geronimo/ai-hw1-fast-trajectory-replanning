from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Generic, Iterator, Tuple, TypeVar

T = TypeVar("T")


@dataclass(order=True)
class _PrioritizedItem(Generic[T]):
    f: float
    tie: float
    counter: int
    item: T = field(compare=False)


class _BaseCustomPQ(Generic[T]):
    def __init__(self) -> None:
        self._heap: list[_PrioritizedItem[T]] = []
        self._counter = 0

    def __len__(self) -> int:
        return len(self._heap)

    def empty(self) -> bool:
        return not self._heap

    def pop(self) -> Tuple[float, float, T]:
        it = heapq.heappop(self._heap)
        return it.f, it.tie, it.item

    def __iter__(self) -> Iterator[T]:
        return (x.item for x in self._heap)


class CustomPQ_minG(_BaseCustomPQ[T]):
    """Tie-break by smaller g when f ties."""

    def push(self, *, f: float, g: float, item: T) -> None:
        self._counter += 1
        heapq.heappush(self._heap, _PrioritizedItem(f=f, tie=g, counter=self._counter, item=item))


class CustomPQ_maxG(_BaseCustomPQ[T]):
    """Tie-break by larger g when f ties."""

    def push(self, *, f: float, g: float, item: T) -> None:
        self._counter += 1
        heapq.heappush(self._heap, _PrioritizedItem(f=f, tie=-g, counter=self._counter, item=item))

