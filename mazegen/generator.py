"""Build mazes with symmetric wall bitmasks and solve them with BFS."""

from collections import deque
from dataclasses import dataclass
from random import Random

Point = tuple[int, int]
DIRECTIONS = (
    ("N", 0, -1, 1, 4),
    ("E", 1, 0, 2, 8),
    ("S", 0, 1, 4, 1),
    ("W", -1, 0, 8, 2),
)
MAX_CELLS = 100_000  # Cap the size of the in-memory grid and searches.
MAX_BRAID_ATTEMPTS = 32  # Limit retries when a tree cannot be braided.
MIN_LOOPS = 2  # A playable board needs at least two independent loops.
MAX_DEAD_ENDS = 2  # The subject tolerates a couple of avoidable dead ends.
ALL_WALLS = 15
PATTERN = (
    "#.#.###",
    "#.#...#",
    "###.###",
    "..#.#..",
    "..#.###",
)


@dataclass(frozen=True)
class Maze:
    """Store the maze, blocked cells, endpoints and shortest solution."""

    walls: tuple[tuple[int, ...], ...]
    blocked: frozenset[Point]
    entry: Point
    exit: Point
    solution: str

    def path(self) -> tuple[Point, ...]:
        """Return the solution coordinates, including both endpoints."""
        moves = {letter: (dx, dy) for letter, dx, dy, _, _ in DIRECTIONS}
        x, y = self.entry
        points = [self.entry]
        for step in self.solution:
            dx, dy = moves[step]
            x, y = x + dx, y + dy
            points.append((x, y))
        return tuple(points)


class MazeGenerator:
    """Generate perfect trees or braided boards from the same settings."""

    def __init__(
        self,
        width: int,
        height: int,
        entry: Point = (0, 0),
        exit: Point | None = None,
        *,
        perfect: bool = False,
        seed: int | None = None,
    ) -> None:
        """Validate the dimensions and endpoints for both build modes."""
        if min(width, height) < 1 or not 2 <= width * height <= MAX_CELLS:
            raise ValueError(f"Maze must contain 2 to {MAX_CELLS} cells.")
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = (width - 1, height - 1) if exit is None else exit
        if not self._inside(self.entry) or not self._inside(self.exit):
            raise ValueError("ENTRY and EXIT must be inside the maze.")
        if self.entry == self.exit:
            raise ValueError("ENTRY and EXIT must differ.")
        if not perfect and (width - 1) * (height - 1) < MIN_LOOPS:
            raise ValueError("This size cannot support two loops.")
        self.perfect = perfect
        self.seed = seed

    def generate(self) -> Maze:
        """Return a new maze; a fixed seed reproduces the same result."""
        rng = Random(self.seed)
        blocked = self._pattern()
        cells = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in blocked
        ]
        attempts = 1 if self.perfect else MAX_BRAID_ATTEMPTS
        for _ in range(attempts):
            walls = [[ALL_WALLS] * self.width for _ in range(self.height)]
            self._carve_tree(walls, blocked, rng)
            if self.perfect or self._braid(walls, cells, blocked, rng):
                return Maze(
                    tuple(tuple(row) for row in walls),
                    blocked,
                    self.entry,
                    self.exit,
                    self._solve(walls),
                )
        raise ValueError(
            "Could not braid this maze. Try another size or seed."
        )

    def _inside(self, cell: Point) -> bool:
        """Check whether a coordinate belongs to the grid."""
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def _pattern(self) -> frozenset[Point]:
        """Place the 42 close to the center, with a corridor around it."""
        pw, ph = len(PATTERN[0]), len(PATTERN)
        # These margins keep the outer corridors connected.
        if self.width < pw + 2 or self.height < ph + 2:
            return frozenset()
        cx, cy = (self.width - pw) // 2, (self.height - ph) // 2
        keep_open = {self.entry, self.exit}
        if not self.perfect:
            keep_open.add((self.width // 2, self.height // 2))
        offsets = [
            (x, y)
            for y, line in enumerate(PATTERN)
            for x, char in enumerate(line)
            if char == "#"
        ]
        positions = sorted(
            ((x, y) for y in range(1, self.height - ph)
             for x in range(1, self.width - pw)),
            key=lambda pos: abs(pos[0] - cx) + abs(pos[1] - cy),
        )
        for x, y in positions:
            blocked = frozenset(
                (x + dx, y + dy) for dx, dy in offsets
            )
            if blocked.isdisjoint(keep_open):
                return blocked
        return frozenset()

    def _carve_tree(
        self, walls: list[list[int]], blocked: frozenset[Point], rng: Random
    ) -> None:
        """Open a passage only when DFS reaches an unvisited cell."""
        visited = {self.entry}
        stack = [self.entry]
        while stack:
            x, y = stack[-1]
            options: list[tuple[Point, int, int]] = []
            for _, dx, dy, wall, opposite in DIRECTIONS:
                other = (x + dx, y + dy)
                if (self._inside(other) and other not in visited
                        and other not in blocked):
                    options.append((other, wall, opposite))
            if not options:
                stack.pop()
                continue
            other, wall, opposite = rng.choice(options)
            nx, ny = other
            walls[y][x] &= ~wall
            walls[ny][nx] &= ~opposite
            visited.add(other)
            stack.append(other)

    def _braid(
        self,
        walls: list[list[int]],
        cells: list[Point],
        blocked: frozenset[Point],
        rng: Random,
    ) -> bool:
        """Remove dead ends first, then ensure at least two loops."""
        rng.shuffle(cells)
        loops = 0
        for x, y in cells:
            if walls[y][x].bit_count() != 3:
                continue
            options = list(DIRECTIONS)
            rng.shuffle(options)
            options.sort(
                key=lambda move: self._is_dead_end(
                    walls, (x + move[1], y + move[2]),
                ),
                reverse=True,
            )
            for _, dx, dy, wall, opposite in options:
                if self._try_open(walls, blocked, (x, y), dx, dy,
                                  wall, opposite):
                    loops += 1
                    break
        if self._avoidable_dead_ends(walls, cells, blocked) > MAX_DEAD_ENDS:
            return False
        for x, y in cells:
            if loops >= MIN_LOOPS:
                return True
            for _, dx, dy, wall, opposite in DIRECTIONS[1:3]:
                if self._try_open(walls, blocked, (x, y), dx, dy,
                                  wall, opposite):
                    loops += 1
                    if loops >= MIN_LOOPS:
                        return True
        return False

    def _is_dead_end(self, walls: list[list[int]], cell: Point) -> bool:
        """Check whether an in-bounds cell has exactly one open side."""
        x, y = cell
        return self._inside(cell) and walls[y][x].bit_count() == 3

    def _avoidable_dead_ends(
        self,
        walls: list[list[int]],
        cells: list[Point],
        blocked: frozenset[Point],
    ) -> int:
        """Count dead ends that are not forced by the 42 or the border."""
        return sum(
            walls[y][x].bit_count() == 3
            and sum(
                self._inside((x + dx, y + dy))
                and (x + dx, y + dy) not in blocked
                for _, dx, dy, _, _ in DIRECTIONS
            ) > 1
            for x, y in cells
        )

    def _try_open(
        self,
        walls: list[list[int]],
        blocked: frozenset[Point],
        cell: Point,
        dx: int,
        dy: int,
        wall: int,
        opposite: int,
    ) -> bool:
        """Open both sides of a passage unless it clears a 3x3 square."""
        x, y = cell
        nx, ny = x + dx, y + dy
        if (not self._inside((nx, ny)) or (nx, ny) in blocked
                or not walls[y][x] & wall):
            return False
        walls[y][x] &= ~wall
        walls[ny][nx] &= ~opposite
        for top in self._square_starts(y, ny, self.height):
            for left in self._square_starts(x, nx, self.width):
                if self._square_is_open(walls, left, top):
                    walls[y][x] |= wall
                    walls[ny][nx] |= opposite
                    return False
        return True

    @staticmethod
    def _square_starts(first: int, second: int, size: int) -> range:
        """List 3-cell window starts that contain both coordinates."""
        start = max(0, max(first, second) - 2)
        stop = min(first, second, size - 3) + 1
        return range(start, stop)

    @staticmethod
    def _square_is_open(walls: list[list[int]], x: int, y: int) -> bool:
        """Test the twelve interior edges of a square of nine cells."""
        return all(
            (i == x + 2 or not walls[j][i] & 2)
            and (j == y + 2 or not walls[j][i] & 4)
            for j in range(y, y + 3)
            for i in range(x, x + 3)
        )

    def _solve(self, walls: list[list[int]]) -> str:
        """Follow open passages in BFS order and reconstruct the route."""
        queue = deque([self.entry])
        steps: dict[Point, tuple[Point, str]] = {}
        seen = {self.entry}
        while queue:
            cell = queue.popleft()
            if cell == self.exit:
                break
            x, y = cell
            for letter, dx, dy, wall, _ in DIRECTIONS:
                other = (x + dx, y + dy)
                if not walls[y][x] & wall and other not in seen:
                    steps[other] = cell, letter
                    seen.add(other)
                    queue.append(other)
        result: list[str] = []
        cell = self.exit
        while cell != self.entry:
            cell, letter = steps[cell]
            result.append(letter)
        return "".join(reversed(result))
