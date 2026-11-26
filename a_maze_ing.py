"""Read a configuration, write the generated maze and open its viewer."""

from collections.abc import Sequence
from pathlib import Path
from random import Random, SystemRandom
import sys

from maze_config import read_config
from maze_display import show_maze
from maze_output import write_maze
from mazegen import Maze


def main(argv: Sequence[str]) -> int:
    """Run the application and report configuration or display errors."""
    if len(argv) != 1:
        print("Usage: python3 a_maze_ing.py config.txt", file=sys.stderr)
        return 1
    try:
        config = read_config(Path(argv[0]))
        seed = config.seed
        if seed is None:
            seed = SystemRandom().getrandbits(64)
        seeds = Random(seed)

        def generate(value: int) -> Maze:
            """Generate and save a maze before returning it to the viewer."""
            maze = config.generator(value).generate()
            write_maze(maze, config.output)
            if not maze.blocked:
                print(
                    "Warning: not enough room for the 42 pattern.",
                    file=sys.stderr,
                )
            print(f"Seed: {value} | Output: {config.output.name}", flush=True)
            return maze

        maze = generate(seed)
        if config.display == "MLX":
            show_maze(maze, lambda: generate(seeds.getrandbits(64)))
        return 0
    except (OSError, ValueError, RuntimeError, ImportError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
