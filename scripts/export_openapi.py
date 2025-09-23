import json
import os
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from app.main import app

    schema = app.openapi()
    out_dir = Path(os.getenv("OPENAPI_OUT_DIR", "dist"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "openapi.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"Wrote {out_file}")


if __name__ == "__main__":
    main()


