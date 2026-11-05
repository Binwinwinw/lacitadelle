import json
import shlex
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "dev" / "tools"))

import bootstrap
import creer_archive
import install
import lancer


def test_lancer_detects_windows():
    with patch("lancer.platform.system", return_value="Windows"):
        assert lancer.get_runtime_binary() == (
            PROJECT_ROOT / "dist" / "llamafile.exe"
        )


def test_lancer_detects_linux():
    with patch("lancer.platform.system", return_value="Linux"):
        assert lancer.get_runtime_binary() == (
            PROJECT_ROOT / "dist" / "llamafile-linux"
        )


def test_lancer_detects_macos():
    with patch("lancer.platform.system", return_value="Darwin"):
        assert lancer.get_runtime_binary() == (
            PROJECT_ROOT / "dist" / "llamafile-macos"
        )


def test_lancer_unsupported_os():
    with patch("lancer.platform.system", return_value="FreeBSD"):
        with pytest.raises(RuntimeError, match="FreeBSD"):
            lancer.get_runtime_binary()


def test_install_selects_linux_and_windows_destinations(tmp_path, monkeypatch):
    downloaded = []
    chmod_paths = []
    launched = []

    def fake_download(url, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(url.encode("utf-8"))
        downloaded.append((url, destination))

    def record_launch(command, *, cwd, check):
        launched.append((command, cwd, check))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(bootstrap, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(bootstrap, "download", fake_download)
    monkeypatch.setattr(bootstrap, "verify_sha256", lambda *_: None)
    monkeypatch.setattr(
        bootstrap,
        "_make_executable",
        lambda path: chmod_paths.append(path),
    )
    monkeypatch.setattr(install.subprocess, "run", record_launch)
    with patch("install.platform.system", side_effect=["Linux", "Windows"]):
        assert install.main() == 0
        linux_runtime = tmp_path / "dist" / "llamafile-linux"
        assert linux_runtime.is_file()
        assert len(chmod_paths) == 1
        assert chmod_paths[0].parent == linux_runtime.parent
        assert chmod_paths[0].name.startswith(".tmp-llamafile-0.10.6-thin-")
        assert install.main() == 0

    runtime_url = (
        "https://github.com/mozilla-ai/llamafile/releases/download/"
        "0.10.6/llamafile-0.10.6-thin"
    )
    windows_runtime = tmp_path / "dist" / "llamafile.exe"
    assert windows_runtime.is_file()
    assert windows_runtime not in chmod_paths
    runtime_downloads = [item for item in downloaded if item[0] == runtime_url]
    assert [item[1].parent for item in runtime_downloads] == [
        tmp_path / "dist",
        tmp_path / "dist",
    ]
    assert len(runtime_downloads) == 2
    assert len(launched) == 2


def test_install_rejects_invalid_sha256(tmp_path):
    asset = tmp_path / "asset"
    asset.write_bytes(b"runtime")
    with pytest.raises(bootstrap.BootstrapError, match="Checksum invalide"):
        bootstrap.verify_sha256(asset, "0" * 64)


def test_config_has_universal_runtime():
    config = json.loads(
        (PROJECT_ROOT / "dev" / "tools" / "llamafile_config.json").read_text(
            encoding="utf-8"
        )
    )
    runtime = config["assets"]["runtime-universal"]
    assert runtime["url"].endswith("/llamafile-0.10.6-thin")
    assert runtime["sha256"] == (
        "756bf97febae557084e8ced9bde7a1cb0c7f6ce778530d582afa219406237a50"
    )
    assert runtime["destination_by_os"] == {
        "Windows": "dist/llamafile.exe",
        "Linux": "dist/llamafile-linux",
        "Darwin": "dist/llamafile-macos",
    }


def test_archive_includes_wrappers_and_executable_permissions(tmp_path, monkeypatch):
    archive_path = tmp_path / "lacitadelle-distribution.zip"
    monkeypatch.setattr(creer_archive, "ARCHIVE_PATH", archive_path)

    assert creer_archive.main() == 0
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert set(creer_archive.ROOT_WRAPPERS) <= names
        assert "dev/tools/lancer.py" in names
        assert "dev/tools/install.py" in names
        assert not any(
            name.endswith((".gguf", ".exe"))
            or name in {"dist/llamafile-linux", "dist/llamafile-macos"}
            for name in names
        )
        for name in ("lancer.sh", "lancer.command", "install.sh", "install.command"):
            mode = archive.getinfo(name).external_attr >> 16 & 0o777
            assert mode == 0o755


def test_archive_normalizes_shell_wrapper_line_endings(tmp_path, monkeypatch):
    wrapper_names = (
        "install.sh",
        "lancer.sh",
        "install.command",
        "lancer.command",
    )
    for name in creer_archive.ROOT_WRAPPERS:
        content = (
            b"#!/usr/bin/env bash\r\necho ready\r\n"
            if name in wrapper_names
            else b"@echo off\r\necho ready\r\n"
        )
        (tmp_path / name).write_bytes(content)

    archive_path = tmp_path / "distribution.zip"
    monkeypatch.setattr(creer_archive, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(creer_archive, "ARCHIVE_PATH", archive_path)

    assert creer_archive.main() == 0
    with zipfile.ZipFile(archive_path) as archive:
        for name in wrapper_names:
            content = archive.read(name)
            assert b"\r\n" not in content
            assert b"\n" in content
            assert content.startswith(b"#!/usr/bin/env bash\n")
            mode = archive.getinfo(name).external_attr >> 16 & 0o777
            assert mode == 0o755


def test_lancer_uses_sh_c_on_unix(tmp_path):
    binary = tmp_path / "runtime binary"
    gguf = tmp_path / "model file.gguf"
    popen = MagicMock()
    expected_args = [
        str(binary),
        "-m",
        str(gguf),
        "--server",
        "--host",
        "127.0.0.1",
        "--port",
        "8080",
        *lancer.RUNTIME_OPTIONS,
    ]
    with (
        patch("lancer.platform.system", return_value="Linux"),
        patch("lancer.subprocess.Popen", popen),
    ):
        lancer.start_llamafile(binary, gguf, "127.0.0.1", 8080)

    command = popen.call_args.args[0]
    assert command[:2] == ["sh", "-c"]
    assert command[2].startswith("exec ")
    assert shlex.split(command[2][len("exec "):]) == expected_args
    assert popen.call_args.kwargs["start_new_session"] is True
    assert expected_args.index("-m") < expected_args.index("--server")


def test_lancer_uses_exec_on_unix(tmp_path):
    binary = tmp_path / "runtime binary"
    gguf = tmp_path / "model file.gguf"
    with (
        patch("lancer.platform.system", return_value="Linux"),
        patch("lancer.subprocess.Popen") as popen,
    ):
        lancer.start_llamafile(binary, gguf, "127.0.0.1", 8080)

    command = popen.call_args.args[0]
    assert command[:2] == ["sh", "-c"]
    assert command[2].startswith("exec ")
    assert str(binary) in shlex.split(command[2])


def test_lancer_uses_start_new_session_on_macos(tmp_path):
    with (
        patch("lancer.platform.system", return_value="Darwin"),
        patch("lancer.subprocess.Popen") as popen,
    ):
        lancer.start_llamafile(
            tmp_path / "llamafile",
            tmp_path / "model.gguf",
            "127.0.0.1",
            8080,
        )

    assert popen.call_args.args[0][:2] == ["sh", "-c"]
    assert popen.call_args.kwargs["start_new_session"] is True


def test_lancer_windows_remains_direct_without_new_session(tmp_path):
    binary = tmp_path / "llamafile.exe"
    gguf = tmp_path / "model.gguf"
    with (
        patch("lancer.platform.system", return_value="Windows"),
        patch("lancer.subprocess.Popen") as popen,
    ):
        lancer.start_llamafile(binary, gguf, "127.0.0.1", 8080)

    command = popen.call_args.args[0]
    assert command[0] == str(binary)
    assert command[1:3] == ["-m", str(gguf)]
    assert "sh" not in command
    assert "start_new_session" not in popen.call_args.kwargs


def test_lancer_windows_uses_direct_popen(tmp_path):
    binary = tmp_path / "llamafile.exe"
    gguf = tmp_path / "model.gguf"
    expected_args = [
        str(binary),
        "-m",
        str(gguf),
        "--server",
        "--host",
        "127.0.0.1",
        "--port",
        "8080",
        *lancer.RUNTIME_OPTIONS,
    ]
    with (
        patch("lancer.platform.system", return_value="Windows"),
        patch("lancer.subprocess.Popen") as popen,
    ):
        lancer.start_llamafile(
            binary,
            gguf,
            "127.0.0.1",
            8080,
            creationflags=123,
        )

    popen.assert_called_once_with(
        expected_args,
        cwd=PROJECT_ROOT,
        creationflags=123,
    )
