"""Write maze walls and the shortest solution in the assignment format."""

from pathlib import Path
import re

from mazegen import Maze


def write_maze(maze: Maze, destination: Path) -> None:
    """Write LF-delimited output, protecting other existing files."""
    if destination.parent.resolve() != Path.cwd().resolve():
        raise ValueError("The output must be in the working directory.")
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
    """Recognize output files, including the team's earlier hex-only maze."""
    if not path.is_file() or path.stat().st_size > 400_004:
        return False
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except UnicodeError:
        return False
    split = lines.index("") if "" in lines else len(lines)
    rows, footer = lines[:split], lines[split + 1:]
    if not rows or not all(
        len(row) == len(rows[0]) and re.fullmatch(r"[0-9A-F]+", row)
        for row in rows
    ):
        return False
    if split == len(lines):
        return True
    return (
        len(footer) == 3
        and re.fullmatch(r"\d+,\d+", footer[0]) is not None
        and re.fullmatch(r"\d+,\d+", footer[1]) is not None
        and re.fullmatch(r"[NESW]+", footer[2]) is not None
    )
