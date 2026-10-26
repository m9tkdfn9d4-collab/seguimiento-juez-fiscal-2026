#!/usr/bin/env python3
import json, re, os

base = os.path.dirname(os.path.abspath(__file__))
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

aptos = []
for num, x in by_num.items():
    if x.get("estado") in ("apto", "20", ">=20"):
        p = people_by_num.get(num, {})
        nota2 = round(float(p["nota2"]), 2) if p.get("nota2") is not None else None
        nota3 = round(float(x["nota3"]), 2) if x.get("nota3") is not None else None
        suma = round(nota2 + nota3, 2) if (nota2 is not None and nota3 is not None) else None
        aptos.append({
            "num": num,
            "nombre": p.get("nombre") or x.get("nombre"),
            "trib": x.get("trib") or p.get("trib"),
            "nota2": nota2,
            "nota3": nota3,
            "suma": suma,
            "fecha": x.get("fecha")
        })

aptos.sort(key=lambda r: (r["trib"], -(r["suma"] or 0), r["num"]))

with open(os.path.join(base, "aptos.json"), "w", encoding="utf-8") as f:
    json.dump(aptos, f, ensure_ascii=False, indent=2)

print(f"aptos.json updated with {len(aptos)} aptos")
