"""Interactive MiniLibX 2.2 renderer for a generated maze."""

from collections.abc import Callable
from ctypes import CDLL
from importlib import import_module
import os
from pathlib import Path
import sys
from typing import Any

from mazegen import Maze

BACKGROUND = 0x111926
FLOOR = 0x202D40
PATTERN = 0x556DA6
ENTRY = 0x4EE4A5
EXIT = 0xFF896E
SOLUTION = 0xF3C86A
PALETTE = (0xDDEBFF, 0x78DCF2, 0xE7A6F5, 0xC6E981)
MARGIN = 22
HEADER = 50
FOOTER = 58


def show_maze(maze: Maze, regenerate: Callable[[], Maze]) -> None:
    """Open the MLX window and wait until the user closes it."""
    if sys.platform != "linux" or not os.environ.get("DISPLAY"):
        raise RuntimeError("MLX requires Linux with an X display (or WSLg).")
    try:
        # make install can provide this dependency inside the virtualenv.
        keysyms = Path(sys.prefix) / "mlx-native" / "libxcb-keysyms.so.1"
        if keysyms.is_file():
            CDLL(str(keysyms))
        mlx = import_module("mlx").Mlx()
    except (ImportError, OSError, AttributeError) as error:
        raise RuntimeError(
            f"MLX 2.2 could not load: {error}. Run make install."
        ) from error
    context = mlx.mlx_init()
    if not context:
        raise RuntimeError("MLX could not initialize its display.")
    try:
        Viewer(mlx, context, maze, regenerate).run()
    finally:
        mlx.mlx_release(context)


class Canvas:
    """Write solid rectangles into the native MLX image buffer."""

    def __init__(
        self, buffer: memoryview, stride: int, fmt: int
    ) -> None:
        """Keep the row stride and byte order provided by MLX."""
        self.buffer = buffer
        self.stride = stride
        self.fmt = fmt

    def rect(
        self, x: int, y: int, width: int, height: int, color: int
    ) -> None:
        """Fill a rectangle with an opaque RGB color."""
        argb = color | 0xFF000000
        pixel = argb.to_bytes(4, "little" if self.fmt == 0 else "big")
        line = pixel * width
        for row in range(y, y + height):
            offset = row * self.stride + x * 4
            self.buffer[offset:offset + len(line)] = line


class Viewer:
    """Display a maze and handle keyboard shortcuts and window events."""

    def __init__(
        self,
        mlx: Any,
        context: int,
        maze: Maze,
        regenerate: Callable[[], Maze],
    ) -> None:
        """Set up the viewport and initialize display settings."""
        self.mlx = mlx
        self.context = context
        self.maze = maze
        self.regenerate = regenerate
        self.columns = len(maze.walls[0])
        self.rows = len(maze.walls)
        _, screen_width, screen_height = mlx.mlx_get_screen_size(context)
        max_width = max(540, min(1060, screen_width - 80))
        max_height = max(260, min(770, screen_height - 100))
        area_width = max_width - 2 * MARGIN - 2
        area_height = max_height - HEADER - FOOTER - 2
        self.tile = max(8, min(
            32, area_width // self.columns, area_height // self.rows,
        ))
        self.visible_x = min(self.columns, area_width // self.tile)
        self.visible_y = min(self.rows, area_height // self.tile)
        self.width = max(540, self.visible_x * self.tile + 2 * MARGIN + 2)
        self.height = self.visible_y * self.tile + HEADER + FOOTER + 2
        self.origin_x = (self.width - self.visible_x * self.tile) // 2 - 1
        self.left = min(
            maze.entry[0], self.columns - self.visible_x,
        )
        self.top = min(maze.entry[1], self.rows - self.visible_y)
        self.show_solution = False
        self.color = 0
        self.window = 0
        self.image = 0
        self.canvas: Canvas

    def run(self) -> None:
        """Manage the window and image for the lifetime of the event loop."""
        self.window = self.mlx.mlx_new_window(
            self.context, self.width, self.height, "A-Maze-ing",
        )
        if not self.window:
            raise RuntimeError("MLX could not open the maze window.")
        try:
            self.image = self.mlx.mlx_new_image(
                self.context, self.width, self.height,
            )
            if not self.image:
                raise RuntimeError("MLX could not allocate a drawing buffer.")
            try:
                data, bpp, stride, fmt = self.mlx.mlx_get_data_addr(self.image)
                if bpp != 32 or fmt not in (0, 1):
                    raise RuntimeError("Unsupported MLX pixel format.")
                self.canvas = Canvas(data, stride, fmt)
                self.mlx.mlx_key_hook(self.window, self._key, None)
                self.mlx.mlx_expose_hook(self.window, self._present, None)
                self.mlx.mlx_hook(self.window, 33, 0, self._close, None)
                self._draw()
                self.mlx.mlx_loop(self.context)
            finally:
                self.mlx.mlx_destroy_image(self.context, self.image)
        finally:
            self.mlx.mlx_destroy_window(self.context, self.window)

    def _close(self, _: object) -> None:
        """Stop the MLX loop so the window can be destroyed safely."""
        self.mlx.mlx_loop_exit(self.context)

    def _key(self, key: int, _: object) -> None:
        """Regenerate, toggle the route, change color, pan or quit."""
        if key in (65307, ord("q"), ord("Q")):
            self._close(None)
            return
        if key in (ord("r"), ord("R")):
            try:
                self.maze = self.regenerate()
            except (ValueError, OSError) as error:
                print(f"Error: {error}", file=sys.stderr)
                return
        elif key in (ord("p"), ord("P")):
            self.show_solution = not self.show_solution
        elif key in (ord("c"), ord("C")):
            self.color = (self.color + 1) % len(PALETTE)
        elif key in (65361, 65362, 65363, 65364):
            self.left = max(0, min(
                self.columns - self.visible_x,
                self.left + (key == 65363) * 4 - (key == 65361) * 4,
            ))
            self.top = max(0, min(
                self.rows - self.visible_y,
                self.top + (key == 65364) * 4 - (key == 65362) * 4,
            ))
        else:
            return
        try:
            self._draw()
        except (OSError, ValueError, RuntimeError) as error:
            print(f"Error: {error}", file=sys.stderr)
            self._close(None)

    def _draw(self) -> None:
        """Paint the visible cells, shortest route, markers and walls."""
        self.mlx.mlx_sync(self.context, 1, self.image)
        self.canvas.rect(0, 0, self.width, self.height, BACKGROUND)
        size = self.tile
        self.canvas.rect(
            self.origin_x, HEADER,
            self.visible_x * size + 2, self.visible_y * size + 2, FLOOR,
        )
        visible = [
            (x, y)
            for y in range(self.top, self.top + self.visible_y)
            for x in range(self.left, self.left + self.visible_x)
        ]
        for x, y in visible:
            if (x, y) in self.maze.blocked:
                px, py = self._pixel(x, y)
                self.canvas.rect(px, py, size, size, PATTERN)
        if self.show_solution:
            self._draw_path(set(visible))
        for x, y in visible:
            px, py = self._pixel(x, y)
            cell = (x, y)
            if cell == self.maze.entry or cell == self.maze.exit:
                inset = max(2, size // 4)
                color = ENTRY if cell == self.maze.entry else EXIT
                self.canvas.rect(
                    px + inset, py + inset, size - 2 * inset,
                    size - 2 * inset, color,
                )
            self._walls(px, py, self.maze.walls[y][x])
        self._present(None)

    def _pixel(self, x: int, y: int) -> tuple[int, int]:
        """Convert a visible coordinate into the image's pixel space."""
        return (
            self.origin_x + (x - self.left) * self.tile,
            HEADER + (y - self.top) * self.tile,
        )

    def _walls(self, px: int, py: int, bits: int) -> None:
        """Draw the four closed walls encoded in a cell."""
        size = self.tile
        color = PALETTE[self.color]
        if bits & 1:
            self.canvas.rect(px, py, size + 2, 2, color)
        if bits & 2:
            self.canvas.rect(px + size, py, 2, size + 2, color)
        if bits & 4:
            self.canvas.rect(px, py + size, size + 2, 2, color)
        if bits & 8:
            self.canvas.rect(px, py, 2, size + 2, color)

    def _draw_path(self, visible: set[tuple[int, int]]) -> None:
        """Connect adjacent visible solution cells with a colored trace."""
        points = self.maze.path()
        middle = self.tile // 2
        line = max(2, self.tile // 6)
        for start, end in zip(points, points[1:]):
            if start not in visible or end not in visible:
                continue
            sx, sy = self._pixel(*start)
            ex, ey = self._pixel(*end)
            self.canvas.rect(
                min(sx, ex) + middle, min(sy, ey) + middle,
                abs(sx - ex) + line, abs(sy - ey) + line, SOLUTION,
            )

    def _present(self, _: object) -> None:
        """Copy the current frame to the window and draw its controls."""
        mlx = self.mlx
        mlx.mlx_put_image_to_window(
            self.context, self.window, self.image, 0, 0,
        )
        text = mlx.mlx_string_put
        text(self.context, self.window, MARGIN, 28, 0xFFDEE9FB,
             f"A-MAZE-ING   /   {self.columns} x {self.rows}")
        controls = "R  New maze    P  Path    C  Color    Esc  Quit"
        text(self.context, self.window, MARGIN, self.height - 30,
             0xFFDEE9FB, controls)
        text(self.context, self.window, MARGIN, self.height - 12,
             0xFF4EE4A5, "Entry")
        text(self.context, self.window, MARGIN + 60, self.height - 12,
             0xFFFF896E, "Exit")
        if self.visible_x < self.columns or self.visible_y < self.rows:
            text(self.context, self.window, MARGIN + 108, self.height - 12,
                 0xFFDEE9FB, "Arrow keys scroll")
