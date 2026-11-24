"""AssetFurnace add-on entry: make a rigged figure or a finished prop game-ready and leave `{out}/{stem}.glb`.

Runs inside Blender (the add-on's `run` starts `{blender}` with this file), so the studio only has to know Blender.
The work is done by `scripts/game_ready.py` and `scripts/prop_ready.py`. They need numpy, Pillow, SciPy and
AssetFurnace's own package, which Blender's Python does not have, so this file starts them with the Python of the
AssetFurnace install the add-on lives in (`<install>/.venv`; `I2L_PYTHON` names another one), through `launcher.py`,
and hands them this Blender. The stem is the name of the run folder AssetFurnace made, the name it looks for.

    blender -b --factory-startup -P addon_run.py -- OUT_DIR figure MODEL HEIGHT TRIANGLES ATLAS BONES FINGERS GLOW
    blender -b --factory-startup -P addon_run.py -- OUT_DIR prop MODEL FRONT AXIS SIZE LODS COLLIDER

A prop's result is its LOD0; the other LODs, the collider and `<stem>.prop.json` stay beside it. A figure's report
(`<stem>.report.json`) and its check pictures (`<stem>.colour.png`, `<stem>.pose.png`) stay beside it too.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent

TRIANGLES = ("14000", "8000", "20000", "30000", "50000", "as rigged")  # 50000 with 4096: a PC figure (D225)
ATLAS = ("1024", "2048", "512", "4096")
BONES = ("unity", "mixamo", "keep")
FINGERS = ("keep", "merge")
GLOW_WHERE = ("body lines", "eyes only")  # eyes only: the head alone glows (a red eye slit over red trims)
LOOK = ("clean", "stylized")  # clean (the default since 0.1.7): a fifth of the default sheen (game_ready.py --look)
FRONT = ("+z", "-z", "+x", "-x")
AXIS = ("height", "length", "width")
LODS = ("2500,1000", "1200,500", "5000,2500,1000")
COLLIDER = ("box", "hull", "none")
NO_GLOW = {"", "none", "-", "no", "off"}
HEX = re.compile(r"#?([0-9a-fA-F]{6})")


@dataclass
class Job:
    tool: str
    argv: list[str]  # for game_ready.py or prop_ready.py
    result: Path  # what AssetFurnace looks for
    lod0: Path | None = None  # a prop's LOD0, copied to `result`


def _pick(name: str, value: str, choices: Sequence[str]) -> str:
    value = value.strip()
    if value not in choices:
        raise SystemExit(f"{name}: {value!r} is not one of {', '.join(choices)}")
    return value


def _number(name: str, value: str) -> str:
    try:
        number = float(value)
    except ValueError:
        raise SystemExit(f"{name}: {value!r} is not a number") from None
    if number <= 0:
        raise SystemExit(f"{name}: must be above 0, got {value}")
    return value.strip()


def glow_colours(text: str) -> list[str]:
    """'none' or '#29e6ff, ff6a00' -> ['#29e6ff', '#ff6a00']."""
    if text.strip().lower() in NO_GLOW:
        return []
    colours = []
    for part in text.replace(";", ",").split(","):
        match = HEX.fullmatch(part.strip())
        if not match:
            raise SystemExit(f"glow: {part.strip()!r} is not a colour like #29e6ff (or write none)")
        colours.append("#" + match.group(1).lower())
    return colours


def plan(argv: Sequence[str]) -> Job:
    """The job from the arguments after Blender's `--`."""
    args = list(argv[list(argv).index("--") + 1:] if "--" in argv else argv)
    if len(args) < 2 or args[1] not in ("figure", "prop"):
        raise SystemExit("usage: addon_run.py -- OUT_DIR figure|prop MODEL ...; unknown tool")
    out_dir, tool = Path(args[0]), args[1]
    stem = out_dir.name
    result = out_dir / f"{stem}.glb"
    if tool == "figure":
        if len(args) not in (9, 10, 11):
            raise SystemExit("usage: addon_run.py -- OUT_DIR figure MODEL HEIGHT TRIANGLES ATLAS BONES FINGERS GLOW "
                             "[LOOK [GLOW_WHERE]]")
        model, height, triangles, atlas, bones, fingers, glow = args[2:9]
        look = _pick("look", args[9], LOOK) if len(args) >= 10 else LOOK[0]
        where = _pick("glow where", args[10], GLOW_WHERE) if len(args) == 11 else GLOW_WHERE[0]
        cmd = [str(Path(model)), str(result), "--height", _number("height", height),
               "--atlas", _pick("atlas", atlas, ATLAS), "--style", _pick("bones", bones, BONES),
               "--fingers", _pick("fingers", fingers, FINGERS)]
        if _pick("triangles", triangles, TRIANGLES) != "as rigged":
            cmd += ["--decimate-to", triangles.strip(), "--drop-hidden"]
        colours = glow_colours(glow)
        for colour in colours:
            cmd += ["--glow", colour]
        if colours and where == "eyes only":  # the eyes' colour is on the body too: the head alone glows
            cmd += ["--glow-only-on-head"]
        elif colours:  # a glowing face or glowing hands read as a fault on a figure
            cmd += ["--glow-not-on-head", "--glow-not-on-hands"]
        cmd += ["--look", look]  # always named: game_ready.py itself still defaults to stylized
        return Job("figure", cmd, result)
    if len(args) != 8:
        raise SystemExit("usage: addon_run.py -- OUT_DIR prop MODEL FRONT AXIS SIZE LODS COLLIDER")
    model, front, axis, size, lods, collider = args[2:]
    cmd = [str(Path(model)), str(out_dir), "--name", stem, f"--front={_pick('front', front, FRONT)}",
           f"--{_pick('axis', axis, AXIS)}", _number("size", size), "--lods", _pick("lods", lods, LODS),
           "--collider", _pick("collider", collider, COLLIDER)]
    return Job("prop", cmd, result, lod0=out_dir / f"{stem}_LOD0.glb")


def find_python(addon_dir: Path, env: Mapping[str, str]) -> tuple[Path | None, Path | None]:
    """(AssetFurnace's Python, the install's root): `I2L_PYTHON`, else the install's `.venv`, else an active venv."""
    root = addon_dir.parent.parent if addon_dir.parent.name == "addons" else None
    candidates = []
    if env.get("I2L_PYTHON"):
        candidates.append(Path(env["I2L_PYTHON"]))
    if root is not None:
        candidates += [root / ".venv" / "Scripts" / "python.exe", root / ".venv" / "bin" / "python"]
    if env.get("VIRTUAL_ENV"):
        venv = Path(env["VIRTUAL_ENV"])
        candidates += [venv / "Scripts" / "python.exe", venv / "bin" / "python"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate, root
    return None, root


def main(argv: Sequence[str]) -> int:
    import bpy  # only inside Blender: the path of the Blender that runs this file

    job = plan(argv)
    python, root = find_python(HERE, os.environ)
    if python is None or root is None:
        print("game-ready: AssetFurnace's own Python was not found next to this add-on (<install>/.venv); "
              "set I2L_PYTHON to it", flush=True)
        return 1
    blender = bpy.app.binary_path
    job.result.parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "I2L_BLENDER": blender}
    cmd = [str(python), str(HERE / "launcher.py"), str(root), job.tool, *job.argv, "--blender", blender]
    code = subprocess.run(cmd, cwd=str(HERE), env=env, check=False).returncode
    if code != 0:
        return code
    if job.lod0 is not None:
        if not job.lod0.is_file():
            print(f"game-ready: {job.lod0.name} was not written", flush=True)
            return 1
        shutil.copyfile(job.lod0, job.result)
    if not job.result.is_file():
        print(f"game-ready: {job.result.name} was not written", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
