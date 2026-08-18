from pathlib import Path
import json
from .models import Pokemon, Box
from .storage import load, save, backup, import_ppk, raw_to_pokemon

class Service:
    def __init__(self):
        self.lib = load()

    def add_box(self, name):
        self.lib.boxes.append(Box(name=name or f"Box {len(self.lib.boxes)+1}"))
        save(self.lib)

    def add_pokemon(self, p, box=0, slot=None):
        b = self.lib.boxes[box]
        if slot is None:
            try: slot = b.slots.index(None)
            except ValueError: raise ValueError("Box voll")
        if not 0 <= slot < 30: raise ValueError("Slot außerhalb 0..29")
        self.lib.pokemon[p.id] = p
        b.slots[slot] = p.id
        save(self.lib)

    def delete_pokemon(self, pid):
        self.lib.pokemon.pop(pid, None)
        for b in self.lib.boxes:
            b.slots = [None if x == pid else x for x in b.slots]
        save(self.lib)

    def import_path(self, p):
        p = Path(p)
        if p.name.lower().endswith(".ppk.json"):
            return import_ppk(self.lib, p.read_bytes())
        self.add_pokemon(raw_to_pokemon(p.suffix, p.read_bytes()))
        return 1

    def backup(self):
        return backup(self.lib)
