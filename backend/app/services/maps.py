"""Gói offline: đường dẫn an toàn, manifest SHA-256, tùy chọn tải."""

import hashlib
from pathlib import Path
from urllib.parse import unquote

from fastapi import HTTPException

THU_MUC_MAPS = Path(__file__).resolve().parents[2] / "static" / "maps"

# Hai scope theo plan: Quận 4 gọn nhẹ, TP.HCM đầy đủ hơn.
SCOPES = ("quan4", "hcm")


def duong_an_toan(ten_tep: str) -> Path:
    """Giải mã phần trăm rồi chuẩn hóa, còn trong gốc mới cho qua."""
    giai_ma = unquote(unquote(ten_tep))
    base = THU_MUC_MAPS.resolve()
    dich = (base / giai_ma).resolve()
    if dich != base and base not in dich.parents:
        raise HTTPException(status_code=400, detail="Đường dẫn không hợp lệ")
    return dich


def sha256_tep(tep: Path) -> str:
    h = hashlib.sha256()
    with tep.open("rb") as f:
        for mieng in iter(lambda: f.read(65536), b""):
            h.update(mieng)
    return h.hexdigest()


def manifest_scope(scope: str) -> dict:
    """Manifest một scope: danh sách tệp kèm hash để client kiểm toàn vẹn."""
    thu_muc = THU_MUC_MAPS / scope
    tep_list = []
    if thu_muc.is_dir():
        for tep in sorted([*thu_muc.glob("*.pmtiles"), *thu_muc.glob("*.json")]):
            tep_list.append(
                {
                    "file": f"{scope}/{tep.name}",
                    "sha256": sha256_tep(tep),
                    "bytes": tep.stat().st_size,
                }
            )
    fingerprint = hashlib.sha256(str([(t["file"], t["sha256"]) for t in tep_list]).encode()).hexdigest()
    return {"scope": scope, "files": tep_list, "fingerprint": fingerprint}


async def manifest_audio_pack(db, lang: str) -> dict:
    """Manifest gói audio theo ngôn ngữ từ audio_url local đã có."""
    ds = []
    async for ban in db["poi_localizations"].find({"lang": lang, "audio_url": {"$ne": None}}):
        url = str(ban["audio_url"]).split("?")[0]
        if not url.startswith("/static/audio/"):
            continue
        tep = THU_MUC_MAPS.parent / "audio" / Path(url).name
        if tep.is_file():
            ds.append({"url": url, "sha256": sha256_tep(tep), "bytes": tep.stat().st_size})
    return {"lang": lang, "files": ds}
