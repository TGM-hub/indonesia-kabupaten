"""Build index.html (self-contained) from src/template.html + data/.

    python build.py

Inputs : data/kabupaten.csv (curated), data/shapes.json, data/provinces.json (tools/fetch_sources.py)
Output : index.html (no external request at runtime)
Python 3 standard library only.
"""
import csv, json, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
S = 1000            # 1 unit = 0.001 degree
LON0, LAT0 = 94.9, 6.2
ISLANDS = ["Sumatra", "Java", "Bali & Nusa Tenggara", "Kalimantan", "Sulawesi", "Maluku", "Papua"]
ISLANDS_FR = {"Sumatra": "Sumatra", "Java": "Java", "Bali & Nusa Tenggara": "Bali et Nusa Tenggara",
              "Kalimantan": "Kalimantan", "Sulawesi": "Sulawesi", "Maluku": "Moluques", "Papua": "Papouasie"}


def proj(lon, lat):
    return round((lon - LON0) * S), round((LAT0 - lat) * S)


def path_and_bbox(polys):
    out, xs, ys = [], [], []
    for poly in polys:
        for ring in poly:
            pts = [proj(*p) for p in ring]
            if pts[0] == pts[-1]:
                pts = pts[:-1]
            if len(pts) < 3:
                continue
            x, y = pts[0]
            seg = [f"M{x} {y}l"]
            px, py = x, y
            for (x, y) in pts[1:]:
                dx, dy = x - px, y - py
                if dx or dy:
                    seg.append(f"{dx} {dy} ".replace(" -", "-"))
                px, py = x, y
            out.append("".join(seg).rstrip() + "z")
            xs += [p[0] for p in pts]
            ys += [p[1] for p in pts]
    return "".join(out), [min(xs), min(ys), max(xs), max(ys)]


def main():
    shapes = json.load(open(os.path.join(ROOT, "data", "shapes.json")))
    provs = json.load(open(os.path.join(ROOT, "data", "provinces.json")))
    units, errors = [], []
    prov_meta = {}
    with open(os.path.join(ROOT, "data", "kabupaten.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            c = r["code"]
            if c not in shapes:
                errors.append(f"{c}: no shape")
                continue
            if r["type"] not in ("kab", "kota"):
                errors.append(f"{c}: bad type {r['type']}")
            if r["island"] not in ISLANDS:
                errors.append(f"{c}: unknown island {r['island']}")
            d, b = path_and_bbox(shapes[c]["poly"])
            units.append({"c": c, "t": r["type"], "n": r["name"], "p": r["province_code"],
                          "cap": r["capital"], "pl": r["plate"],
                          "ph": [x for x in r["phone"].split(";") if x], "d": d, "b": b,
                          "pt": list(proj(*shapes[c]["pt"]))})
            prov_meta.setdefault(r["province_code"], {"n": r["province"], "i": r["island"]})
    if len(units) != 514:
        errors.append(f"expected 514 units, got {len(units)}")
    if errors:
        sys.exit("ERRORS:\n" + "\n".join(errors))
    # kota drawn last so enclaves sit on top of their surrounding kabupaten
    units.sort(key=lambda u: (u["t"] == "kota", u["c"]))
    P = {}
    for code, polys in provs.items():
        d, b = path_and_bbox(polys)
        P[code] = dict(prov_meta[code], d=d, b=b)
    allb = [min(u["b"][0] for u in units), min(u["b"][1] for u in units),
            max(u["b"][2] for u in units), max(u["b"][3] for u in units)]
    data = {"units": units, "provs": P, "islands": [[i, ISLANDS_FR[i]] for i in ISLANDS], "bbox": allb}
    tpl = open(os.path.join(ROOT, "src", "template.html"), encoding="utf-8").read()
    html = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    out = os.path.join(ROOT, "index.html")
    open(out, "w", encoding="utf-8", newline="\n").write(html)
    missing_phone = [u["n"] for u in units if not u["ph"]]
    print(f"index.html: {len(units)} units, {len(P)} provinces, {os.path.getsize(out) / 1e6:.2f} MB")
    print(f"{len(missing_phone)} units without phone code")


if __name__ == "__main__":
    main()
