# Hong Kong FPS Trends Dashboard

**香港「轉數快」使用趨勢分析：從兩組金管局官方 API 建立可追溯、可更新、可互動嘅港元支付分析作品。**

Python · pandas · Streamlit · Plotly | HKD only | 96 months | 19 automated tests

[![Validate FPS dashboard](https://github.com/CardiFfung/hong-kong-fps-dashboard/actions/workflows/tests.yml/badge.svg)](https://github.com/CardiFfung/hong-kong-fps-dashboard/actions/workflows/tests.yml)

[GitHub repository](https://github.com/CardiFfung/hong-kong-fps-dashboard)

![實際運行截圖：最新月份概覽及支付趨勢](docs/dashboard.png)

> 本地成品已實際執行及驗證。公開 demo 尚待帳戶部署；不使用虛構 demo 網址。數據快照擷取於 2026-09-17T00:59:25.629892+08:00。

## 招聘者可以睇到乜

由官方資料擷取、分頁、清理、月份合併及品質檢查，到有明確定義嘅指標、互動圖表、CSV 下載同錯誤處理。作品適合展示 FinTech、Digital Banking、Payment Operations 或 Junior Data / Business Analyst 所需基礎能力；並非生產環境銀行系統。

## 研究問題

1. 每月港元 FPS 筆數同金額自推出以來點變？
2. 最新完整月相比上月／上年同月，絕對及百分比變化係幾多？
3. 即時及批量支付各佔總筆數／總金額幾多？
4. 個人代碼／帳戶號碼轉帳佔所有即時轉帳 `rtctp` 幾多？
5. 同月同類別平均每筆金額點變？

## 三個主要發現

以下由 2026-09-17 快照計算，最新月份為 2026-08；更新後 Dashboard 會重新計算，README 呢段係有日期嘅固定紀錄。

1. 2026-08 總筆數為 82,587,554 筆，按月 -2.03%，按年 +14.93%。
2. 同月總金額為 8,062.70 億港元，按年 +9.09%；平均每筆 9,762.61 港元。
3. 即時支付佔總筆數 88.13%，佔總金額 69.21%；筆數與金額組成並不相同。

以上係描述性結論，唔解釋原因。由首個完整月 2018-10 至最新月，總筆數由 1,682,647 增至 82,587,554，總金額由約 359.81 億增至 8,062.70 億港元；圖表保留中間波動，唔假設持續每月上升。

## 安裝及啟動

建議 **Python 3.13**（本機已使用 3.13.14 驗證）。先將 Terminal 切換到呢個 `fps-dashboard` 資料夾。

下載新副本：

```bash
git clone https://github.com/CardiFfung/hong-kong-fps-dashboard.git
cd hong-kong-fps-dashboard
```

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

瀏覽器打開 `http://localhost:8501`。本機交付已安裝好 `.venv`，可以直接 `source .venv/bin/activate` 後啟動，或在 Finder 雙擊 `Start Dashboard.command`。
Windows 啟用方式改為 `.venv\Scripts\activate`，建立環境用 `py -3.13 -m venv .venv`。

隨附真實官方快照，啟動唔需要即時連線。第一次重新下載或更新：

```bash
python -m src.pipeline
```

亦可按側欄「從 HKMA 更新資料」。每次取兩個來源全部月份，保留新版本，只有成功驗證後先切換快照；冇設定自動排程。API 失敗會顯示錯誤同舊資料日期；冇快照就停止顯示指標。

## 數據來源及定義

- [HKMA 港元 FPS 筆數 API](https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/banking/ch-statistics-turnover-fps-hkd-payment-vol)：交易筆數。
- [HKMA 港元 FPS 金額 API](https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/banking/ch-statistics-turnover-fps-hkd-payment-val)：**千港元，乘 1,000 先係港元**。
- [欄位、時間範圍、分頁及品質核對](docs/DATA_AUDIT.md)：包含官方文件連結及實際回應證據。

金額與筆數用月份一對一合併，以 `_volume`、`_value_hkd_thousand` 分清。平均每筆 = 同類別千港元 × 1,000 ÷ 筆數。MoM／YoY 需要確切上月／上年同月，零分母不計百分比。

總支付 = 即時支付 + 批量支付；即時支付 = 即時轉帳 + 即時扣帳。所有合計同子類別不可重複加埋。個人類別圖嘅主要比例分母係 `rtctp`，包括「其他即時轉帳」。

## 互動及展示

- 月份滑桿影響圖表及 CSV；類別選擇影響趨勢及平均圖。
- 筆數／金額切換影響模式組成及子類別比較。
- 最新月份卡及三個發現固定使用全資料最新完整月，避免篩選後誤稱「最新」。
- 五張圖分清筆數、金額、比例、平均；每張圖附閱讀方法及不可推論事項。
- CSV 按月份篩選，保留全部類別同兩種指標；原始快照、清理結果、呈現層分開。

## 專案結構

```text
app.py                  畫面、篩選、圖表、下載、錯誤提示
src/pipeline.py         API、分頁、清理、合併、驗證、全部衍生計算
requirements.txt        固定執行依賴
requirements-dev.txt    驗證工具
requirements-lock.txt   本機完整套件版本
 data/current.json      指向上次成功版本
 data/raw/<snapshot>/   原始回應及每頁網址
 data/processed/<snapshot>/  fps.csv、metadata.json
 tests/                 單元、畫面及瀏覽器檢查
 docs/                  截圖、資料核對、測試、部署、履歷及面試筆記
LEARNING_NOTES.md       新手廣東話／繁體中文學習路線
```

## 驗證

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m src.pipeline --offline
```

19 項測試通過：月份唯一、缺月處理、單位換算、零分母、推出月份排除、分母選擇、合計差異報告、分頁、API 失敗、快照保護及畫面篩選。另用 Decimal 手算核對最新官方數字，真實 Chromium 瀏覽器驗證五張圖、CSV 下載及手機畫面。詳見 [QA 報告](docs/QA_REPORT.md)。GitHub Actions 已於 2026-09-17 喺 Ubuntu / Python 3.13 [通過驗證](https://github.com/CardiFfung/hong-kong-fps-dashboard/actions/runs/35129351241)。

## 資料限制

- 僅港元；整體月度資料，唔知道個別用戶、獨立人數、用途或人口特徵。
- 2018-09-30 全面推出，9 月可能只係部分月份；圖上標記，增長率及移動平均排除。
- 平均每筆唔係中位數，亦唔能代表典型個人交易；大額交易同組成變化會影響平均。
- 月份長短、節日等可能影響總數；未作季節調整、因果分析或預測。
- 官方可能修訂，最新已結束月份唔代表永不修訂；快照保存擷取時間、來源及校驗值。
- 空值不填零。合計差異只報告，唔改官方原數據；最新頁面先檢查兩組總數存在。
- 雲端執行時嘅更新檔案可能隨重啟消失，需另設持久儲存或更新 repository 快照。

## 我喺 project 學到乜

定義正確分母比圖表花巧更重要；千港元轉港元需要一致單位；月份排序唔等於月份連續；資料錯誤唔可以用零遮掩；可重跑流程同原始快照令指標可以核對。

呢個初稿由 AI 協助實作。作為作品集持有人，應按 [LEARNING_NOTES](LEARNING_NOTES.md) 親手重跑、完成練習，並能解釋設計選擇，再按實際參與程度描述。

## 求職及部署

- [CV／LinkedIn 三句描述](docs/CV_LINKEDIN.md)
- [10 分鐘面試講解大綱](docs/INTERVIEW_OUTLINE.md)
- [公開 demo 部署步驟](docs/DEPLOYMENT.md)

本作品為獨立學習專案，數據來源為 HKMA，並非金管局官方產品。公開轉載數據時請保留來源並查閱官方使用條款。
