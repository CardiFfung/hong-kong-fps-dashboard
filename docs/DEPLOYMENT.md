# 公開 demo 部署準備

本地版已驗證；尚未建立公開網址。此 project 需要 Python 伺服器，採用原本指定嘅 Streamlit，唔將佢改成只能顯示靜態數字嘅網頁。

建議使用 Streamlit Community Cloud。已核對[官方部署文件](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)及[依賴文件](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)，核對日期 2026-09-17。

## 已準備好

- `app.py` 為啟動入口，`requirements.txt` 固定本地驗證版本。
- `.streamlit/config.toml` 設定主題。
- `data/current.json`、對應 raw 與 processed 快照可以一併提交，首次啟動唔依賴官方 API 即時可用。
- 冇 API 金鑰需要公開；唔好提交 `.venv`、任何帳戶憑證或個人檔案。
- `.github/workflows/tests.yml` 可喺 GitHub 重跑離線測試。

## 最後發佈步驟（需要帳戶）

1. 將 `fps-dashboard` 內容放到你選定 GitHub repository 根目錄；審閱 README、程式、快照同截圖。
2. 登入 Streamlit Community Cloud，選 Create app，指定 repository、branch 同 `app.py`。
3. Advanced settings 選 **Python 3.13**，與本地驗證主版本一致；唔需要設定 secrets。
4. 發佈後打開公開網址，確認五張圖、下載、更新及錯誤狀態，再將網址加入 README／CV。

雲端容器重啟可能清除執行期間寫入嘅快照，原始 repository 快照仍可用。正式长期更新應由擁有者定期執行 pipeline，審閱修訂再更新 repository，或另設持久儲存。呢版冇聲稱已具備生產級排程、監察或持久儲存。

尚欠：你嘅 GitHub／Streamlit 登入同發佈目的地。登入應由你喺瀏覽器完成，唔需要將密碼貼入對話。
