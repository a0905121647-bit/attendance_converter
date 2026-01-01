# 快速部署指南

## 推薦部署方案

### 最簡單：Streamlit Cloud ⭐ 推薦

**優點**：
- 完全免費
- 一鍵部署
- 自動更新
- 官方支援

**步驟**：

1. **準備 GitHub 倉庫**
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/attendance_converter.git
git push -u origin main
```

2. **訪問 Streamlit Cloud**
   - 打開 https://streamlit.io/cloud
   - 使用 GitHub 帳戶登入

3. **部署應用**
   - 點擊「New app」
   - 選擇倉庫：`YOUR_USERNAME/attendance_converter`
   - 選擇分支：`main`
   - 設定主檔案路徑：`app.py`
   - 點擊「Deploy」

4. **獲取 URL**
   - 部署完成後，應用 URL 為：`https://your-app-name.streamlit.app`

---

## 替代方案

### 方案 2：Render

**優點**：
- 免費層級
- 自動重新部署
- 簡單配置

**步驟**：

1. 在 [Render](https://render.com) 建立帳戶
2. 連接 GitHub
3. 建立新 Web Service
4. 選擇倉庫
5. 設定：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port=8501 --server.address=0.0.0.0`
6. 部署

**URL 格式**：`https://your-app-name.onrender.com`

---

### 方案 3：Railway

**優點**：
- 快速部署
- 自動檢測
- 免費試用額度

**步驟**：

1. 在 [Railway](https://railway.app) 建立帳戶
2. 連接 GitHub
3. 選擇倉庫
4. Railway 自動檢測 `Procfile` 並部署
5. 應用將在 Railway 分配的 URL 上運行

**URL 格式**：`https://your-app-name-production.up.railway.app`

---

### 方案 4：Heroku

**優點**：
- 業界標準
- 豐富的附加服務
- 穩定可靠

**步驟**：

1. 安裝 [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

2. 登入 Heroku：
```bash
heroku login
```

3. 建立應用：
```bash
heroku create your-app-name
```

4. 部署：
```bash
git push heroku main
```

5. 查看應用：
```bash
heroku open
```

**URL 格式**：`https://your-app-name.herokuapp.com`

---

## 部署後的設定

### 1. 環境變數（如需要）

在部署平台設定環境變數：
```
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### 2. 自訂域名（可選）

大多數平台支援自訂域名：
- 在 DNS 設定中指向部署平台
- 在應用設定中配置自訂域名

### 3. SSL 證書

所有推薦的平台都提供免費 SSL 證書

---

## 常見部署問題

### 問題 1：部署失敗 - 依賴安裝錯誤

**解決方案**：
- 檢查 `requirements.txt` 格式
- 確保所有套件版本相容
- 清除快取並重新部署

### 問題 2：應用啟動失敗

**檢查清單**：
- [ ] `app.py` 存在且可執行
- [ ] 所有依賴已安裝
- [ ] 沒有 import 錯誤
- [ ] 檢查部署平台的日誌

### 問題 3：上傳檔案失敗

**解決方案**：
- 檢查檔案大小限制
- 確認 CSV 編碼為 UTF-8
- 驗證欄位名稱正確

### 問題 4：計算結果不正確

**檢查清單**：
- [ ] 員工起算時間設定正確
- [ ] CSV 日期時間格式有效
- [ ] 打卡順序正確（簽到在簽退前）

---

## 監控與維護

### 查看應用狀態

**Streamlit Cloud**：
- 訪問 https://share.streamlit.io
- 查看應用狀態和日誌

**Render**：
- 訪問 Render Dashboard
- 查看部署日誌和監控資訊

**Railway**：
- 訪問 Railway Dashboard
- 查看實時日誌

**Heroku**：
```bash
heroku logs --tail
```

### 更新應用

所有平台都支援自動更新：
1. 在本地修改代碼
2. 提交到 GitHub：
```bash
git add .
git commit -m "Update message"
git push origin main
```
3. 部署平台自動檢測並重新部署

---

## 性能優化建議

### 1. 快取設定

在 `.streamlit/config.toml` 中：
```toml
[client]
showErrorDetails = true

[logger]
level = "info"
```

### 2. 限制上傳檔案大小

在應用中添加檢查：
```python
if uploaded_file.size > 10 * 1024 * 1024:  # 10MB
    st.error("檔案過大")
```

### 3. 定期清理臨時檔案

部署平台會自動清理，但可手動管理。

---

## 成本估算

| 平台 | 免費層級 | 推薦層級 | 成本 |
|------|--------|--------|------|
| Streamlit Cloud | ✅ | - | 免費 |
| Render | ✅ | 付費 | $7/月起 |
| Railway | ✅ | 付費 | 按使用量計費 |
| Heroku | ❌ | 付費 | $7/月起 |

---

## 支援的部署平台

| 平台 | 難度 | 成本 | 推薦度 |
|------|------|------|--------|
| Streamlit Cloud | ⭐ 簡單 | 免費 | ⭐⭐⭐⭐⭐ |
| Render | ⭐⭐ 中等 | 免費/付費 | ⭐⭐⭐⭐ |
| Railway | ⭐⭐ 中等 | 免費/付費 | ⭐⭐⭐⭐ |
| Heroku | ⭐⭐ 中等 | 付費 | ⭐⭐⭐ |

---

## 下一步

1. 選擇部署平台
2. 按照相應步驟部署
3. 測試應用功能
4. 分享 URL 給團隊使用

---

**需要幫助？** 查看 README.md 中的常見問題或聯絡技術支援。
