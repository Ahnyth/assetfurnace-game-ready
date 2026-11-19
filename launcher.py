"""Run this add-on's `game_ready.py` or `prop_ready.py` with the AssetFurnace install it lives in.

`addon_run.py` starts this file with the install's own Python. It puts the add-on's scripts first on the path (they
are newer than any copy in the install), then the install's root (its `image_to_3dlab` package, ahead of any other
copy in site-packages) and the install's `scripts/` (the helpers both tools share with the core: the rig check, the
skeleton mapping, Finish's LOD and texture code). The two checks the core does not ship yet, the colour comparison and
the outline check (`extra/`), join the installed `image_to_3dlab` package; a copy the core ships itself comes first.

    python launcher.py INSTALL_ROOT figure|prop ARGS...
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def set_paths(root: Path) -> None:
    sys.path.insert(0, str(HERE / "scripts"))
    sys.path.insert(1, str(root))
    sys.path.insert(2, str(root / "scripts"))


def lend_checks() -> None:
    import image_to_3dlab

    extra = str(HERE / "extra")
    if extra not in image_to_3dlab.__path__:
        image_to_3dlab.__path__.append(extra)


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[2] not in ("figure", "prop"):
        print("usage: launcher.py INSTALL_ROOT figure|prop ARGS...")
        return 2
    root, tool, rest = Path(argv[1]), argv[2], argv[3:]
    set_paths(root)
    lend_checks()
    if tool == "figure":
        import game_ready

        return game_ready.main(rest)
    import prop_ready

    return prop_ready.main(rest)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
