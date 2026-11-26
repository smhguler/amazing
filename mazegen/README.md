# mazegen

A pure Python 3.10+ maze generator. It has no runtime dependencies.

```python
from mazegen import MazeGenerator

maze = MazeGenerator(
    20, 15, entry=(0, 0), exit=(19, 14), perfect=False, seed=42
).generate()

print(maze.walls[0][0])  # int wall mask, indexed as walls[y][x]
print(maze.solution)     # shortest route as N/E/S/W letters
print(maze.path())       # the same route as an (x, y) coordinate sequence
```

The width and height are required. The entry defaults to the top left,
and the exit defaults to the bottom right. A fixed seed reproducibly
generates the same maze for the same settings. `perfect=True` produces a
tree; `perfect=False` creates a braided board. Invalid or impossible
parameters raise `ValueError`.

`Maze.blocked` contains the fully closed cells drawn as the 42 pattern.
An empty set means the pattern could not fit with the requested size and
endpoints. Each wall mask uses bits 1, 2, 4, 8 for N, E, S, W respectively;
a set bit means that wall is closed. `Maze.entry` and `Maze.exit` are
`(x, y)` pairs.
