"""Build docs/age_data.js: 2026 population by age group per city, joined with election results.

Inputs (repo root): israeli_citizens_age_city.csv (population registry, 2026),
expc.csv (2026 results by city), expc_2022.csv (2022 results by city), and
docs/data.js (built by build_data.py) for each city's hourly voting pace.

Run after build_data.py:  python3 scripts/build_age.py
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "age_data.js"

AGE_COLS = ["גיל_0_5", "גיל_6_18", "גיל_19_45", "גיל_46_55", "גיל_56_64", "גיל_65_פלוס"]

BLOC_2026 = {"coalition": ["מחל", "ג", "שס", "ט", "ב"], "opposition": ["דרך", "רק", "אמת", "ל"], "arab": ["ודם", "עם"]}
BLOC_2022 = {"coalition": ["מחל", "ג", "שס", "ט"], "opposition": ["כן", "פה", "אמת", "מרצ", "ל"], "arab": ["ום", "עם", "ד"]}


def results(path, blocs):
    d = pd.read_csv(ROOT / path, encoding="utf-8-sig")
    d = d[d["סמל ישוב"] != 9999].set_index("סמל ישוב")
    return {int(code): [int(r["בזב"]), int(r["מצביעים"]), int(r["כשרים"])] + [int(sum(r[c] for c in cols)) for cols in blocs.values()]
            for code, r in d.iterrows()}


def main():
    pop = pd.read_csv(ROOT / "israeli_citizens_age_city.csv", encoding="cp1255", skipinitialspace=True)
    pop.columns = [c.strip() for c in pop.columns]
    for c in ["שם_ישוב", "נפה"]:
        pop[c] = pop[c].astype(str).str.strip()
    pop = pop[pop["סמל_ישוב"] != 0]  # "not registered"

    r26, r22 = results("expc.csv", BLOC_2026), results("expc_2022.csv", BLOC_2022)

    # hourly pace per city from the ballot-box data: cumulative voters at 9,12,16,18,20 and final
    hourly = json.loads((ROOT / "docs" / "data.js").read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
    codes = [c for c, _ in hourly["cities"]]
    pace = {}
    for c_idx, _box, _bzb, final, cum, _imp, _valid, _votes in hourly["boxes"]:
        acc = pace.setdefault(codes[c_idx], [0] * 6)
        for i, v in enumerate(cum + [final]):
            acc[i] += v

    cities = []
    for _, r in pop.iterrows():
        code = int(r["סמל_ישוב"])
        if code not in r26:
            continue
        cities.append([code, r["שם_ישוב"], r["נפה"], [int(r[c]) for c in AGE_COLS], r26[code], r22.get(code), pace.get(code)])

    OUT.write_text("window.AGE_DATA = " + json.dumps(
        dict(groups=["0–5", "6–18", "19–45", "46–55", "56–64", "65+"], hours=hourly["meta"]["hours"], cities=cities),
        ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"{len(cities)} cities ({sum(1 for c in cities if c[5])} with 2022 results, "
          f"{sum(1 for c in cities if c[6])} with hourly data); wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} KB)")


if __name__ == "__main__":
    main()
