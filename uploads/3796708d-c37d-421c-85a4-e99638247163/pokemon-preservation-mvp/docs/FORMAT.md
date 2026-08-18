# PPN Neutral Format v1

Die Bibliothek ist JSON mit `schema_version: 1`.

Ein Pokémon besitzt eine stabile UUID und kann zusätzlich eine unveränderte Raw-Payload tragen:
```json
{
  "id": "uuid",
  "species": "Unknown",
  "generation": 9,
  "payload": {
    "encoding": "base64",
    "extension": ".pk9",
    "data": "..."
  }
}
```

Ziel: lokale, vollständige Exportierbarkeit und spätere Parser-Erweiterungen ohne Verlust unbekannter Bytes.
