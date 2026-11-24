"""The add-on's entry: what it hands the scripts, and where it finds AssetFurnace's own Python."""

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import addon_run


def figure_args(**over):
    args = {"out": "/o/run-1", "model": "/m/hero_rigged.glb", "height": "1.8", "triangles": "14000",
            "atlas": "1024", "bones": "unity", "fingers": "keep", "glow": "none"}
    args.update(over)
    run = ["blender", "-b", "--python", "addon_run.py", "--", args["out"], "figure", args["model"], args["height"],
           args["triangles"], args["atlas"], args["bones"], args["fingers"], args["glow"]]
    return run + [args["look"]] if "look" in args else run


def test_figure_writes_the_glb_the_studio_looks_for():
    job = addon_run.plan(figure_args())
    assert job.tool == "figure"
    assert job.result == Path("/o/run-1/run-1.glb")
    assert job.argv[:2] == [str(Path("/m/hero_rigged.glb")), str(Path("/o/run-1/run-1.glb"))]


def test_figure_options():
    argv = addon_run.plan(figure_args()).argv
    assert argv[argv.index("--height") + 1] == "1.8"
    assert argv[argv.index("--atlas") + 1] == "1024"
    assert argv[argv.index("--style") + 1] == "unity"
    assert argv[argv.index("--fingers") + 1] == "keep"
    assert argv[argv.index("--decimate-to") + 1] == "14000"
    assert "--drop-hidden" in argv  # a thinned figure drops the hidden inner wall too
    assert "--glow" not in argv


def test_figure_pc_choices():
    # a PC figure (AssetFurnace Support D225): about 50k triangles and a 4096 map; above that the shape stops gaining
    argv = addon_run.plan(figure_args(triangles="50000", atlas="4096")).argv
    assert argv[argv.index("--decimate-to") + 1] == "50000"
    assert argv[argv.index("--atlas") + 1] == "4096"


def test_the_manifest_offers_what_the_runner_takes():
    import json
    tools = json.loads((HERE / "addon.json").read_text(encoding="utf-8"))["tools"]
    inputs = {i["id"]: i for t in tools for i in t.get("inputs", []) if i.get("type") == "choice"}
    assert tuple(inputs["triangles"]["choices"]) == addon_run.TRIANGLES
    assert tuple(inputs["atlas"]["choices"]) == addon_run.ATLAS


def test_figure_look():
    # clean (AssetFurnace Support D232/D233): a fifth of the default sheen, no grey veil over dark cloth
    # clean is the default since 0.1.7 (AssetFurnace Support #212 (a), D246): blacks stay black for whoever picks nothing
    def look_of(argv):
        return argv[argv.index("--look") + 1]

    assert look_of(addon_run.plan(figure_args(look="clean")).argv) == "clean"
    assert look_of(addon_run.plan(figure_args(look="stylized")).argv) == "stylized"
    assert look_of(addon_run.plan(figure_args()).argv) == "clean"  # a studio passing the eight inputs of 0.1.5
    with pytest.raises(SystemExit):
        addon_run.plan(figure_args(look="shiny"))


def test_the_manifest_offers_the_looks_the_runner_takes():
    import json
    tool = json.loads((HERE / "addon.json").read_text(encoding="utf-8"))["tools"][0]
    inputs = {i["id"]: i for i in tool["inputs"]}
    assert tuple(inputs["look"]["choices"]) == addon_run.LOOK
    assert inputs["look"]["choices"][0] == "clean"  # the studio shows the first choice as the default
    assert tool["run"][-2:] == ["{look}", "{glow_where}"]
    assert tuple(inputs["glow_where"]["choices"]) == addon_run.GLOW_WHERE  # the first, body lines, is the default


def test_figure_as_rigged_keeps_every_triangle():
    argv = addon_run.plan(figure_args(triangles="as rigged")).argv
    assert "--decimate-to" not in argv
    assert "--drop-hidden" not in argv


def test_figure_glow_colours():
    argv = addon_run.plan(figure_args(glow="#29e6ff, ff6a00")).argv
    assert [argv[i + 1] for i, a in enumerate(argv) if a == "--glow"] == ["#29e6ff", "#ff6a00"]
    assert "--glow-not-on-head" in argv and "--glow-not-on-hands" in argv


@pytest.mark.parametrize("glow", ["none", "", "  ", "None", "-"])
def test_figure_no_glow(glow):
    argv = addon_run.plan(figure_args(glow=glow)).argv
    assert "--glow" not in argv and "--glow-not-on-head" not in argv


def test_figure_refuses_a_bad_colour():
    with pytest.raises(SystemExit, match="colour"):
        addon_run.plan(figure_args(glow="test"))


def test_figure_refuses_a_bad_choice():
    with pytest.raises(SystemExit, match="bones"):
        addon_run.plan(figure_args(bones="roblox"))


def prop_args(**over):
    args = {"out": "/o/crate-2", "model": "/m/crate_5k.glb", "front": "+z", "axis": "height", "size": "0.8",
            "lods": "2500,1000", "collider": "box"}
    args.update(over)
    return ["blender", "--", args["out"], "prop", args["model"], args["front"], args["axis"], args["size"], args["lods"],
            args["collider"]]


def test_prop_options():
    job = addon_run.plan(prop_args())
    assert job.tool == "prop"
    assert job.result == Path("/o/crate-2/crate-2.glb")
    argv = job.argv
    assert argv[:2] == [str(Path("/m/crate_5k.glb")), str(Path("/o/crate-2"))]
    assert argv[argv.index("--name") + 1] == "crate-2"
    assert "--front=+z" in argv  # one token: argparse would read "-z" as an option
    assert argv[argv.index("--height") + 1] == "0.8"
    assert argv[argv.index("--lods") + 1] == "2500,1000"
    assert argv[argv.index("--collider") + 1] == "box"


def test_prop_front_minus_and_length():
    argv = addon_run.plan(prop_args(front="-x", axis="length", size="12")).argv
    assert "--front=-x" in argv
    assert argv[argv.index("--length") + 1] == "12"


def test_prop_lod0_is_the_result():
    job = addon_run.plan(prop_args())
    assert job.lod0 == Path("/o/crate-2/crate-2_LOD0.glb")


def test_unknown_tool():
    with pytest.raises(SystemExit, match="tool"):
        addon_run.plan(["blender", "--", "/o/x", "vehicle", "a"])


def make_python(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")
    return path


def test_python_of_the_install_the_addon_lives_in(tmp_path):
    root = tmp_path / "AssetFurnace"
    addon_dir = root / "addons" / "game-ready"
    addon_dir.mkdir(parents=True)
    windows = make_python(root / ".venv" / "Scripts" / "python.exe")
    assert addon_run.find_python(addon_dir, {}) == (windows, root)


def test_python_on_linux_and_mac(tmp_path):
    root = tmp_path / "af"
    addon_dir = root / "addons" / "game-ready"
    addon_dir.mkdir(parents=True)
    posix = make_python(root / ".venv" / "bin" / "python")
    assert addon_run.find_python(addon_dir, {}) == (posix, root)


def test_python_named_by_hand_wins(tmp_path):
    root = tmp_path / "af"
    addon_dir = root / "addons" / "game-ready"
    addon_dir.mkdir(parents=True)
    make_python(root / ".venv" / "bin" / "python")
    mine = make_python(tmp_path / "elsewhere" / "python.exe")
    assert addon_run.find_python(addon_dir, {"I2L_PYTHON": str(mine)}) == (mine, root)


def test_python_from_an_active_venv(tmp_path):
    addon_dir = tmp_path / "checkout" / "addons" / "game-ready"
    addon_dir.mkdir(parents=True)
    venv_python = make_python(tmp_path / "venv" / "Scripts" / "python.exe")
    found, root = addon_run.find_python(addon_dir, {"VIRTUAL_ENV": str(tmp_path / "venv")})
    assert found == venv_python
    assert root == tmp_path / "checkout"


def test_no_python_found(tmp_path):
    addon_dir = tmp_path / "loose" / "game-ready"
    addon_dir.mkdir(parents=True)
    assert addon_run.find_python(addon_dir, {})[0] is None


def test_glow_on_the_body_lines_or_on_the_eyes_alone():
    # a knight's red eye slit shares its red with his trims: "eyes only" keeps the glow on the head (AssetFurnace
    # Support D275); body lines stay the default, never on the face or the hands
    argv = addon_run.plan(figure_args(glow="#da294c")).argv
    assert "--glow-not-on-head" in argv and "--glow-not-on-hands" in argv and "--glow-only-on-head" not in argv
    argv = addon_run.plan(figure_args(glow="#da294c", look="clean") + ["eyes only"]).argv
    assert "--glow-only-on-head" in argv and "--glow-not-on-head" not in argv
    assert "--glow" not in addon_run.plan(figure_args(look="clean") + ["eyes only"]).argv
    with pytest.raises(SystemExit):
        addon_run.plan(figure_args(glow="#da294c", look="clean") + ["the left knee"])
