*This project has been created as part of the 42 curriculum by seguler, asobolev.*

# A-Maze-ing

## Description

A seedable maze generator and an interactive MiniLibX (MLX) viewer.
Generate a perfect maze with a single route between any two cells, or
a playable braided board with loops and few dead ends. The maze is
also saved as hexadecimal wall masks with the shortest solution.

## Instructions

Use Python 3.10 or later and GNU Make. To open the MLX window, use
an x86-64 Ubuntu or Fedora desktop with X11 and Vulkan. Ubuntu with
WSLg also works. From a fresh checkout, run:

```sh
make install
make run
```

The MIT-licensed MLX 2.2 wheels are in `vendor/mlx`. The installer
automatically selects the distribution and uses the project-local
`.venv`. If the XCB keysyms library is missing, it downloads and extracts
the distribution package into that environment. Installation uses no
`sudo`. The download needs repository access, and the desktop must
already provide the remaining graphics libraries and a Vulkan driver.
Fedora downloads need DNF's download command, rpmkeys, rpm2cpio and cpio.
You can override the wheel selection with `MLX_DISTRO=ubuntu` or
`MLX_DISTRO=fedora`, or use `MLX_BUNDLE="/path/to/mlx-2.2.tgz"`.

The application takes one argument. Activate the environment with
`. .venv/bin/activate` to run `python3 a_maze_ing.py config.txt` directly.
Use `make run CONFIG=other.txt` to try another file. On a machine without a
graphical desktop, set `DISPLAY=NONE` in the config and run
`python3 a_maze_ing.py config.txt` with system Python.

`make install-dev` downloads the development tools into the same
environment; `make lint`, `make lint-strict` and `make package` also
install them on demand. `make debug` starts PDB and `make clean` removes
caches and build directories.

| Key | Meaning |
| --- | --- |
| `R` | Regenerate and save a new maze |
| `P` | Toggle the shortest route |
| `C` | Cycle wall colors |
| Arrow keys | Pan when the maze is larger than the window |
| `Esc` or `Q` | Close the window |

## Configuration

Write one `KEY=VALUE` per line in UTF-8. Empty lines and lines starting
with `#` are ignored. Keys are case-sensitive.

| Key | Accepted value |
| --- | --- |
| `WIDTH`, `HEIGHT` | Positive integer dimensions, between 2 and 100,000 total cells |
| `ENTRY`, `EXIT` | Distinct `x,y` coordinates inside the maze, starting at zero |
| `OUTPUT_FILE` | A file name in the working directory, e.g. `maze.txt` |
| `PERFECT` | `True` for one unique route, `False` for a braided board |
| `SEED` | Optional non-negative integer, chosen randomly when omitted |
| `DISPLAY` | Optional `MLX` (default) or `NONE` for output without a window |

The included config uses `PERFECT=False`. When a board is too small for
two loops, use `PERFECT=True` or increase its dimensions. The program
warns if the 42 pattern cannot fit around the selected endpoints. The
output contains one hex digit for each cell, then a blank line, entry
and exit coordinates, and the shortest route as `N/E/S/W` letters.

## Algorithms

We start with closed walls and use randomized depth-first search to
join each newly visited cell to the tree. Iterative DFS uses a stack,
avoids Python's recursion limit, and reproduces the maze with a seed.
The cells that draw 42 remain fully closed and are skipped by DFS.

In braided mode we remove some additional walls, starting at dead
ends. Each opening creates a loop, and any opening that would clear
all interior walls of a 3×3 square is reversed. A breadth-first
search then finds the shortest path in either mode, because each
step between adjacent cells has the same cost.

## Reuse

Install the root-level wheel with
`python3 -m pip install mazegen-1.0.0-py3-none-any.whl`. To rebuild it,
install `build` in a virtual environment and run
`python3 -m build --wheel --outdir .`, or use `make package` after setup.
The wheel includes the MIT license. The generator needs no MLX,
configuration file, or application code.

```python
from mazegen import MazeGenerator

maze = MazeGenerator(
    20, 15, entry=(0, 0), exit=(19, 14), perfect=False, seed=42
).generate()

print(maze.walls[0][0])  # bitmask at x=0, y=0
print(maze.solution)     # shortest route as direction letters
print(maze.path())       # shortest route as coordinates
```

The optional endpoints default to opposite corners. Pass `perfect=True`
for a tree or set a different `seed` for another maze. The bit order is
N, E, S, W (1, 2, 4, 8), and a set bit means a closed wall. Access the
pattern coordinates through `maze.blocked`.

## Team and process

- Semih started with the wall bitmasks, shared wall removal and hex
  output. Alex developed configuration parsing, validation and the
  initial Makefile and license.
- The plan moved from a fixed grid to a seedable generator with separate
  file and window interfaces. Keeping the grid representation separate
  made it possible to test both maze modes before opening a window.
- VS Code, Git, GitHub, flake8, mypy and the provided analyzer were used.
  Sharing smaller changes earlier would reduce overlap during integration.

## Resources

- [Python random module](https://docs.python.org/3/library/random.html)
- [Python deque](https://docs.python.org/3/library/collections.html#collections.deque)
- The assignment's MiniLibX 2.2 manuals and Python example shipped with
  `mlx-2.2.tgz`.
- The official `maze_analyzer.py` checks wall consistency and reports
  whether a maze is perfect or playable.
