import openai
import hashlib
import json
from pathlib import Path

CACHE_FILE = Path("openai_file_cache.json")

def load_cache():
    if CACHE_FILE.exists():
        with CACHE_FILE.open("r") as f:
            return json.load(f)
    return {}

def save_cache(cache: dict):
    with CACHE_FILE.open("w") as f:
        json.dump(cache, f, indent=2)

def compute_file_hash(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def upload_file_cached(file_path: str, purpose: str = "assistants") -> str:
    """
    Uploads a file to OpenAI with local hash-based caching.

    If the file has already been uploaded, reuse the existing file_id.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found.")

    cache = load_cache()
    file_hash = compute_file_hash(file_path)

    if file_hash in cache:
        return cache[file_hash]

    with file_path.open("rb") as f:
        response = openai.files.create(file=f, purpose=purpose)

    cache[file_hash] = response.id
    save_cache(cache)

    return response.id

CONFIG_PATH = Path("project_assets.json")
ASSETS_ROOT = Path(__file__).parent / "assets"
ASSETS = {
    "V_mall": {
    },
    "V_Metroway": {
        "ara": ASSETS_ROOT / "svg" / "V_metroway" / "genel.svg",
        "cover": ASSETS_ROOT / "svg" / "V_metroway" / "kapak.svg"
    }
}


def populate_config():
    config = {}
    for project, files in ASSETS.items():
        config[project] = {}
        for label, path in files.items():
            file_id = upload_file_cached(str(path))
            config[project][label] = file_id
            print(f"Uploaded {path} → {file_id}")
    
    CONFIG_PATH.write_text(json.dumps(config, indent=2))
    print(f"\n✅ Asset file IDs saved to {CONFIG_PATH}")

if __name__ == "__main__":
    populate_config()


