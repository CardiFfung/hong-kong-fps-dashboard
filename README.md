# Hong Kong FPS Trends Dashboard

Explore monthly HKD payment activity in Hong Kong's Faster Payment System using official Hong Kong Monetary Authority (HKMA) data.

**[Open the live dashboard](https://hong-kong-fps-dashboard.streamlit.app/)**

![Dashboard showing monthly payment trends and the latest metrics](docs/dashboard.png)

## Overview

The dashboard brings transaction volume, value, payment mix, and average transaction size into one view for reviewing payment activity. It covers September 2018 to August 2026 in the included snapshot.

The interface is in Traditional Chinese for local readers, with amounts displayed in HKD. This README documents the project in English.

### Features

- Monthly volume and value trends, with optional 12-month moving averages.
- Latest complete-month metrics with absolute and percentage changes against the previous month and the same month a year earlier.
- Real-time versus batch payment shares, plus a breakdown of real-time credit transfers.
- Category and date filters, average transaction values, and CSV downloads.
- On-demand API updates with validation, archived source responses, and a dated fallback when an update fails.

## Analysis Highlights

Based on August 2026 data, retrieved on 17 September 2026:

| Observation | Interpretation |
|---|---|
| Volume rose **14.93% year over year**, while value rose **9.09%**. Average transaction value fell **5.08%** to **HK$9,762.61**. | Higher payment activity did not translate into an equally large increase in value. Tracking both counts and average transaction size makes this distinction visible. |
| Batch payments represented **11.87% of transactions** but **30.79% of value**. Their average was **HK$25,330.69**, versus **HK$7,666.29** for real-time payments—about **3.30 times** as much. | A volume-only view understates the contribution of batch payments to total value. Payment-mix comparisons should include both measures. |
| Total volume fell **2.03% month over month** but remained **14.93% above August 2025**. | The monthly decline and annual growth describe different comparison periods. One weaker month alone does not establish a reversal in the longer-term trend. |

These figures describe aggregate payment patterns; the data do not identify the reasons behind them.

## Tech Stack

**Python · pandas · Streamlit · Plotly · pytest · GitHub Actions**

Streamlit keeps the data pipeline and interactive interface in one Python project. Plotly provides hover details and chart interactions, while pandas handles monthly alignment and calculations.

```text
app.py                      Dashboard interface and charts
src/pipeline.py             Retrieval, validation, and derived metrics
data/raw/<snapshot>/        Original API responses and request URLs
data/processed/<snapshot>/  Processed CSV and snapshot metadata
data/current.json           Active snapshot pointer
tests/                      Pipeline, interface, and browser checks
docs/                       Data definitions, validation, and deployment
```

## Run Locally

Use **Python 3.13**.

```bash
git clone https://github.com/CardiFfung/hong-kong-fps-dashboard.git
cd hong-kong-fps-dashboard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open `http://localhost:8501`. The included snapshot allows the dashboard to start without an API request.

On Windows, create the environment with `py -3.13 -m venv .venv` and activate it with `.venv\Scripts\activate.bat` in Command Prompt or `.venv\Scripts\Activate.ps1` in PowerShell.

To refresh the data, use the sidebar update button or run:

```bash
python -m src.pipeline
```

Updates retrieve both datasets and activate a new snapshot after validation. Headline metrics always use the latest complete month; chart filters control the displayed period and CSV export. Updates are manual.

For hosting configuration, see the [deployment guide](docs/DEPLOYMENT.md).

## Data Sources and Methodology

- [HKMA HKD FPS transaction volume](https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/banking/ch-statistics-turnover-fps-hkd-payment-vol): Number of transactions.
- [HKMA HKD FPS transaction value](https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/banking/ch-statistics-turnover-fps-hkd-payment-val): Amounts in **HKD thousands**.

The pipeline retrieves all pages and merges the datasets one-to-one on `end_of_month`. It checks duplicate and missing months, invalid values, and component-to-total relationships. Raw fields retain `_volume` and `_value_hkd_thousand` suffixes.

```text
Average transaction value (HKD) = value (HKD thousands) × 1,000 ÷ volume
```

Calculations use the same month and payment category. Growth rates require the exact comparison month and a positive baseline. Missing values remain blank.

Real-time payments plus batch payments equal total payments. The personal-account transfer breakdown uses **all real-time credit transfers (`rtctp`)** as its denominator, including other credit transfers. Totals and their components are not added together.

The dashboard displays volume in units of 10,000 transactions and value in units of HK$100 million. See the [data audit and field definitions](docs/DATA_AUDIT.md) for source documentation and reconciliation details.

## Validation

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover pagination, monthly alignment, unit conversion, zero denominators, reconciliation, snapshot handling, and dashboard states. Independent calculations and browser checks are documented in the [validation report](docs/QA_REPORT.md). Current automated results are available in [GitHub Actions](https://github.com/CardiFfung/hong-kong-fps-dashboard/actions/workflows/tests.yml).

## Limitations

- **Aggregate HKD data:** Transaction counts are not user counts, and average values are not medians. The dataset does not reveal individual behaviour, transaction purposes, or causes of changes.
- **Monthly comparability:** September 2018 is a partial launch month and is excluded from growth comparisons and moving averages. Month length and seasonality may affect subsequent totals; no seasonal adjustment is applied.
- **Snapshot revisions:** HKMA may revise historical figures. Each snapshot records its retrieval time and sources; update failures retain the previous dated snapshot.

Data source: HKMA. This project is independently maintained and is not an official HKMA product. Developed with AI assistance.
