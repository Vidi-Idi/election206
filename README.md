# election206 – הצבעה לפי שעות, בחירות 2026

דשבורד שמראה מתי הצביעו בכל קלפי, יישוב, גוש ומפלגה.

- **הדשבורד:** `docs/index.html` (אפשר לפתוח ישירות בדפדפן, או להפעיל GitHub Pages מהתיקייה `docs`).
- **השוואה ל־2022:** `docs/compare.html` – שינויים בגושים ובמפלגות לפי יישוב, עם מבחנים סטטיסטיים.
- **עיבוד הנתונים:** `python3 scripts/build_data.py` – קורא את קובצי ההצבעה (`voter_turnout_*.xlsx`, `voter_turnout_22.Csv`) ואת התוצאות (`expb.csv`, `expc.csv`) ומייצר את `docs/data.js`. צריך `pandas` ו־`openpyxl`.
  `python3 scripts/build_compare.py` – קורא את `expc_2022.csv` ו־`expc.csv` ומייצר את `docs/compare_data.js`.

אופן החישוב מוסבר בדשבורד עצמו, בחלק "איך זה מחושב".
