# Data Audit and Field Definitions

Baseline snapshot retrieved on 17 September 2026 at 00:59 HKT. This document records that snapshot; `data/current.json` identifies the active snapshot used by the dashboard.

## Official Sources

- [Volume field documentation](https://apidocs.hkma.gov.hk/documentation/market-data-and-statistics/monthly-statistical-bulletin/banking/ch-statistics-turnover-fps-hkd-payment-vol/)
- [Value field documentation](https://apidocs.hkma.gov.hk/documentation/market-data-and-statistics/monthly-statistical-bulletin/banking/ch-statistics-turnover-fps-hkd-payment-val/)
- [General API documentation](https://apidocs.hkma.gov.hk/documentation/)
- [Volume API](https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/banking/ch-statistics-turnover-fps-hkd-payment-vol)
- [Value API](https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/banking/ch-statistics-turnover-fps-hkd-payment-val)

## Response Format and Coverage

Both responses returned `header.success=true`, `err_code=0000`, and `result.datasize=96`. Records are stored as a list of objects in `result.records`.

Each dataset contains **96 months, from September 2018 to August 2026**. `end_of_month` is a `YYYY-MM` string. Volume is an integer count; value contains decimal amounts in **HKD thousands**.

The API defaults to 100 rows per page and permits up to 1,000. The pipeline requests `pagesize=1000` and advances `offset` whenever a full page is returned. The baseline fits in one page; tests cover full pages, an empty final page, and repeated-page detection. Records are requested in ascending month order and sorted again during processing.

## Source Fields

| Field | Definition |
|---|---|
| `end_of_month` | Reporting month |
| `total` | Total payments |
| `rt_payment` | Real-time payments |
| `bat_payment` | Batch payments |
| `rtctp` | Total real-time credit transfers |
| `rtddp` | Real-time direct debits |
| `rtctp_pp_payee_proxy_id` | Credit transfers initiated by personal accounts using payee proxy IDs |
| `rtctp_pp_payee_acc_no` | Credit transfers initiated by personal accounts using payee account numbers |
| `rtctp_other_payment` | Other real-time credit transfers |

After merging, source fields use `_volume` and `_value_hkd_thousand` suffixes. Derived HKD amounts use `_value_hkd`; averages use `_avg_hkd`.

## Reconciliation and Denominators

The pipeline checks these relationships for both volume and value:

```text
rtctp = rtctp_pp_payee_proxy_id + rtctp_pp_payee_acc_no + rtctp_other_payment
rt_payment = rtctp + rtddp
total = rt_payment + bat_payment
```

The main denominator for personal-account transfer shares is the same month's `rtctp`, including other real-time credit transfers. A separate measure compares proxy-ID payments only with the sum of the two personal-account categories.

The baseline contains no duplicate months, missing months, nulls, non-numeric values, negative values, or extra fields. All three reconciliation relationships pass. Volume uses zero tolerance; value uses an absolute tolerance of **0.0001 HKD thousand (HK$0.10)** for floating-point and source rounding differences. Any differences outside tolerance are reported without changing source values.

FPS was fully launched on 30 September 2018. September 2018 is marked as a potentially partial month and excluded from full-month growth comparisons and moving averages.

## Worked Reconciliation: August 2026

- Volume: **82,587,554 transactions**.
- Source value: **806,269,783.54935 HKD thousand**.
- Converted value: **HK$806,269,783,549.35**.
- Average: 806,269,783,549.35 ÷ 82,587,554 = **HK$9,762.6064**.
- Volume MoM: (82,587,554 − 84,300,073) ÷ 84,300,073 × 100 = **−2.03146%**.
- Volume YoY: an increase of **10,725,876 transactions**, or **14.92572%**, relative to August 2025.

Baseline responses: `data/raw/20260917T005922463786+0800/`. Each saved page includes the request URL.

Baseline quality report: `data/processed/20260917T005922463786+0800/metadata.json`.

## Derived Fields

| Suffix or field | Meaning |
|---|---|
| `_mom_abs` / `_yoy_abs` | Absolute change against the previous month / same month a year earlier, in the original metric's unit |
| `_mom_pct` / `_yoy_pct` | Growth rate expressed as a percentage; 20 means 20% growth, not a 20-percentage-point change in a share |
| `_ma12` | Simple average over 12 consecutive eligible monthly observations |
| `_share_total_pct` | Percentage of the same month's total payments, using the same measure |
| `_share_rtctp_pct` | Percentage of the same month's real-time credit transfers |
| `proxy_*_share_personal_pct` | Proxy-ID payments ÷ (proxy-ID payments + account-number payments) × 100 |
| `is_partial_launch_month` | Whether the month is September 2018 |
| `is_complete_calendar_month` | Whether the reporting month precedes the calendar month at analysis time |

Missing comparison months and zero denominators produce null percentages, exported as blank CSV cells. Absolute changes remain available when both values exist, even with a zero baseline. Headline metrics require both source totals, a completed calendar month, and exclusion of the launch month.

The 12-month line on the average-value chart is a simple average of monthly average transaction values, rather than a volume-weighted average over all transactions in the year.
