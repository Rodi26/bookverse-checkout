import json
import os
from pathlib import Path


def main() -> None:
    # Lazy import to avoid side effects when not needed
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


