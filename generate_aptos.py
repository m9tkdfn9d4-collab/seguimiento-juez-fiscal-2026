#!/usr/bin/env python3
import json, re, os, urllib.request
from collections import defaultdict

base = os.path.dirname(os.path.abspath(__file__))
aptos_path = os.path.join(base, "aptos.json")

existing_carrera = {}
if os.path.exists(aptos_path):
    try:
        with open(aptos_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                if item.get("num") is not None and item.get("carrera") in ("juez", "fiscal"):
                    existing_carrera[int(item["num"])] = item["carrera"]
    except Exception:
        pass

try:
    req = urllib.request.Request("https://eleccionjudicatura.netlify.app/.netlify/functions/elecciones", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        data_remote = json.loads(resp.read().decode("utf-8"))
        for item in data_remote.get("items", []):
            if item.get("num") is not None and item.get("carrera") in ("juez", "fiscal"):
                existing_carrera[int(item["num"])] = item["carrera"]
except Exception:
    pass

with open(os.path.join(base, "index.html"), "r", encoding="utf-8") as f:
    html = f.read()

m_data = re.search(r"const DATA = (\{.*?\});\n", html)
data = json.loads(m_data.group(1))
people_by_num = {p["num"]: p for p in data["people"]}

m_notas = re.search(r"let NOTAS = \{updated:\"[^\"]*\", items:(\[.*?\])\};", html)
embedded_items = json.loads(m_notas.group(1))

with open(os.path.join(base, "notas.json"), "r", encoding="utf-8") as f:
    notas_file = json.load(f)

by_num = {x["num"]: x for x in embedded_items}
for x in notas_file.get("items", []):
    by_num[x["num"]] = x

by_trib = defaultdict(list)
for num, x in by_num.items():
    if x.get("estado") in ("apto", "20", ">=20"):
        p = people_by_num.get(num, {})
        nota2 = round(float(p["nota2"]), 2) if p.get("nota2") is not None else None
        nota3 = round(float(x["nota3"]), 2) if x.get("nota3") is not None else None
        suma = round(nota2 + nota3, 2) if (nota2 is not None and nota3 is not None) else None
        trib = x.get("trib") or p.get("trib")
        by_trib[trib].append({
            "num": num,
            "nombre": p.get("nombre") or x.get("nombre"),
            "trib": trib,
            "nota2": nota2,
            "nota3": nota3,
            "suma": suma,
            "fecha": x.get("fecha"),
            "carrera": existing_carrera.get(int(num), None)
        })

for t in by_trib:
    by_trib[t].sort(key=lambda r: (r["suma"] is None, -(r["suma"] or 0), r["nombre"]))

max_pos = max((len(v) for v in by_trib.values()), default=0)
aptos = []
for pos in range(max_pos):
    wave = [by_trib[t][pos] for t in sorted(by_trib.keys()) if pos < len(by_trib[t])]
    wave.sort(key=lambda r: (r["suma"] is None, -(r["suma"] or 0), r["trib"]))
    aptos.extend(wave)

with open(aptos_path, "w", encoding="utf-8") as f:
    json.dump(aptos, f, ensure_ascii=False, indent=2)

print(f"aptos.json updated with {len(aptos)} aptos in escalafon order")
for i, a in enumerate(aptos[:12], 1):
    print(f"#{i:2d}: T{a['trib']} | {a['nombre']} | suma={a['suma']} | {a['carrera']}")
