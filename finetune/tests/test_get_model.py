import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import get_model  # noqa: E402


def make_zip(path, names, prefix="b-tok2/"):
    with zipfile.ZipFile(path, "w") as z:
        for name in names:
            z.writestr(prefix + name, "x")
    return path


def test_install_unpacks_a_complete_model(tmp_path):
    z = make_zip(tmp_path / "m.zip", get_model.NEEDED)
    folder = get_model.install(z, out_dir=tmp_path / "out")
    assert get_model.is_installed(folder)
    assert folder == (tmp_path / "out" / "b-tok2").resolve()


def test_install_rejects_an_incomplete_zip(tmp_path):
    z = make_zip(tmp_path / "m.zip", ["config.json"])
    with pytest.raises(SystemExit):
        get_model.install(z, out_dir=tmp_path / "out")


def test_install_rejects_paths_that_escape_the_folder(tmp_path):
    z = tmp_path / "evil.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("../escaped.txt", "x")
    with pytest.raises(SystemExit):
        get_model.install(z, out_dir=tmp_path / "out")
    assert not (tmp_path / "escaped.txt").exists()


def test_checksum_is_stable_and_detects_changes(tmp_path):
    a = tmp_path / "a.bin"
    a.write_bytes(b"hello")
    first = get_model.sha256_of(a)
    assert first == get_model.sha256_of(a)
    a.write_bytes(b"hellO")
    assert first != get_model.sha256_of(a)
