# 實際驗證報告

執行日期：2026-09-17，香港時間。環境：macOS ARM64、Python 3.13.14；完整版本見 `requirements-lock.txt`。

## 結果

| 檢查 | 實際結果 |
|---|---|
| 官方 API 下載 | 兩組均成功；96 行／組 |
| 月份範圍 | 2018-09 至 2026-08 |
| 重複／缺失月份 | 0／0 |
| 空值／非数值／負數 | 均未發現 |
| 三層合計驗證 | 兩組全部通過；原值不修改 |
| 自動測試 | **19 passed** |
| Chromium 桌面 | 實際啟動本機服務，五張 Plotly 圖成功渲染 |
| 指標／類別切換 | 金額及批量支付可選，無畫面例外 |
| 月份篩選 | Streamlit AppTest 驗證 2025-01 至 2026-08 |
| CSV 實際下載 | 96 行，最新 total_volume = 82,587,554 |
| 瀏覽器 JavaScript 錯誤 | 0 |
| 手機畫面 | 390 × 844 截圖，標題及 KPI 可讀，側欄折疊 |
| 無快照 | 錯誤提示，0 張假指標卡 |
| API 失敗 | 模擬失敗測試顯示舊快照日期；保留已成功版本 |

## 獨立數值核對

以保存嘅原始 JSON 及 Decimal 計算，核對筆數、千港元轉換、平均、MoM、YoY。

2026-08：

- 港元金額 = 806,269,783.54935 × 1,000 = HK$806,269,783,549.35。
- 平均每筆 = HK$806,269,783,549.35 ÷ 82,587,554 ≈ HK$9,762.61。
- 筆數 MoM = −1,712,519 筆（−2.031456%）。
- 筆數 YoY = +10,725,876 筆（+14.925724%）。
- 金額 MoM = −HK$51,083,680,510.91（−5.958299%）。
- 金額 YoY = +HK$67,153,125,176.07（+9.085592%）。
- 手算教學例子：50,000 千港元、10,000 筆 → HK$5,000／筆；零筆數 → 空值。

## 發現並修正嘅問題

1. 沙盒無法解析外網域名／綁定本機服務：經權限授權後下載套件、讀 API 同啟動服務，冇改用虛構數據。
2. 安裝版本嘅 Streamlit AppTest 以測試檔案位置解析相對路徑，初次 3 項画面測試失敗：改成以 project 根目錄定位，重跑 19 項全過。
3. 快照指標暫存檔改為每次更新獨立檔名，避免不同更新互相覆蓋暫存檔。

## 重跑

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m streamlit run app.py
```

另開 Terminal，在同一已啟用環境執行瀏覽器驗證：

```bash
python -m playwright install chromium
python tests/browser_check.py
```

交付驗證時瀏覽器下載至 `/tmp/fps-browsers`，因此使用 `PLAYWRIGHT_BROWSERS_PATH=/tmp/fps-browsers` 執行。正常安裝至 Playwright 預設位置唔需要呢個環境變數。瀏覽器測試嘅 96 行／2026-08 數字對應交付快照，更新快照後要同步調整期望值。

## 實際驗證範圍限制

已驗證本機 macOS 及 Chromium；Windows、Safari、公開雲端部署未實測。GitHub CI 檔已備妥但未上傳執行。API 故障以受控模擬測試，唔代表能預測所有網絡錯誤；所有 refresh 例外會由畫面統一處理。

截圖：`dashboard.png`（概覽）、`dashboard-detail.png`（資料下載區）、`dashboard-mobile.png`（手機概覽）。
