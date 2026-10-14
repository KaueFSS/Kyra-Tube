import hashlib

import pytest

from core import updater


def test_parse_version_ignores_the_v_and_spaces():
    assert updater.parse_version("v3.1.0") == (3, 1, 0)
    assert updater.parse_version(" 3.0.0 ") == (3, 0, 0)
    assert updater.parse_version("lixo") == (0,)


def test_newer_compares_numbers_not_text():
    assert updater.is_newer("3.10.0", local="3.9.0")  # 10 > 9, não "3.1" < "3.9"
    assert updater.is_newer("v3.0.1", local="3.0.0")
    assert not updater.is_newer("3.0.0", local="3.0.0")
    assert not updater.is_newer("2.9.9", local="3.0.0")


def test_notes_take_the_first_bullet_lines():
    body = "Novidades:\n- Primeira\n- Segunda\n\n* Terceira\n- Quarta"
    assert updater.parse_notes(body) == ["Primeira", "Segunda", "Terceira"]
    assert updater.parse_notes("") == []
    assert updater.parse_notes(None) == []


def test_verify_accepts_the_right_hash_and_rejects_a_wrong_one(tmp_path):
    f = tmp_path / "setup.exe"
    f.write_bytes(b"instalador")
    right = hashlib.sha256(b"instalador").hexdigest()
    updater.verify(f, right)
    updater.verify(f, right.upper())
    updater.verify(f, None)  # o GitHub não informou hash: nada a conferir
    with pytest.raises(updater.UpdateError):
        updater.verify(f, "0" * 64)
