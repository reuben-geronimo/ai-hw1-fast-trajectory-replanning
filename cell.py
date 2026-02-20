class Cell:
    def __init__(self, coord: tuple[int, int]):
        self.coord = coord

        # search metadata
        self.parent: 'Cell' | None = None
        self.search_id: int = -1
        self.g: float = float('inf')

        # heuristic metadata (for adaptive A*)
        self.h: float | None = None

    # property accessors for row and column
    @property
    def r(self) -> int:
        return self.coord[0]

    @property
    def c(self) -> int:
        return self.coord[1]

    def reset_for_search(self, current_search: int) -> None:
        """Lazy init/reset for a new A* search."""
        if self.search_id != current_search:
            self.g = float('inf')
            self.parent = None
            self.search_id = current_search

    def __repr__(self) -> str:
        parent = self.parent.coord if self.parent else None
        return (
            f"Cell(coord={self.coord}, g={self.g}, h={self.h}, "
            f"search_id={self.search_id}, parent={parent})"
        )

