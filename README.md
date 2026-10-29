# election206 – הצבעה לפי שעות, בחירות 2026

דשבורד שמראה מתי הצביעו בכל קלפי, יישוב, גוש ומפלגה.

- **הדשבורד:** `docs/index.html` (אפשר לפתוח ישירות בדפדפן, או להפעיל GitHub Pages מהתיקייה `docs`).
- **השוואה ל־2022:** `docs/compare.html` – שינויים בגושים ובמפלגות לפי יישוב, עם מבחנים סטטיסטיים.
- **הצבעה לפי גיל:** `docs/age.html` – הקשר בין הרכב הגילאים ביישוב (מרשם האוכלוסין 2026) לבין ההצבעה, עם מתאמים ורגרסיה.
- **עיבוד הנתונים:** `python3 scripts/build_data.py` – קורא את קובצי ההצבעה (`voter_turnout_*.xlsx`, `voter_turnout_22.Csv`) ואת התוצאות (`expb.csv`, `expc.csv`) ומייצר את `docs/data.js`. צריך `pandas` ו־`openpyxl`.
  `python3 scripts/build_compare.py` – קורא את `expc_2022.csv` ו־`expc.csv` ומייצר את `docs/compare_data.js`.
  `python3 scripts/build_age.py` – קורא את `israeli_citizens_age_city.csv` ואת התוצאות ומייצר את `docs/age_data.js` (להריץ אחרי `build_data.py`).

אופן החישוב מוסבר בדשבורד עצמו, בחלק "איך זה מחושב".
