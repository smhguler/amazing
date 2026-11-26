"""Parse and validate the configuration for the command-line program."""

from dataclasses import dataclass
from pathlib import Path
import re

from mazegen import MazeGenerator, Point

REQUIRED = {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"}
OPTIONAL = {"DISPLAY", "SEED"}
MAX_CONFIG_CHARS = 32 * 1024  # Bound the amount of input read at startup.
MAX_INTEGER_DIGITS = 20  # Enough for any unsigned 64-bit seed.
MAX_OUTPUT_NAME_LENGTH = 128  # Limit the generated file name.


@dataclass(frozen=True)
class Config:
    """Hold typed, validated settings and construct a maze generator."""

    width: int
    height: int
    entry: Point
    exit: Point
    output: Path
    perfect: bool
    seed: int | None
    display: str

    def generator(self, seed: int) -> MazeGenerator:
        """Create the generator for this configuration and seed."""
        return MazeGenerator(
            self.width, self.height, self.entry, self.exit,
            perfect=self.perfect, seed=seed,
        )


def read_config(path: Path) -> Config:
    """Read UTF-8 KEY=VALUE lines and reject invalid configurations."""
    with path.open("r", encoding="utf-8-sig") as source:
        content = source.read(MAX_CONFIG_CHARS + 1)
    if len(content) > MAX_CONFIG_CHARS:
        raise ValueError("Configuration file is too large.")
    values: dict[str, str] = {}
    for number, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not separator:
            raise ValueError(f"Line {number}: expected KEY=VALUE.")
        if key not in REQUIRED | OPTIONAL:
            raise ValueError(f"Line {number}: unknown setting {key!r}.")
        if key in values or not value:
            raise ValueError(f"Line {number}: duplicate or empty {key}.")
        values[key] = value
    missing = REQUIRED - values.keys()
    if missing:
        raise ValueError(f"Missing settings: {', '.join(sorted(missing))}.")

    if values["PERFECT"] not in ("True", "False"):
        raise ValueError("PERFECT must be True or False.")
    display = values.get("DISPLAY", "MLX").upper()
    if display not in ("MLX", "NONE"):
        raise ValueError("DISPLAY must be MLX or NONE.")
    filename = values["OUTPUT_FILE"]
    if len(filename) > MAX_OUTPUT_NAME_LENGTH:
        raise ValueError("OUTPUT_FILE is too long.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", filename):
        raise ValueError("OUTPUT_FILE must be a file name without a path.")
    if filename.endswith("."):
        raise ValueError("OUTPUT_FILE cannot end with a period.")
    output = Path.cwd() / filename
    if output.resolve() == path.resolve():
        raise ValueError("OUTPUT_FILE cannot be the configuration file.")
    seed = _integer("SEED", values["SEED"]) if "SEED" in values else None

    return Config(
        _integer("WIDTH", values["WIDTH"]),
        _integer("HEIGHT", values["HEIGHT"]),
        _point("ENTRY", values["ENTRY"]),
        _point("EXIT", values["EXIT"]),
        output,
        values["PERFECT"] == "True",
        seed,
        display,
    )


def _integer(name: str, value: str) -> int:
    """Read a bounded unsigned decimal integer."""
    if len(value) > MAX_INTEGER_DIGITS or not re.fullmatch(r"[0-9]+", value):
        raise ValueError(f"{name} must be a non-negative integer.")
    return int(value)


def _point(name: str, value: str) -> Point:
    """Read a pair of unsigned coordinates in x,y order."""
    x, separator, y = value.partition(",")
    if not separator:
        raise ValueError(f"{name} must have the form x,y.")
    return _integer(name, x.strip()), _integer(name, y.strip())
