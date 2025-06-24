# backend/utils/assets.py
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
MANIFEST = BASE_DIR / "data" / "project_assets" / "manifest.json"

def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text())

def get_project_assets(project_slug: str) -> dict:
    manifest = load_manifest()
    if project_slug not in manifest:
        raise KeyError(f"No assets defined for '{project_slug}' in manifest.json")
    return manifest[project_slug]