"""Check the Ubuntu MLX wheel's native libraries after pip installs it."""

import os
from pathlib import Path
from shutil import copyfile
import subprocess
import sys
import sysconfig
from tempfile import TemporaryDirectory

KEYSYMS = "libxcb-keysyms.so.1"


def missing_libraries(library: Path, native: Path) -> set[str]:
    """Read the list of unresolved shared libraries from ldd."""
    search_path = [str(native)]
    if previous := os.environ.get("LD_LIBRARY_PATH"):
        search_path.append(previous)
    check = subprocess.run(
        ["ldd", str(library)], check=True, capture_output=True, text=True,
        env={**os.environ, "LC_ALL": "C",
             "LD_LIBRARY_PATH": ":".join(search_path)},
    )
    return {
        line.partition(" => ")[0].strip()
        for line in check.stdout.splitlines()
        if "=> not found" in line
    }


def install_keysyms(native: Path) -> None:
    """Download the Ubuntu package and copy its library into the venv."""
    with TemporaryDirectory(prefix="amazing-mlx-") as directory:
        folder = Path(directory)
        extracted = folder / "package"
        subprocess.run(
            ["apt-get", "download", "libxcb-keysyms1"], cwd=folder, check=True,
        )
        packages = list(folder.glob("libxcb-keysyms1_*.deb"))
        if len(packages) != 1:
            raise RuntimeError("Expected one libxcb-keysyms1 package.")
        subprocess.run(
            ["dpkg-deb", "-x", str(packages[0]), str(extracted)], check=True,
        )
        library = next(extracted.rglob(KEYSYMS), None)
        if library is None:
            raise RuntimeError(f"The package did not contain {KEYSYMS}.")
        source = library.resolve(strict=True)
        if not source.is_relative_to(extracted):
            raise RuntimeError("The library points outside its package.")
        native.mkdir(exist_ok=True)
        copyfile(source, native / KEYSYMS)


def main() -> int:
    """Check the installed wheel and report unresolved prerequisites."""
    try:
        library = Path(sysconfig.get_path("purelib")) / "mlx" / "libmlx.so"
        native = Path(sys.prefix) / "mlx-native"
        missing = missing_libraries(library, native)
        if missing == {KEYSYMS}:
            install_keysyms(native)
            missing = missing_libraries(library, native)
        if missing:
            names = ", ".join(sorted(missing))
            raise RuntimeError(f"Missing Linux libraries: {names}.")
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"MLX setup error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
