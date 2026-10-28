"""Build docs/compare_data.js: city results 2022 vs 2026, mapped to the same parties and blocs.

Inputs (repo root): expc_2022.csv, expc.csv (2026 results by city),
voter_turnout_22.Csv (2026 registered voters in every ballot box, including
boxes missing from the 2026 results file).

The 2022 "external envelopes" row (city code 9999) has no city, and the 2026
files have no such row, so it is left out of both years.

Run:  python3 scripts/build_compare.py
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "compare_data.js"

# (name, bloc, 2022 columns, 2026 columns)
PARTIES = [
    ("הליכוד", "coalition", ["מחל"], ["מחל"]),
    ("יהדות התורה", "coalition", ["ג"], ["ג"]),
    ("ש״ס", "coalition", ["שס"], ["שס"]),
    ("הציונות הדתית + עוצמה יהודית", "coalition", ["ט"], ["ט", "ב"]),
    ("המחנה הממלכתי → ישר", "opposition", ["כן"], ["דרך"]),
    ("יש עתיד → ביחד", "opposition", ["פה"], ["רק"]),
    ("העבודה + מרצ → הדמוקרטים", "opposition", ["אמת", "מרצ"], ["אמת"]),
    ("ישראל ביתנו", "opposition", ["ל"], ["ל"]),
    ("חד״ש-תע״ל → רשימה משותפת", "arab", ["ום"], ["ודם"]),
    ("רע״ם", "arab", ["עם"], ["עם"]),
    ("בל״ד (לא רצה ב־2026)", "arab", ["ד"], []),
]


def load(path, year_idx):
    d = pd.read_csv(ROOT / path, encoding="utf-8-sig")
    d = d[d["סמל ישוב"] != 9999].set_index("סמל ישוב")
    out = {}
    for code, r in d.iterrows():
        parties = [int(sum(r[c] for c in (cols22 if year_idx == 0 else cols26))) for _, _, cols22, cols26 in PARTIES]
        out[int(code)] = dict(name=str(r["שם ישוב"]).strip(), bzb=int(r["בזב"]), voters=int(r["מצביעים"]),
                              invalid=int(r["פסולים"]), valid=int(r["כשרים"]), parties=parties)
    return out


def main():
    y22, y26 = load("expc_2022.csv", 0), load("expc.csv", 1)

    # Registered voters in all 2026 boxes, to measure how much of each city the 2026 results cover
    t = pd.read_csv(ROOT / "voter_turnout_22.Csv", encoding="cp1255")
    t = t[t["סמל יישוב"] < 99999]
    bzb_all26 = t.groupby("סמל יישוב")['בז"ב'].sum().to_dict()

    def rec(y):
        return [y["bzb"], y["voters"], y["invalid"], y["valid"], y["parties"]] if y else None

    cities = []
    for code in sorted(set(y22) | set(y26), key=lambda c: (y26.get(c) or y22.get(c))["name"]):
        a, b = y22.get(code), y26.get(code)
        name = (b or a)["name"]
        full = int(bzb_all26.get(code, b["bzb"] if b else 0))
        cities.append([code, name, rec(a), rec(b), full])

    data = dict(parties=[dict(name=n, bloc=bl, c22=c22, c26=c26) for n, bl, c22, c26 in PARTIES], cities=cities)
    OUT.write_text("window.COMPARE_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n",
                   encoding="utf-8")
    both = sum(1 for c in cities if c[2] and c[3])
    print(f"{len(cities)} cities, {both} in both years; wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} KB)")


if __name__ == "__main__":
    main()
