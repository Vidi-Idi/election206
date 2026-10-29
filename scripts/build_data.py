"""Build docs/data.js for the turnout dashboard.

Inputs (repo root):
  voter_turnout_{09,12,16,18,20}.xlsx, voter_turnout_22.Csv  - hourly turnout per ballot box
  expb.csv - results per ballot box, expc.csv - results per city (used as a check)

Ballot boxes are joined on (city code, ברזל).

Each hourly report carries its real update time (a box listed in the 18:00 file
may have last reported at 12:11), so every report is treated as a point
(update time, cumulative voters). The points, plus 0 at 07:00 and the official
final count at 22:00, are interpolated to the nominal hours. When a box has no
report near an hour, its share of final voters at that hour is taken from the
median of real reports in the same city (or nationwide), kept between the
box's own earlier and later reports, and flagged as imputed.

Run:  python3 scripts/build_data.py
"""

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "data.js"  # a script, not JSON, so index.html also works when opened from disk

HOURS = [9, 12, 16, 18, 20]
OPEN, CLOSE = 7 * 60, 22 * 60
NEAR = 75  # minutes: a report this close to an hour counts as a real reading

# Party columns in the results files, grouped by bloc. Parties not listed are ignored.
PARTIES = [
    ("מחל", "הליכוד", "coalition"),
    ("ג", "יהדות התורה", "coalition"),
    ("ב", "עוצמה יהודית", "coalition"),
    ("שס", "ש״ס", "coalition"),
    ("ט", "הציונות הדתית", "coalition"),
    ("דרך", "ישר", "opposition"),
    ("רק", "ביחד", "opposition"),
    ("אמת", "הדמוקרטים", "opposition"),
    ("ל", "ישראל ביתנו", "opposition"),
    ("ודם", "רשימה משותפת", "arab"),
    ("עם", "רע״ם", "arab"),
]


def to_minutes(v):
    if isinstance(v, dt.time):
        return v.hour * 60 + v.minute
    if isinstance(v, str) and ":" in v:
        h, m = v.split(":")[:2]
        return int(h) * 60 + int(m)
    return None


def read_turnout(hour):
    if hour == 22:
        d = pd.read_csv(ROOT / "voter_turnout_22.Csv", encoding="cp1255", header=None, skiprows=1)
    else:
        d = pd.read_excel(ROOT / f"voter_turnout_{hour:02d}.xlsx", header=None)
    d = d.iloc[:, :8]
    d.columns = ["city", "name", "box", "barzel", "bzb", "voters", "pct", "time"]
    d["city"] = pd.to_numeric(d["city"], errors="coerce")
    d = d[d["city"].notna() & (d["city"] < 99999)].copy()  # drop header/footer rows and the national total
    for c in ["city", "barzel", "bzb", "voters"]:
        d[c] = d[c].astype(int)
    d["box"] = d["box"].astype(float)
    d["t"] = d["time"].map(to_minutes)
    return d.set_index(["city", "barzel"])


def main():
    res = pd.read_csv(ROOT / "expb.csv", encoding="utf-8-sig")
    res = res.dropna(subset=["סמל ישוב"])
    res["סמל ישוב"] = res["סמל ישוב"].astype(int)
    # external envelopes (city code 9999) have no city and no hourly reports
    envelopes = res[res["סמל ישוב"] == 9999]
    res = res[res["סמל ישוב"] != 9999]
    res = res.set_index(["סמל ישוב", "ברזל"])

    turn = {h: read_turnout(h) for h in HOURS + [22]}

    # Every box that appears anywhere
    keys = sorted(set(res.index) | set(turn[22].index) | set().union(*(set(turn[h].index) for h in HOURS)))

    city_names = {}
    for (c, _), name in res["שם ישוב"].items():
        city_names[c] = name.strip()
    for (c, _), name in turn[22]["name"].items():  # the 22:00 CSV decodes cleanly; xlsx names are garbled
        city_names.setdefault(c, str(name).strip())

    boxes = []
    for key in keys:
        c, barzel = key
        has_res = key in res.index
        r = res.loc[key] if has_res else None
        if has_res:
            bzb, final = int(r["בזב"]), int(r["מצביעים"])
            box_no = float(r["קלפי"])
        else:
            src = next((turn[h].loc[key] for h in [22] + HOURS[::-1] if key in turn[h].index), None)
            if src is None or key not in turn[22].index:
                continue  # no final count at all
            bzb, final, box_no = int(src["bzb"]), int(turn[22].loc[key, "voters"]), float(src["box"])
        if final <= 0:
            continue
        pts = {}
        for h in HOURS:
            if key in turn[h].index:
                row = turn[h].loc[key]
                t = row["t"] if row["t"] is not None and not pd.isna(row["t"]) else h * 60
                t = min(max(t, OPEN + 1), CLOSE - 1)
                pts[t] = min(int(row["voters"]), final)
        boxes.append(dict(city=c, barzel=barzel, box=box_no, bzb=bzb, final=final, has_res=has_res, pts=pts, r=r))

    # Interpolate real readings to nominal hours
    for b in boxes:
        ts = sorted(b["pts"])
        vs = [b["pts"][t] for t in ts]
        # cumulative counts can't decrease: an earlier reading above a later one is capped by it
        for i in range(len(vs) - 2, -1, -1):
            vs[i] = min(vs[i], vs[i + 1])
        xs = [OPEN] + ts + [CLOSE]
        ys = [0] + vs + [b["final"]]
        b["xs"], b["ys"] = xs, ys
        b["real"] = [any(abs(t - h * 60) <= NEAR for t in ts) for h in HOURS]
        b["share"] = [np.interp(h * 60, xs, ys) / b["final"] if b["real"][i] else None for i, h in enumerate(HOURS)]

    # Medians of real shares, by city and nationwide, for imputation
    nat = [np.median([b["share"][i] for b in boxes if b["real"][i]]) for i in range(len(HOURS))]
    by_city = {}
    for b in boxes:
        by_city.setdefault(b["city"], []).append(b)
    city_med = {}
    for c, bs in by_city.items():
        meds = []
        for i in range(len(HOURS)):
            vals = [b["share"][i] for b in bs if b["real"][i]]
            meds.append(float(np.median(vals)) if len(vals) >= 5 else nat[i])
        city_med[c] = meds

    n_imputed = [0] * len(HOURS)
    for b in boxes:
        shares = []
        for i, h in enumerate(HOURS):
            if b["real"][i]:
                s = b["share"][i]
            else:
                n_imputed[i] += 1
                s = city_med[b["city"]][i]
                # stay between this box's own readings before and after the hour
                lo = max([y for x, y in zip(b["xs"], b["ys"]) if x <= h * 60], default=0) / b["final"]
                hi = min([y for x, y in zip(b["xs"], b["ys"]) if x >= h * 60], default=b["final"]) / b["final"]
                s = min(max(s, lo), hi)
            shares.append(s)
        for i in range(1, len(shares)):  # keep monotone after imputation
            shares[i] = max(shares[i], shares[i - 1])
        b["cum"] = [round(s * b["final"]) for s in shares]

    # Compact output
    cities = sorted(by_city, key=lambda c: city_names.get(c, ""))
    city_idx = {c: i for i, c in enumerate(cities)}
    rows = []
    for b in sorted(boxes, key=lambda b: (city_idx[b["city"]], b["box"])):
        imputed_mask = sum(1 << i for i, ok in enumerate(b["real"]) if not ok)
        if b["has_res"]:
            r = b["r"]
            votes = [int(r[col]) for col, _, _ in PARTIES]
            valid = int(r["כשרים"])
        else:
            votes, valid = None, None
        box_label = int(b["box"]) if float(b["box"]).is_integer() else b["box"]
        rows.append([city_idx[b["city"]], box_label, b["bzb"], b["final"], b["cum"], imputed_mask, valid, votes])

    # Sanity check against the city results file
    city_res = pd.read_csv(ROOT / "expc.csv", encoding="utf-8-sig")
    city_res = city_res[city_res["סמל ישוב"] != 9999].set_index("סמל ישוב")
    box_sum = res.groupby(level=0)["מצביעים"].sum()
    mismatched = int((city_res["מצביעים"] - box_sum.reindex(city_res.index).fillna(0)).ne(0).sum())

    meta = dict(
        hours=HOURS,
        parties=[dict(code=c, name=n, bloc=bl) for c, n, bl in PARTIES],
        boxes_total=len(rows),
        boxes_with_results=sum(1 for r in rows if r[7] is not None),
        boxes_without_results=sum(1 for r in rows if r[7] is None),
        boxes_without_hourly=sum(1 for b in boxes if not b["pts"]),
        envelope_voters=int(envelopes["מצביעים"].sum()),
        imputed_per_hour=n_imputed,
        city_file_mismatches=mismatched,
    )
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        "window.ELECTION_DATA = " + json.dumps(dict(meta=meta, cities=[[c, city_names.get(c, str(c))] for c in cities], boxes=rows),
                   ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
