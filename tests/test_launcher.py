"""The launcher puts the add-on's scripts first and lends the two checks to AssetFurnace's own package."""

import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import launcher


def test_paths_put_the_addon_first_and_the_install_after(tmp_path, monkeypatch):
    root = tmp_path / "AssetFurnace"
    (root / "scripts").mkdir(parents=True)
    path = ["site-packages"]
    monkeypatch.setattr(sys, "path", path)
    launcher.set_paths(root)
    assert path[0] == str(HERE / "scripts")
    assert path.index(str(root)) < path.index("site-packages")
    assert path.index(str(root / "scripts")) > path.index(str(HERE / "scripts"))


def test_the_checks_join_the_installed_package(monkeypatch):
    package = types.ModuleType("image_to_3dlab")
    package.__path__ = ["/install/image_to_3dlab"]
    monkeypatch.setitem(sys.modules, "image_to_3dlab", package)
    launcher.lend_checks()
    assert package.__path__ == ["/install/image_to_3dlab", str(HERE / "extra")]
    launcher.lend_checks()  # twice changes nothing
    assert package.__path__.count(str(HERE / "extra")) == 1


def test_every_lent_module_is_one_the_core_lacks():
    """When AssetFurnace ships one of them itself, its own copy wins: the install's folder comes first."""
    assert sorted(p.name for p in (HERE / "extra").glob("*.py")) == ["colour_compare.py", "outline_check.py"]
