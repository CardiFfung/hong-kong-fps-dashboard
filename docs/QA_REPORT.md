# Validation Report

Baseline validation: 17 September 2026. Local environment: macOS ARM64, Python 3.13.14. Dependency versions are recorded in `requirements-lock.txt` at the repository root.

## Coverage

| Check | Result |
|---|---|
| Official API retrieval | Both datasets returned 96 monthly records |
| Coverage | September 2018 to August 2026 |
| Duplicate or missing months | None |
| Null, non-numeric, or negative values | None found in the baseline snapshot |
| Component-to-total reconciliation | All three relationships passed for both datasets |
| Automated tests | 19 passed in baseline validation |
| Desktop browser | Five Plotly charts rendered in Chromium |
| Metric and category controls | Value and batch-payment selections worked without interface exceptions |
| Date filtering | January 2025 to August 2026 verified with Streamlit AppTest |
| CSV download | 96 rows for the full period; final monthly volume was 82,587,554 |
| Browser JavaScript errors | None observed |
| Mobile layout | Checked at 390 × 844; sidebar collapsed and headline metrics remained readable |
| Missing snapshot | Error displayed without metrics |
| Failed API refresh | Error displayed with the previous snapshot's date; active snapshot preserved |

## Independent Calculation Checks

Tests compare the original JSON values with calculations using `Decimal`.

For August 2026:

- HKD value: 806,269,783.54935 × 1,000 = **HK$806,269,783,549.35**.
- Average transaction value: HK$806,269,783,549.35 ÷ 82,587,554 = approximately **HK$9,762.61**.
- Volume MoM: **−1,712,519 transactions (−2.031456%)**.
- Volume YoY: **+10,725,876 transactions (+14.925724%)**.
- Value MoM: **−HK$51,083,680,510.91 (−5.958299%)**.
- Value YoY: **+HK$67,153,125,176.07 (+9.085592%)**.

A separate fixture checks that HKD 50,000 thousand across 10,000 transactions produces an average of HK$5,000. Zero transaction volume produces a missing average.

## Reproduce

From the repository root:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m src.pipeline --offline
```

For browser checks, start the app in one terminal:

```bash
python -m streamlit run app.py
```

Then run in another terminal using the same Python environment:

```bash
python -m playwright install chromium
python tests/browser_check.py
```

The browser script's expected row count and latest volume refer to the baseline snapshot. Update those assertions when deliberately replacing the dataset.

## Verification Scope

[GitHub Actions passed on Ubuntu with Python 3.13](https://github.com/CardiFfung/hong-kong-fps-dashboard/actions/runs/35129351241). Browser verification was performed locally in Chromium. Windows, Safari, and the hosted Streamlit application have not been tested in this baseline.

API failure states are tested with controlled exceptions. Raw responses are preserved, and snapshot activation occurs only after retrieval and validation complete.

Screenshots: `dashboard.png`, `dashboard-detail.png`, and `dashboard-mobile.png` in this directory.
