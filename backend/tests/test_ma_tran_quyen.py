"""TEST-004: ma trận quyền tự động cho TOÀN BỘ route của app.

Bài toán thật ở đây: app có hơn 40 route và mỗi route một kiểu guard khác nhau.
Nguy cơ không phải "quyền sai" mà là **route mới thêm vào mà quên gắn guard** —
lúc đó mọi người đều đoán. Vì vậy test này có hai phần:

1. **Độ phủ**: route nào tồn tại trong app mà không có trong bảng khai báo thì
   FAIL ngay, kèm tên route để người viết biết cần khai báo gì.
2. **Hành vi**: đăng nhập bằng từng role rồi gọi từng route, đối chiếu mã trạng
   thái mong đợi (401 chưa đăng nhập, 403 thiếu quyền, 2xx được phép).

Bảng khai báo là nguồn sự thật cho *ý định*, còn app.routes là nguồn sự thật cho
*hiện trạng* — test bắt được độ lệch giữa hai thứ.

Route công khai có guard riêng (consent, rate limit) chứ không dùng `doi_quyen`,
nên phải khai báo rõ `cong_khai` thay vì mặc định coi là "không có quyền".
"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.config import settings

settings.mongodb_db_name = "amds_test"

from app.main import app  # noqa: E402
from app.permissions import ROLE_MAC_DINH, dam_bao_roles  # noqa: E402

# Mỗi route: (method, path) -> (quyền hoặc None, mã kỳ vọng khi thiếu quyền)
# None nghĩa là route công khai (guard riêng, không dùng doi_quyen).
KHAI_BAO: dict[str, str | None] = {
    # ---- Công khai: xem nội dung POI ----
    "GET /": None,
    "GET /health": None,
    "GET /poi": None,
    "GET /poi/load-all": None,
    "GET /poi/delta": None,
    "GET /poi/nearby": None,
    "GET /poi/hotset": None,
    "GET /poi/{poi_id}": None,
    "GET /ui-bundles/{locale}": None,
    "GET /maps/offline-options": None,
    "GET /maps/manifest": None,
    "GET /maps/pack/{scope}/{ten_tep}": None,
    "GET /maps/audio-pack": None,
    "GET /maps/thu-muc": None,
    "GET /audio/giong": None,
    # ---- Công khai nhưng có guard riêng: consent / rate limit ----
    "GET /analytics/consent": None,
    "POST /analytics/consent": None,
    "POST /analytics/collect": None,
    "POST /runtime-observability/location": None,
    # ---- Đăng nhập, không cần quyền ----
    "POST /admin/auth/login": None,
    "POST /admin/auth/logout": None,
    "POST /owner/register": None,
    # ---- Cần đăng nhập (bất kỳ role nào đã đăng nhập) ----
    "GET /admin/auth/me": "__dang_nhap__",
    "POST /admin/auth/refresh": "__refresh__",
    "GET /audio/tasks": "__dang_nhap__",
    "GET /audio/tasks/stream": "__dang_nhap__",
    "POST /audio/tasks/{task_id}/{lenh}": "__dang_nhap__",
    "POST /audio/tts": "__dang_nhap__",
    "POST /audio/on-demand": "__dang_nhap__",
    "POST /localizations/on-demand": "__dang_nhap__",
    "POST /localizations/warmup": "poi:update",
    "GET /localizations/warmup-status": "poi:update",
    # ---- Owner ----
    "GET /owner/registration-status": "__dang_nhap__",
    "GET /owner/submissions/mine": "__owner_duyet__",
    "GET /owner/notifications": "__owner_duyet__",
    "POST /owner/notifications/{nid}/read": "__owner_duyet__",
    "POST /owner/submissions": "__owner_duyet__",
    "GET /owner/submissions/pending": "poi:approve",
    "GET /owner/registrations": "user:update",
    "POST /owner/registrations/{username}/approve": "user:update",
    "POST /owner/registrations/{username}/reject": "user:update",
    "POST /owner/submissions/{sid}/approve": "poi:approve",
    # ---- Admin POI ----
    "POST /admin/pois": "poi:create",
    "PUT /admin/pois/{poi_id}": "poi:update",
    "DELETE /admin/pois/{poi_id}": "poi:delete",
    # ---- Admin meta ----
    "GET /admin/roles": "role:read",
    "GET /admin/audit-logs": "audit:read",
    # ---- AI ----
    "POST /ai/enhance-description": "__dang_nhap__",
    # ---- Analytics (ADM-005) ----
    "GET /admin/analytics/summary": "analytics:view",
    "GET /admin/runtime-observability/location": "analytics:view",
}


def duyet(route):
    """Duyệt cây route của app, mở vò các router bị FastAPI gói lại.

    Nhận được cả một route lẫn một danh sách route: truyền `app` sẽ ra 1 phần
    tử (chính object app, không có `.path`), truyền `app.routes` mà không mở
    vò thì chỉ ra 1 phần tử là cả list — cả hai đều ra kết quả rỗng.

    `_IncludedRouter` của FastAPI 0.141 giữ một `APIRouter` ở `original_router`,
    và phải duyệt `.routes` của nó; duyệt trực tiếp object đó không ra route nào.
    """
    if isinstance(route, list):
        for r in route:
            yield from duyet(r)
        return
    if type(route).__name__ == "_IncludedRouter":
        for con in route.original_router.routes:
            yield from duyet(con)
        return
    yield route


def tach(path: str) -> list[str]:
    return [m for m in path.strip("/").split("/") if m]


def la_tham_so(seg: str) -> bool:
    return seg.startswith("{") and seg.endswith("}")


def khop_path(path_that: str, path_mau: str) -> bool:
    """Path thật khớp path mẫu khi mỗi phần tử bằng nhau hoặc mẫu là tham số động."""
    a, b = tach(path_that), tach(path_mau)
    if len(a) != len(b):
        return False
    return all(x == y or la_tham_so(y) for x, y in zip(a, b, strict=True))


# Đường dẫn đã khai báo, gom theo method để khớp nhanh và tránh lấy nhầm
# path của method khác (ví dụ "GET /poi" khác "POST /audio/poi").
THEO_METHOD: dict[str, list[str]] = {}
for _khoa in KHAI_BAO:
    _method, _duong_dan = _khoa.split(" ", 1)
    THEO_METHOD.setdefault(_method, []).append(_duong_dan)


def route_that(method: str, path: str) -> str:
    """Rút route thật về khóa khai báo đầy đủ ("GET /poi/nearby").

    `/poi/nearby` phải khớp `"/poi/nearby"` chứ không phải `"/poi/{poi_id}"`,
    nên khi nhiều mẫu cùng khớp thì chọn mẫu có nhiều phần tử cố định hơn
    (ít tham số động hơn). Trả về kèm method để so trực tiếp với KHAI_BAO.
    """
    ung_vien = [d for d in THEO_METHOD.get(method, []) if khop_path(path, d)]
    if not ung_vien:
        return f"{method} {path}"
    tot_phan_tu_dong = lambda d: sum(1 for s in tach(d) if la_tham_so(s))  # noqa: E731
    return f"{method} {min(ung_vien, key=tot_phan_tu_dong)}"


def tat_ca_route() -> set[str]:
    ra: set[str] = set()
    for r in duyet(app.routes):
        path = getattr(r, "path", None)
        if not path or path.startswith(("/docs", "/openapi", "/redoc", "/static")):
            continue
        for method in sorted(getattr(r, "methods", {"GET"}) - {"HEAD", "OPTIONS"}):
            ra.add(f"{method} {path}")
    return ra


def khoa_khai_bao_thuc() -> set[str]:
    """Mọi route thật, đã rút về khóa khai báo."""
    ra: set[str] = set()
    for r in tat_ca_route():
        method, path = r.split(" ", 1)
        ra.add(route_that(method, path))
    return ra


def nap_nguoi_dung() -> dict[str, str]:
    from pymongo import MongoClient

    from app.auth import bam_mat_khau

    async def nap() -> None:
        from motor.motor_asyncio import AsyncIOMotorClient

        a = AsyncIOMotorClient(settings.mongodb_uri)
        db = a[settings.mongodb_db_name]
        await dam_bao_roles(db)
        await db["admin_users"].delete_many({})
        for ten, role in (("root", "super_admin"), ("quanly", "admin"), ("chu", "poi_owner")):
            await db["admin_users"].insert_one(
                {"username": ten, "password_hash": bam_mat_khau("pw123456"), "role": role}
            )

    asyncio.run(nap())
    mongo = MongoClient(settings.mongodb_uri)
    db = mongo[settings.mongodb_db_name]
    return {d["username"]: d["role"] for d in db["admin_users"].find({}, {"username": 1, "role": 1})}


def client_dang_nhap(ten: str):
    """Đăng nhập rồi trả TestClient. Bắt buộc dùng `with` để chạy lifespan,
    nếu không sẽ chưa có connect_db() và mọi truy vấn ném RuntimeError."""
    c = TestClient(app)
    c.__enter__()
    res = c.post("/admin/auth/login", json={"username": ten, "password": "pw123456"})
    assert res.status_code == 200, f"đăng nhập {ten} thất bại: {res.status_code}"
    return c


# --- Phần 1: độ phủ khai báo ---


def test_moi_route_deu_co_khai_bao() -> None:
    """Route mới thêm mà chưa khai báo thì test FAIL — đúng mục đích của TEST-004."""
    thieu = sorted(khoa_khai_bao_thuc() - set(KHAI_BAO))
    assert thieu == [], (
        "Route mới chưa có trong bảng KHAI_BAO của test_ma_tran_quyen.py:\n"
        + "\n".join(f"  {r}" for r in thieu)
        + "\nThêm vào KHAI_BAO với quyền thật, hoặc None nếu là route công khai."
    )


def test_khai_bao_thua_route_khong_ton_tai() -> None:
    """Ngược lại: khai báo mà route đã bị xoá thì báo lại, tránh bảng lỗi thời."""
    thua = sorted(set(KHAI_BAO) - khoa_khai_bao_thuc())
    assert thua == [], "KHAI_BAO mô tả route không còn tồn tại:\n" + "\n".join(
        f"  {r}" for r in thua
    )


def test_moi_quyen_trong_ma_tran_deu_ton_tai_trong_he_thong() -> None:
    """Ma trận không được viết sai tên quyền, không phải so với danh sách quyền thật."""
    from app.permissions import TAT_CA_QUYEN

    hop_le = set(TAT_CA_QUYEN)
    for khoa, quyen in KHAI_BAO.items():
        if quyen is None or quyen.startswith("__"):
            continue
        assert quyen in hop_le, f"{khoa} đòi quyền '{quyen}' không có trong hệ thống"


def test_moi_role_trong_ma_tran_deu_ton_tai() -> None:
    ten = {r["name"] for r in ROLE_MAC_DINH}
    assert {"super_admin", "admin", "poi_owner"} <= ten


# --- Phần 2: hành vi thực tế theo từng role ---


def test_voi_poi_owner_moi_route_bien_anh_403() -> None:
    """poi_owner là vai trò hẹp nhất: mọi route đòi quyền hành phải trả 403."""
    nap_nguoi_dung()
    path_that = {
        "/admin/pois": "POST",
        "/admin/pois/000000000000000000000000": "PUT",
        "/admin/roles": "GET",
        "/admin/audit-logs": "GET",
        "/admin/analytics/summary": "GET",
        "/admin/runtime-observability/location": "GET",
        "/owner/registrations": "GET",
        "/localizations/warmup": "POST",
        "/localizations/warmup-status": "GET",
    }
    with client_dang_nhap("chu") as c:
        for path, method in path_that.items():
            res = c.request(method, path)
            assert res.status_code == 403, f"{method} {path} trả {res.status_code}, cần 403"


def test_super_admin_duoc_phep_moi_route_quan_tri() -> None:
    """super_admin có TẤT CẢ quyền nên route quản trị phải không phải 403."""
    nap_nguoi_dung()
    path_that = {
        "/admin/roles": "GET",
        "/admin/audit-logs": "GET",
        "/admin/analytics/summary": "GET",
        "/admin/runtime-observability/location": "GET",
        "/owner/registrations": "GET",
        "/localizations/warmup-status": "GET",
    }
    with client_dang_nhap("root") as c:
        for path, method in path_that.items():
            res = c.request(method, path)
            assert res.status_code != 403, f"{method} {path} bị 403 dù super_admin"


def test_admin_thieu_quyen_he_thong_bi_403() -> None:
    """admin không có quyền system/role (ADR-009) nên phải bị chặn."""
    nap_nguoi_dung()
    with client_dang_nhap("quanly") as c:
        assert c.get("/admin/roles").status_code == 403
        assert c.get("/admin/analytics/summary").status_code == 200


def test_route_quan_tri_phan_401_khi_khong_dang_nhap() -> None:
    """Mọi route quản trị phải chặn cả người chưa đăng nhập, không chỉ người thiếu quyền."""
    nap_nguoi_dung()
    path_that = [
        ("GET", "/admin/roles"),
        ("GET", "/admin/audit-logs"),
        ("GET", "/admin/analytics/summary"),
        ("GET", "/admin/runtime-observability/location"),
        ("GET", "/owner/registrations"),
        ("POST", "/admin/pois"),
        ("PUT", "/admin/pois/000000000000000000000000"),
        ("DELETE", "/admin/pois/000000000000000000000000"),
        ("GET", "/localizations/warmup-status"),
    ]
    with TestClient(app) as c:
        for method, path in path_that:
            res = c.request(method, path)
            assert res.status_code == 401, f"{method} {path} trả {res.status_code}, cần 401"


@pytest.mark.parametrize(
    ("method", "path"),
    [(m, p) for m, p in (r.split(" ", 1) for r in sorted(tat_ca_route()))],
)
def test_khong_route_nao_tra_500(method: str, path: str) -> None:
    """Guard thiếu thường biểu hiện thành 500 hoặc 403 sai; phải là 401/403/2xx/4xx có kiểm soát."""
    if any(b in path for b in ("{", "/openapi", "/docs", "/redoc")):
        pytest.skip("route có tham số động, cần test riêng với giá trị thật")
    nap_nguoi_dung()
    with TestClient(app) as c:
        res = c.request(method, path)
    assert res.status_code < 500, f"{method} {path} trả {res.status_code}"