"""Sinh manifest SHA-256 cho scope bản đồ từ tệp .pmtiles có sẵn."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.maps import SCOPES, manifest_scope


def main() -> None:
    for scope in SCOPES:
        info = manifest_scope(scope)
        print(json.dumps(info, indent=2, ensure_ascii=False))
        print(f"Scope {scope}: {len(info['files'])} tệp.")


if __name__ == "__main__":
    main()
