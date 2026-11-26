"""Write maze walls and the shortest solution in the assignment format."""

from pathlib import Path
import re

from mazegen import Maze

MAX_MAZE_FILE_BYTES = 400_004  # Allow room for the grid, path and footer.


def write_maze(maze: Maze, destination: Path) -> None:
    """Write LF-delimited output, protecting other existing files."""
    if destination.is_symlink():
        raise ValueError("The output cannot be a symbolic link.")
    if destination.exists() and not _is_maze_file(destination):
        raise ValueError(f"Refusing to replace {destination.name!r}.")
    with destination.open("w", encoding="ascii", newline="\n") as output:
        for row in maze.walls:
            output.write("".join(format(cell, "X") for cell in row))
            output.write("\n")
        output.write("\n")
        output.write(f"{maze.entry[0]},{maze.entry[1]}\n")
        output.write(f"{maze.exit[0]},{maze.exit[1]}\n")
        output.write(maze.solution + "\n")


def _is_maze_file(path: Path) -> bool:
    """Check whether an existing file has the maze output format."""
    if not path.is_file() or path.stat().st_size > MAX_MAZE_FILE_BYTES:
        return False
    try:
        grid, separator, metadata = path.read_text(
            encoding="ascii",
        ).partition("\n\n")
    except UnicodeError:
        return False
    rows = grid.splitlines()
    footer = metadata.splitlines()
    if not separator or not rows or not all(
        len(row) == len(rows[0]) and re.fullmatch(r"[0-9A-F]+", row)
        for row in rows
    ):
        return False
    return (
        len(footer) == 3
        and re.fullmatch(r"\d+,\d+", footer[0]) is not None
        and re.fullmatch(r"\d+,\d+", footer[1]) is not None
        and re.fullmatch(r"[NESW]+", footer[2]) is not None
    )
