from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from uuid import uuid4

def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

@dataclass
class Pokemon:
    id: str = field(default_factory=lambda: str(uuid4()))
    nickname: str = ""
    species: str = "Unknown"
    generation: int = 9
    level: int = 1
    details: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    payload: dict | None = None
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)

@dataclass
class Box:
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Box 1"
    slots: list = field(default_factory=lambda: [None] * 30)

@dataclass
class Library:
    schema_version: int = 1
    library_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)
    boxes: list[Box] = field(default_factory=list)
    pokemon: dict = field(default_factory=dict)

    @classmethod
    def empty(cls):
        return cls(boxes=[Box()])

    def to_dict(self):
        return {
            "schema_version": self.schema_version,
            "library_id": self.library_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "boxes": [asdict(x) for x in self.boxes],
            "pokemon": [asdict(x) for x in self.pokemon.values()],
        }

    @classmethod
    def from_dict(cls, d):
        lib = cls(
            schema_version=int(d.get("schema_version", 1)),
            library_id=d.get("library_id", str(uuid4())),
            created_at=d.get("created_at", now()),
            updated_at=d.get("updated_at", now()),
            boxes=[Box(**x) for x in d.get("boxes", [])],
        )
        if not lib.boxes:
            lib.boxes = [Box()]
        for item in d.get("pokemon", []):
            lib.pokemon[item["id"]] = Pokemon(**item)
        return lib
