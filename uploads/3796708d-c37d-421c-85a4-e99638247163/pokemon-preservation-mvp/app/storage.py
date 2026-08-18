import base64, json, os
from datetime import datetime, timezone
from pathlib import Path
from .models import Library, Pokemon

ROOT = Path(__file__).resolve().parents[1]

def data_dir():
    p = Path(os.environ.get("PPN_DATA_DIR", ROOT / "data"))
    (p / "backups").mkdir(parents=True, exist_ok=True)
    return p

def path():
    return data_dir() / "library.json"

def save(lib):
    tmp = path().with_suffix(".tmp")
    tmp.write_text(json.dumps(lib.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path())

def load():
    if not path().exists():
        lib = Library.empty()
        save(lib)
        return lib
    return Library.from_dict(json.loads(path().read_text(encoding="utf-8")))

def backup(lib):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = data_dir() / "backups" / f"library-{stamp}.json"
    out.write_text(json.dumps(lib.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return out

def import_ppk(lib, raw):
    other = Library.from_dict(json.loads(raw.decode("utf-8")))
    count = 0
    for p in other.pokemon.values():
        while p.id in lib.pokemon:
            p.id += "-imported"
        lib.pokemon[p.id] = p
        count += 1
    save(lib)
    return count

def raw_to_pokemon(ext, raw):
    ext = ext.lower()
    if not ext.startswith("."):
        ext = "." + ext
    gens = {f".pk{i}": i for i in range(1, 10)}
    return Pokemon(
        generation=gens.get(ext, 9),
        payload={"encoding":"base64", "extension":ext,
                 "data":base64.b64encode(raw).decode("ascii")}
    )
