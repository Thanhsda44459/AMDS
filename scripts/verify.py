#!/usr/bin/env python3
"""Một lệnh kiểm tra toàn repo (TEST-001): lint + type + test cho cả hai vế.

Chạy bằng Python chuẩn thay vì PowerShell/bash để local và CI dùng chung đúng
một đường code — tránh trường hợp "CI xanh nhưng máy tôi đỏ" vì hai script khác nhau.

    python scripts/verify.py              # tất cả
    python scripts/verify.py --only lint  # chỉ lint
    python scripts/verify.py --skip test  # bỏ test (lúc đang viết code)

Thoát ngay khi một bước fail, và in bước đó để không phải đoán.
"""

import argparse
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
BACKEND = GOC / "backend"
FRONTEND = GOC / "frontend"
VENV_PY = BACKEND / ".venv" / "Scripts" / "python.exe"
POSIX_PY = BACKEND / ".venv" / "bin" / "python"


def python_backend() -> str:
    """Đường dẫn interpreter của venv backend, hoặc python hệ thống nếu chưa có venv."""
    if VENV_PY.is_file():
        return str(VENV_PY)
    if POSIX_PY.is_file():
        return str(POSIX_PY)
    return sys.executable


def npm(*args: str) -> list[str]:
    """npm trên Windows cần .cmd để shell tự tìm thấy."""
    return ["npm.cmd" if sys.platform == "win32" else "npm", *args]


def chay(ten: str, lenh: list[str], cwd: Path) -> bool:
    print(f"\n=== {ten} ===", flush=True)
    print("$ " + " ".join(str(x) for x in lenh), flush=True)
    ket_qua = subprocess.run(lenh, cwd=cwd, check=False)
    if ket_qua.returncode != 0:
        print(f"!!! FAIL: {ten} (mã {ket_qua.returncode})", flush=True)
        return False
    return True


# ruff format chỉ kiểm tra file mới: 20 file cũ tồn tại từ trước chưa format,
# để "check toàn repo" luôn đỏ thì lệnh này mất tác dụng. Xem scripts/verify.py --full-format.
CAC_BUOC = [
    ("backend lint", lambda: chay("backend lint (ruff check)", [python_backend(), "-m", "ruff", "check", "."], BACKEND)),
    ("backend test", lambda: chay("backend test (pytest)", [python_backend(), "-m", "pytest", "-q"], BACKEND)),
    ("frontend lint", lambda: chay("frontend lint (eslint)", npm("run", "lint"), FRONTEND)),
    ("frontend type", lambda: chay("frontend type + build (tsc -b)", npm("run", "build"), FRONTEND)),
    ("frontend test", lambda: chay("frontend test (vitest)", npm("test"), FRONTEND)),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Kiểm tra lint + type + test cho toàn repo.")
    ap.add_argument("--only", choices=["lint", "type", "test"], help="Chỉ chạy nhóm này.")
    ap.add_argument("--skip", choices=["lint", "type", "test"], action="append", default=[], help="Bỏ nhóm này.")
    args = ap.parse_args()

    nhom = {"lint": [b for b in CAC_BUOC if "lint" in b[0]],
            "type": [b for b in CAC_BUOC if "type" in b[0]],
            "test": [b for b in CAC_BUOC if "test" in b[0]]}

    if args.only:
        buoc = nhom[args.only]
    else:
        buoc = list(CAC_BUOC)

    for ten, ham in buoc:
        nhan = ten.split()[-1]
        if nhan in args.skip:
            print(f"--- bỏ qua: {ten}")
            continue
        if not ham():
            return 1

    print("\n=== TẤT CẢ ĐỀU XANH ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())