# Indonesia Kabupaten

GeoGuessr trainer for the 514 second-level divisions of Indonesia (416 *kabupaten* + 98 *kota*), grouped in the 38 current provinces.

Live: https://tgm-hub.github.io/indonesia-kabupaten/ (UI in French)

## Modes

| Mode | Question | Answer |
|---|---|---|
| Nom → carte | `Kab. Sleman` | click the unit |
| Province d'abord | `Kab. Sleman` | click the province, the map zooms in, then click the unit |
| Plaque → zone | `AB` | click any unit using that plate prefix |
| Indicatif → zone | `0274` | click any unit using that area code |
| Explorer | – | hover for names, click for the card |

After each answer a card shows province, capital (*ibu kota*), plate prefix and area code.
Filter by island or province, include/exclude *kota*, series of 10/20/all.
Answers are stored in the browser (`localStorage`): stats per island, most missed items, "Revoir mes erreurs" replays every item whose last answer was wrong.

## Files

```
index.html              built app, self-contained (no network at runtime)
build.py                data/ + src/template.html -> index.html (stdlib only)
src/template.html       UI (HTML/CSS/JS)
data/kabupaten.csv      curated table: code, type, name, province, island, capital, plate, phone
data/shapes.json        simplified polygons + label point per unit (generated)
data/provinces.json     dissolved province outlines (generated)
tools/fetch_sources.py  regenerates shapes/provinces from geoBoundaries (needs Node: npx mapshaper)
publish.ps1 / .cmd      build, preview, confirm, commit, push (creates the repo and Pages on first run)
```

Edit `data/kabupaten.csv`, then `python build.py`. Several units share a phone code or a plate prefix; `phone` holds one or more codes separated by `;`.

## Sources and licences

- Boundaries: [geoBoundaries](https://www.geoboundaries.org) gbOpen IDN ADM2 (BPS, WFP, OCHA ROAP), CC BY 3.0 IGO. Names matched to current codes; old names mapped (Toba Samosir → Toba, Mamuju Utara → Pasangkayu, Maluku Tenggara Barat → Kepulauan Tanimbar).
- Codes, names, capitals, 38 provinces: [cahyadsn/wilayah](https://github.com/cahyadsn/wilayah) (MIT), Kepmendagri No 300.2.2-2430/2025.
- Plate prefixes: Wikipedia, *Vehicle registration plates of Indonesia* (CC BY-SA), residency-level splits for Java, North/South Sulawesi, NTB, NTT and North Sumatra.
- Area codes: Wikipedia, *Daftar kode telepon di Indonesia* and *Telephone numbers in Indonesia* (CC BY-SA), completed from town-level lists for Maluku and Papua. 35 units have no reliable code yet (empty `phone` column): they are shown as "non renseigné" and skipped by the area-code mode.
