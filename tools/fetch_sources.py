"""One-off: regenerate data/shapes.json and data/provinces.json.

Geometry source: geoBoundaries gbOpen IDN ADM2 (simplified), CC BY 3.0 IGO
  (BPS - Statistics Indonesia, WFP, OCHA ROAP). 519 features = 514 kabupaten/kota + 5 lakes/forest.
  https://www.geoboundaries.org  -  github.com/wmgeolab/geoBoundaries
Features are matched by name to the codes in data/kabupaten.csv (Kepmendagri 2025 codes, 38 provinces).

Requires: Python 3, Node.js (npx mapshaper). Run from the repo root:
    python tools/fetch_sources.py
data/kabupaten.csv is NOT touched (names, capitals, plates and phone codes are curated by hand).
"""
import csv, json, os, re, subprocess, sys, tempfile, urllib.request

URL = ("https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/"
       "gbOpen/IDN/ADM2/geoBoundaries-IDN-ADM2_simplified.geojson")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SIMPLIFY = "30%"

NON_UNITS = {"Danau", "Danau Toba", "Hutan", "Waduk Cirata", "Wadung Kedungombo"}
# geoBoundaries name -> name used in kabupaten.csv (old names, spelling variants)
ALIAS = {
    "Kota Baru": "Kotabaru",  # Kabupaten Kotabaru (63.02), not a kota
    "Toba Samosir": "Toba", "Mamuju Utara": "Pasangkayu", "Maluku Tenggara Barat": "Kepulauan Tanimbar",
    "Kota Banjar Baru": "Kota Banjarbaru", "Banyu Asin": "Banyuasin", "Labuhan Batu": "Labuhanbatu",
    "Labuhan Batu Selatan": "Labuhanbatu Selatan", "Labuhan Batu Utara": "Labuhanbatu Utara",
    "Karang Asem": "Karangasem", "Gunung Kidul": "Gunungkidul", "Tulangbawang": "Tulang Bawang",
    "Batang Hari": "Batanghari", "Kota Sawah Lunto": "Kota Sawahlunto", "Kota Tanjung Balai": "Kota Tanjungbalai",
    "Kota Pematang Siantar": "Kota Pematangsiantar", "Kota Pangkal Pinang": "Kota Pangkalpinang",
    "Kota Tanjung Pinang": "Kota Tanjungpinang", "Mahakam Hulu": "Mahakam Ulu",
    "Siau Tagulandang Biaro": "Kepulauan Siau Tagulandang Biaro", "Toli-Toli": "Tolitoli",
}


def norm(s):
    s = s.lower().replace(" dan ", " ").replace("-", " ")
    return re.sub(r"[^a-z]", "", s)


def main():
    units = {}
    with open(os.path.join(DATA, "kabupaten.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            units[norm(("Kota " if r["type"] == "kota" else "") + r["name"])] = r["code"]
    tmp = tempfile.mkdtemp()
    src = os.path.join(tmp, "gb.geojson")
    print("download", URL)
    urllib.request.urlretrieve(URL, src)
    gb = json.load(open(src, encoding="utf-8"))
    feats, unmatched, seen = [], [], set()
    for f in gb["features"]:
        name = f["properties"]["shapeName"]
        if name in NON_UNITS:
            continue
        code = units.get(norm(ALIAS.get(name, name)))
        if not code:
            unmatched.append(name)
            continue
        if code in seen:
            sys.exit(f"duplicate match for {code} ({name})")
        seen.add(code)
        feats.append({"type": "Feature", "properties": {"kode": code, "prov": code[:2]}, "geometry": f["geometry"]})
    missing = set(units.values()) - seen
    if unmatched or missing:
        sys.exit(f"unmatched geoBoundaries names: {unmatched}\ncodes without geometry: {sorted(missing)}")
    print(len(feats), "kabupaten/kota matched")
    raw = os.path.join(tmp, "raw.geojson")
    json.dump({"type": "FeatureCollection", "features": feats}, open(raw, "w"))
    kab, prov, pts = (os.path.join(tmp, n) for n in ("kab.json", "prov.json", "pts.json"))
    ms = ["npx.cmd" if os.name == "nt" else "npx", "--yes", "mapshaper"]
    subprocess.run(ms + ["-i", raw, "-simplify", SIMPLIFY, "keep-shapes",
                         "-o", "precision=0.001", "format=geojson", kab], check=True)
    subprocess.run(ms + ["-i", kab, "-dissolve", "prov", "-o", "precision=0.001", "format=geojson", prov], check=True)
    subprocess.run(ms + ["-i", kab, "-points", "inner", "-o", "precision=0.001", "format=geojson", pts], check=True)

    def poly_list(g):
        if not g:
            return []
        return [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]

    point = {f["properties"]["kode"]: f["geometry"]["coordinates"] for f in json.load(open(pts))["features"]}
    shapes = {f["properties"]["kode"]: {"poly": poly_list(f["geometry"]), "pt": point[f["properties"]["kode"]]}
              for f in json.load(open(kab))["features"]}
    provs = {f["properties"]["prov"]: poly_list(f["geometry"]) for f in json.load(open(prov))["features"]}
    json.dump(shapes, open(os.path.join(DATA, "shapes.json"), "w"), separators=(",", ":"))
    json.dump(provs, open(os.path.join(DATA, "provinces.json"), "w"), separators=(",", ":"))
    print(f"wrote data/shapes.json ({len(shapes)}) and data/provinces.json ({len(provs)})")


if __name__ == "__main__":
    main()
