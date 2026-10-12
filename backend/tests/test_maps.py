"""Test maps: traversal bị chặn, hash đổi theo byte, manifest no-cache."""

from fastapi.testclient import TestClient

from app.config import settings

settings.mongodb_db_name = "amds_test"

from app.main import app  # noqa: E402
from app.services.maps import THU_MUC_MAPS, duong_an_toan, sha256_tep  # noqa: E402


def test_traversal_bi_chan() -> None:
    from fastapi import HTTPException

    for xau in ("../../etc/passwd", "%2e%2e/x", "/etc/passwd", "..\\win.ini"):
        try:
            duong_an_toan(xau)
            raise AssertionError(f"phải chặn: {xau}")
        except HTTPException as exc:
            assert exc.status_code == 400


def test_hash_doi_theo_byte(tmp_path) -> None:
    a = tmp_path / "a.pmtiles"
    a.write_bytes(b"mot")
    b = tmp_path / "b.pmtiles"
    b.write_bytes(b"hai")
    assert sha256_tep(a) != sha256_tep(b)
    a.write_bytes(b"hai")
    assert sha256_tep(a) == sha256_tep(b)


def test_manifest_no_cache_va_pack_404() -> None:
    with TestClient(app) as c:
        res = c.get("/maps/manifest?scope=quan4")
        assert res.status_code == 200
        assert res.headers.get("Cache-Control") == "no-cache"
        assert "fingerprint" in res.json()
        assert c.get("/maps/pack/quan4/../../main.py").status_code in (400, 404)
        assert c.get("/maps/pack/quan4/khong-co.pmtiles").status_code == 404
        opt = c.get("/maps/offline-options")
        assert "quan4" in opt.json()["scopes"]


def test_pack_that_immutable(tmp_path) -> None:
    scope_dir = THU_MUC_MAPS / "quan4"
    scope_dir.mkdir(parents=True, exist_ok=True)
    tep = scope_dir / "kiem-thu.pmtiles"
    tep.write_bytes(b"pmtiles-gia")
    try:
        with TestClient(app) as c:
            res = c.get("/maps/pack/quan4/kiem-thu.pmtiles")
            assert res.status_code == 200
            assert "immutable" in res.headers.get("Cache-Control", "")
            man = c.get("/maps/manifest?scope=quan4").json()
            assert any(f["file"] == "quan4/kiem-thu.pmtiles" for f in man["files"])
    finally:
        tep.unlink(missing_ok=True)
