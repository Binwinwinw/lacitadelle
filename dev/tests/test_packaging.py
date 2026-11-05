import sys
from pathlib import Path
from unittest.mock import patch

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import paths


def test_get_user_data_dir_windows(tmp_path):
    appdata = tmp_path / "Roaming"
    with (
        patch("paths.platform.system", return_value="Windows"),
        patch.dict("os.environ", {"APPDATA": str(appdata)}),
    ):
        assert paths.get_user_data_dir() == appdata / "LaCitadelle"


def test_get_user_data_dir_macos(tmp_path):
    with (
        patch("paths.platform.system", return_value="Darwin"),
        patch.object(Path, "home", return_value=tmp_path),
    ):
        assert paths.get_user_data_dir() == (
            tmp_path / "Library" / "Application Support" / "LaCitadelle"
        )


def test_get_user_data_dir_linux(tmp_path):
    data_home = tmp_path / "xdg-data"
    with (
        patch("paths.platform.system", return_value="Linux"),
        patch.dict("os.environ", {"XDG_DATA_HOME": str(data_home)}),
    ):
        assert paths.get_user_data_dir() == data_home / "LaCitadelle"


def test_get_app_dir_in_development():
    with patch.object(paths.sys, "frozen", False, create=True):
        assert paths.get_app_dir() == Path(__file__).resolve().parents[2]


def test_get_app_and_bundle_dirs_when_frozen(tmp_path):
    executable_dir = tmp_path / "application"
    bundle_dir = tmp_path / "onefile-temp"
    executable_dir.mkdir()
    bundle_dir.mkdir()
    with (
        patch.object(paths.sys, "frozen", True, create=True),
        patch.object(
            paths.sys,
            "executable",
            str(executable_dir / "LaCitadelle.exe"),
        ),
        patch.object(paths.sys, "_MEIPASS", str(bundle_dir), create=True),
    ):
        assert paths.get_app_dir() == executable_dir
        assert paths.get_bundle_dir() == bundle_dir
