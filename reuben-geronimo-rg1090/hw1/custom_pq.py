from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Iterator, Tuple, TypeVar

T = TypeVar("T")


@dataclass
class _PrioritizedItem(Generic[T]):
    f: float
    tie: float
    counter: int
    g: float
    item: T


class _BaseCustomPQ(Generic[T]):
    def __init__(self) -> None:
        self._heap: list[_PrioritizedItem[T]] = []
        self._counter = 0

    def __len__(self) -> int:
        return len(self._heap)

    def empty(self) -> bool:
        return not self._heap

    def _less(self, i: int, j: int) -> bool:
        a = self._heap[i]
        b = self._heap[j]
        return (a.f, a.tie, a.counter) < (b.f, b.tie, b.counter)

    def _swap(self, i: int, j: int) -> None:
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]

    def _sift_up(self, idx: int) -> None:
        while idx > 0:
            parent = (idx - 1) // 2
            if self._less(idx, parent):
                self._swap(idx, parent)
                idx = parent
            else:
                break

    def _sift_down(self, idx: int) -> None:
        n = len(self._heap)
        while True:
            left = 2 * idx + 1
            right = 2 * idx + 2
            smallest = idx

            if left < n and self._less(left, smallest):
                smallest = left
            if right < n and self._less(right, smallest):
                smallest = right

            if smallest != idx:
                self._swap(idx, smallest)
                idx = smallest
            else:
                break

    def pop(self) -> Tuple[float, float, T]:
        if not self._heap:
            raise IndexError("pop from empty priority queue")

        last = len(self._heap) - 1
        self._swap(0, last)
        it = self._heap.pop()
        if self._heap:
            self._sift_down(0)
        return it.f, it.g, it.item

    def __iter__(self) -> Iterator[T]:
        return (x.item for x in self._heap)


class CustomPQ_minG(_BaseCustomPQ[T]):
    """Tie-break by smaller g when f ties."""

    def push(self, *, f: float, g: float, item: T) -> None:
        self._counter += 1
        self._heap.append(_PrioritizedItem(f=float(f), tie=float(g), counter=self._counter, g=float(g), item=item))
        self._sift_up(len(self._heap) - 1)


class CustomPQ_maxG(_BaseCustomPQ[T]):
    """Tie-break by larger g when f ties."""

    def push(self, *, f: float, g: float, item: T) -> None:
        self._counter += 1
        self._heap.append(_PrioritizedItem(f=float(f), tie=-float(g), counter=self._counter, g=float(g), item=item))
        self._sift_up(len(self._heap) - 1)

