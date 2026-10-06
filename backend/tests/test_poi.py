"""Test pytest đầu tiên cho POI, dùng DB test riêng."""

from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.config import settings

# Chuyển sang DB test riêng trước khi app khởi động.
settings.mongodb_db_name = "amds_test"

from app.main import app  # noqa: E402


def nap_mot_poi() -> str:
    """Xóa sạch rồi nạp 1 POI, trả về id chuỗi."""
    mongo = MongoClient(settings.mongodb_uri)
    col = mongo[settings.mongodb_db_name]["pois"]
    col.delete_many({})
    oid = col.insert_one(
        {
            "name": "Quán test",
            "description": "Mô tả test",
            "lat": 10.75,
            "lng": 106.76,
        }
    ).inserted_id
    mongo.close()
    return str(oid)


def test_lay_danh_sach() -> None:
    nap_mot_poi()
    with TestClient(app) as c:
        res = c.get("/poi")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["name"] == "Quán test"
    assert isinstance(data[0]["id"], str)


def test_lay_mot_404() -> None:
    nap_mot_poi()
    with TestClient(app) as c:
        res = c.get("/poi/000000000000000000000000")
    assert res.status_code == 404


def test_id_rac_400() -> None:
    with TestClient(app) as c:
        res = c.get("/poi/id-rac")
    assert res.status_code == 400
