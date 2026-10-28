# election206 – הצבעה לפי שעות, בחירות 2026

דשבורד שמראה מתי הצביעו בכל קלפי, יישוב, גוש ומפלגה.

- **הדשבורד:** `docs/index.html` (אפשר לפתוח ישירות בדפדפן, או להפעיל GitHub Pages מהתיקייה `docs`).
- **עיבוד הנתונים:** `python3 scripts/build_data.py` – קורא את קובצי ההצבעה (`voter_turnout_*.xlsx`, `voter_turnout_22.Csv`) ואת התוצאות (`expb.csv`, `expc.csv`) ומייצר את `docs/data.js`. צריך `pandas` ו־`openpyxl`.

אופן החישוב מוסבר בדשבורד עצמו, בחלק "איך זה מחושב".
