"""Guardas locales del bundle; el restore PostgreSQL se prueba con un drill real."""

import json
from types import SimpleNamespace

import pytest

from scripts import local_recovery as recovery


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / "backup"
    root.mkdir(mode=0o700)
    media = root / "media"
    media.mkdir(mode=0o700)
    (media / "document.pdf").write_bytes(b"sample recovery bytes")
    (root / "database.dump").write_bytes(b"sample archive bytes")
    recovery.write_json(root / "manifest.json", {
        "format_version": 2,
        "dump_sha256": recovery.sha(root / "database.dump"),
        "media": recovery.media_inventory(media),
    })
    (root / "manifest.sha256").write_text(recovery.sha(root / "manifest.json") + "\n")
    for path in root.rglob("*"):
        if path.is_file():
            path.chmod(0o600)
    return root


@pytest.mark.parametrize("change", ["dump", "missing_media", "changed_media", "extra_media", "manifest", "public", "symlink"])
def test_refuses_bad_bundle_before_starting_any_container(bundle, tmp_path, monkeypatch, change):
    if change == "dump":
        (bundle / "database.dump").write_bytes(b"truncated")
    elif change == "missing_media":
        (bundle / "media/document.pdf").unlink()
    elif change == "changed_media":
        (bundle / "media/document.pdf").write_bytes(b"modified document")
    elif change == "extra_media":
        (bundle / "media/unexpected.pdf").write_bytes(b"unregistered")
        (bundle / "media/unexpected.pdf").chmod(0o600)
    elif change == "manifest":
        (bundle / "manifest.json").write_text(json.dumps({"format_version": 2}))
    elif change == "public":
        (bundle / "database.dump").chmod(0o644)
    else:
        (bundle / "media/document.pdf").unlink()
        (bundle / "media/document.pdf").symlink_to(bundle / "database.dump")

    def must_not_run(*args, **kwargs):
        pytest.fail("Un respaldo inválido no debe iniciar contenedores")

    monkeypatch.setattr(recovery, "run", must_not_run)
    with pytest.raises(ValueError):
        recovery.restore_isolated(SimpleNamespace(bundle=bundle, destination=tmp_path / "restore", runtime="podman"))
    assert not (tmp_path / "restore").exists()


def test_missing_media_root_does_not_silently_become_empty(tmp_path):
    with pytest.raises(ValueError, match="MEDIA_ROOT"):
        recovery.media_inventory(tmp_path / "not-mounted")


def test_copy_rejects_traversal(tmp_path):
    with pytest.raises(ValueError, match="fuera"):
        recovery.copy_media(tmp_path, tmp_path / "output", {"../outside": {}})
    assert not (tmp_path / "outside").exists()


def test_valid_bundle_and_private_copy(bundle, tmp_path):
    data = recovery.verify_bundle(bundle)
    recovery.copy_media(bundle / "media", tmp_path / "restored", data["media"])
    assert recovery.media_inventory(tmp_path / "restored") == data["media"]
    assert (tmp_path / "restored/document.pdf").stat().st_mode & 0o777 == 0o600


def test_postgres_array_cast_roundtrip_without_weakening_constraints():
    before = "CHECK (kind::text = ANY ((ARRAY['A'::character varying, 'B'::character varying])::text[]))"
    restored = "CHECK (kind::text = ANY (ARRAY[('A'::character varying)::text, ('B'::character varying)::text]))"
    assert recovery.canonical_constraints(before) == restored
    assert recovery.canonical_constraints(before.replace("'B'", "'C'")) != restored
    expression = "(ARRAY[current_user::character varying])::text[]"
    assert recovery.canonical_constraints(expression) == expression
    numeric = "(ARRAY['1'::character varying])::integer[]"
    assert recovery.canonical_constraints(numeric) == numeric
