"""Install the supplied Linux MLX wheel in a project virtual environment."""

from collections.abc import Sequence
from io import BytesIO
import os
from pathlib import Path, PurePosixPath
import platform
from shutil import copyfile
import subprocess
import sys
import sysconfig
import tarfile
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

WHEEL = "mlx-2.2-py3-none-any.whl"
KEYSYMS = "libxcb-keysyms.so.1"
ROOT = Path(__file__).resolve().parent.parent


def distribution(requested: str) -> str:
    """Select the compatible wheel based on the Linux distribution."""
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise ValueError("The bundled MLX wheels require x86-64 Linux.")
    if requested == "auto":
        info = platform.freedesktop_os_release()
        names = {info.get("ID"), *info.get("ID_LIKE", "").split()}
        if names & {"fedora", "rhel"}:
            return "fedora"
        if names & {"ubuntu", "debian"}:
            return "ubuntu"
        raise ValueError("Unknown Linux distribution. Set MLX_DISTRO.")
    if requested not in {"ubuntu", "fedora"}:
        raise ValueError("MLX_DISTRO must be auto, ubuntu or fedora.")
    return requested


def wheel_bytes(distro: str, bundle: str) -> bytes:
    """Read either the vendored wheel or the named school archive entry."""
    if not bundle:
        return (ROOT / "vendor" / "mlx" / distro / WHEEL).read_bytes()
    with tarfile.open(bundle, "r:gz") as archive:
        member = archive.getmember(f"{distro}/{WHEEL}")
        if not member.isfile() or member.size > 5_000_000:
            raise ValueError("Invalid wheel in the MLX archive.")
        source = archive.extractfile(member)
        if source is None:
            raise ValueError("Missing wheel in the MLX archive.")
        with source:
            return source.read()


def unpack_wheel(raw: bytes, site: Path) -> Path:
    """Extract the MLX package into this virtualenv's site-packages."""
    with ZipFile(BytesIO(raw)) as wheel:
        for name in wheel.namelist():
            member = PurePosixPath(name)
            if (
                not member.parts
                or member.parts[0] not in {"mlx", "mlx-2.2.dist-info"}
                or ".." in member.parts
                or "\\" in name
            ):
                raise ValueError(f"Unexpected MLX wheel entry: {name!r}")
        if "mlx/libmlx.so" not in wheel.namelist():
            raise ValueError("The wheel does not contain libmlx.so.")
        wheel.extractall(site)
    return site / "mlx" / "libmlx.so"


def missing_libraries(library: Path, directory: Path) -> set[str]:
    """List missing shared libraries using the runtime search path."""
    previous = os.environ.get("LD_LIBRARY_PATH")
    search_path = f"{directory}:{previous}" if previous else str(directory)
    check = subprocess.run(
        ["ldd", str(library)], check=True, capture_output=True, text=True,
        env={**os.environ, "LC_ALL": "C", "LD_LIBRARY_PATH": search_path},
    )
    if "not found" in check.stderr:
        raise RuntimeError(check.stderr.strip())
    return {
        line.partition(" => ")[0].strip()
        for line in check.stdout.splitlines()
        if "=> not found" in line
    }


def fetch_keysyms(distro: str, destination: Path) -> None:
    """Download and extract the distro's XCB key library without sudo."""
    with TemporaryDirectory(prefix="amazing-mlx-") as tmp:
        folder = Path(tmp)
        package_files = folder / "package"
        package_files.mkdir()
        if distro == "ubuntu":
            subprocess.run(
                ["apt-get", "download", "libxcb-keysyms1"],
                cwd=folder, check=True,
            )
            (package,) = folder.glob("libxcb-keysyms1_*.deb")
            subprocess.run(
                ["dpkg-deb", "-x", str(package), str(package_files)],
                check=True,
            )
        else:
            fetch_fedora_keysyms(folder, package_files)
        library = next(package_files.rglob(KEYSYMS), None)
        if library is None:
            raise RuntimeError(f"The package did not contain {KEYSYMS}.")
        source = library.resolve(strict=True)
        if not source.is_relative_to(package_files):
            raise RuntimeError("The library points outside its package.")
        destination.mkdir(exist_ok=True)
        copyfile(source, destination / KEYSYMS)


def fetch_fedora_keysyms(folder: Path, package_files: Path) -> None:
    """Download and unpack Fedora's signed keysyms RPM."""
    subprocess.run(
        ["dnf", "--setopt", f"cachedir={folder / 'cache'}", "download",
         "--destdir", str(folder), "xcb-util-keysyms.x86_64"],
        check=True,
    )
    (package,) = folder.glob("xcb-util-keysyms-*.rpm")
    subprocess.run(["rpmkeys", "--checksig", str(package)], check=True)
    archive = subprocess.check_output(["rpm2cpio", str(package)])
    subprocess.run(
        ["cpio", "-idm", "--no-absolute-filenames", "*libxcb-keysyms.so.1*"],
        cwd=package_files, input=archive, check=True,
    )


def main(args: Sequence[str]) -> int:
    """Install the wheel and report native dependencies clearly."""
    if len(args) != 2 or sys.prefix == sys.base_prefix:
        print("Run make install from the project root.", file=sys.stderr)
        return 1
    try:
        distro = distribution(args[0])
        site = Path(sysconfig.get_path("purelib"))
        native = Path(sys.prefix) / "mlx-native"
        library = unpack_wheel(wheel_bytes(distro, args[1]), site)
        missing = missing_libraries(library, native)
        if missing == {KEYSYMS}:
            fetch_keysyms(distro, native)
            missing = missing_libraries(library, native)
        if missing:
            raise RuntimeError(
                f"Missing Linux libraries: {', '.join(sorted(missing))}. "
                "Use a machine with X11/Vulkan or set DISPLAY=NONE."
            )
        print(f"MLX 2.2 ({distro}) installed in {sys.prefix}.")
    except (OSError, RuntimeError, ValueError, KeyError, tarfile.TarError,
            BadZipFile, subprocess.CalledProcessError) as error:
        print(f"MLX install error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
