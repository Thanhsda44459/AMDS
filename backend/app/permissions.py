"""Quyền cố định trong code (32 quyền, 9 nhóm), role động trong DB (ADR-009)."""

NHOM_QUYEN: dict[str, list[str]] = {
    "poi": ["read", "create", "update", "delete", "approve", "toggle"],
    "menu": ["read", "create", "update", "delete"],
    "user": ["read", "create", "update", "delete"],
    "role": ["read", "create", "update", "delete"],
    "analytics": ["view", "export", "view_own"],
    "audit": ["read", "manage"],
    "system": ["config", "logs", "backup"],
    "owner": ["register", "access", "submit_poi", "manage_own_poi"],
    "content": ["moderate", "publish"],
}

TAT_CA_QUYEN: list[str] = sorted(f"{nhom}:{hanh_dong}" for nhom, ds in NHOM_QUYEN.items() for hanh_dong in ds)


def quyen_admin() -> list[str]:
    """Admin có POI, Menu, User, Analytics, Audit, Content (không Role/System)."""
    nhom = ("poi", "menu", "user", "analytics", "audit", "content")
    return sorted(f"{n}:{h}" for n in nhom for h in NHOM_QUYEN[n])


ROLE_MAC_DINH: list[dict] = [
    {"name": "super_admin", "priority": 0, "permissions": TAT_CA_QUYEN},
    {"name": "admin", "priority": 1, "permissions": quyen_admin()},
    {
        "name": "poi_owner",
        "priority": 10,
        "permissions": [
            "poi:read",
            "owner:access",
            "owner:submit_poi",
            "owner:manage_own_poi",
            "menu:read",
            "menu:create",
            "menu:update",
            "analytics:view_own",
        ],
    },
    {"name": "user", "priority": 100, "permissions": ["poi:read", "menu:read", "owner:register"]},
]


async def dam_bao_roles(db) -> None:
    """Seed 4 role mặc định, chạy lại không nhân đôi."""
    for role in ROLE_MAC_DINH:
        await db["roles"].update_one({"name": role["name"]}, {"$set": role}, upsert=True)


async def quyen_cua_role(db, ten_role: str) -> list[str]:
    """Lấy danh sách quyền của role, lạ thì rỗng (không quyền)."""
    role = await db["roles"].find_one({"name": ten_role})
    return list(role.get("permissions", [])) if role else []
