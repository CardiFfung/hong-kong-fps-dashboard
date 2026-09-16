# 官方資料核對紀錄

核對日期：2026-09-17（香港時間）；成功擷取：2026-09-17T00:59:25.629892+08:00。

## 先核對文件，再編程

- [筆數欄位文件](https://apidocs.hkma.gov.hk/documentation/market-data-and-statistics/monthly-statistical-bulletin/banking/ch-statistics-turnover-fps-hkd-payment-vol/)
- [金額欄位文件](https://apidocs.hkma.gov.hk/documentation/market-data-and-statistics/monthly-statistical-bulletin/banking/ch-statistics-turnover-fps-hkd-payment-val/)
- [一般使用方法](https://apidocs.hkma.gov.hk/documentation/)
- [實際筆數 API](https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/banking/ch-statistics-turnover-fps-hkd-payment-vol)
- [實際金額 API](https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/banking/ch-statistics-turnover-fps-hkd-payment-val)

網頁擷取工具最初對一般文件及 API 逾時；其後直接下載官方 HTTPS 回應成功，沒有改用非官方資料。沙盒禁止網絡時，經授權連線完成下載。

## 實際回應

`header.success=true`，`err_code=0000`，`result.records` 為物件清單，`result.datasize=96`。
兩組各 96 行，涵蓋 **2018-09 至 2026-08**；擷取當日最新已結束曆月係 2026-08。
`end_of_month` 實際為 `YYYY-MM` 字串。筆數為整數；金額含小數，單位為千港元。原始預設回應按月份由新到舊，pipeline 明確要求升序並在清理時再排序。

預設每頁 100 行，上限 1,000 行，`offset` 指跳過嘅行數。本次 `pagesize=1000` 一頁即可取全；程式仍持續讀取滿頁之後嘅頁面，單元測試覆蓋剛好滿頁、空尾頁及重複頁。

| 實際欄位 | 中文說明 |
|---|---|
| `end_of_month` | 統計月份 |
| `total` | 總支付 |
| `rt_payment` | 即時支付 |
| `bat_payment` | 批量支付 |
| `rtctp` | 即時轉帳 |
| `rtddp` | 即時扣帳 |
| `rtctp_pp_payee_proxy_id` | 個人：收款人代碼 |
| `rtctp_pp_payee_acc_no` | 個人：帳戶號碼 |
| `rtctp_other_payment` | 其他即時轉帳 |

合併後原始筆數後綴 `_volume`，原始金額後綴 `_value_hkd_thousand`；衍生港元金額 `_value_hkd`、平均 `_avg_hkd`。

## 定義及驗證

- `rtctp` = 代碼 + 帳號 + 其他即時轉帳。
- `rt_payment` = `rtctp` + `rtddp`。
- `total` = `rt_payment` + `bat_payment`。
- 個人子類別主要比例分母為同月 `rtctp`；另設兩個個人子類別合計做分母嘅代碼比例，欄名清楚區分。
- 全面推出日期為 2018-09-30；2018-09 標為可能部分月份，排除完整月份增長率及移動平均。

本次兩組均無重複月份、缺月、空值、非數值、負數或額外欄位。三層合計全部通過：筆數容差 0，金額容差 0.0001 千港元（HK$0.10），用於浮點及來源小數捨入。發現合計差異時只報告，不修正來源數字。

## 手算可追溯例子：2026-08

- 筆數：82,587,554。
- 原始金額：806,269,783.54935 千港元。
- 港元：806,269,783,549.35。
- 平均每筆：806,269,783,549.35 ÷ 82,587,554 = 9,762.6064 港元。
- 筆數 MoM：(82,587,554 − 84,300,073) ÷ 84,300,073 = −2.03146%。
- 筆數 YoY：相對 2025-08 增加 10,725,876 筆，即 +14.92572%。

完整原始回應：`data/raw/20260917T005922463786+0800/`；每頁包含實際請求網址。
完整品質報告：`data/processed/20260917T005922463786+0800/metadata.json`。

## 衍生欄位字典

| 後綴／欄位 | 意義 |
|---|---|
| `_mom_abs` / `_yoy_abs` | 同上月／上年同月嘅絕對差，單位跟原指標 |
| `_mom_pct` / `_yoy_pct` | 百分點表示嘅增長率，例如 20 代表 20% |
| `_ma12` | 12 個連續合資格月份簡單平均 |
| `_share_total_pct` | 佔同月總支付百分比；只作同指標比較 |
| `_share_rtctp_pct` | 子類別佔同月即時轉帳百分比 |
| `proxy_*_share_personal_pct` | 代碼 ÷（代碼 + 帳號）× 100 |
| `is_partial_launch_month` | 是否 2018-09 推出月份 |
| `is_complete_calendar_month` | 是否早於擷取／分析當日所處曆月 |

月份欠缺、零分母等情況以空值表示，CSV 內留空。最新 KPI 要求兩組總數均存在、曆月已結束且並非推出月份。下載包括全部類別，但不同層級不可一起加總。
