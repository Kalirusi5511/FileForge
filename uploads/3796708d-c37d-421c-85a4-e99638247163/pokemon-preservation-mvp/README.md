# Pokémon Preservation MVP

Lokales, Nintendo-unabhängiges MVP für die langfristige Verwaltung einer Pokémon-Sammlung.

## Funktionen
- 30-Slot-Boxen
- Pokémon lokal speichern/verwalten
- Weboberfläche auf `127.0.0.1:8765`
- neutrales JSON-Bibliotheksformat
- Raw-Import für `.pk1` bis `.pk9` ohne Byteverlust
- Bibliotheks-Download
- Backups
- tests

## Start
Python 3.11+:
```bash
python -m app
```
Dann `http://127.0.0.1:8765` öffnen.

Dieses MVP interpretiert `.pk*`-Dateien noch nicht vollständig; ihre Rohdaten werden verlustfrei als Base64 gespeichert. Das Datenmodell ist absichtlich erweiterbar.

## Daten
Standard: `data/library.json`
Backups: `data/backups/`
