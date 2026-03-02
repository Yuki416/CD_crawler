# 網頁更新監控爬蟲 - Docker 版本

自動監控網頁更新的 Docker 化爬蟲系統，支援 Email 和 Line 通知。

## ✨ 功能特色

- ✅ 自動登入並監控網頁更新
- ✅ 使用 Docker 容器化部署
- ✅ **支援 Email 通知**（推薦，附 HTML 格式）
- ✅ 支援 Line Notify 通知（備選）
- ✅ 自動儲存網頁快照
- ✅ Cron 定時執行
- ✅ 系統重啟後自動恢復

## 📧 通知方式

### Email 通知（推薦）
- 簡單易用，不需要額外註冊服務
- 支援 Gmail、Yahoo、Outlook 等
- 美觀的 HTML 格式通知
- 📖 **詳細設定請參考 [EMAIL_SETUP.md](EMAIL_SETUP.md)**

### Line Notify（備選）
- 即時推播到 Line
- 需要取得 Line Notify Token
- 作為 Email 的備援方案

---

## 🚀 快速開始

### 前置需求

- Docker 和 Docker Compose
- Gmail 帳號（用於接收通知）或 Line 帳號

### 步驟 1：測試 Email 設定（可選但推薦）

```bash
# 執行測試腳本
python test_email.py
```

按照提示輸入 Gmail 資訊，如果收到測試郵件就表示設定正確。

**📖 不知道如何取得 Gmail 應用程式密碼？** 請參考 [EMAIL_SETUP.md](EMAIL_SETUP.md)

### 步驟 2：設定環境變數

```bash
# 複製範本檔案
cp docker-compose-cron.yml.example docker-compose-cron.yml

# 編輯設定檔
nano docker-compose-cron.yml
```

填入你的資訊：
```yaml
environment:
  # 網站登入資訊
  - WEB_USERNAME=your_username
  - WEB_PASSWORD=your_password
  
  # Email 通知（推薦）
  - EMAIL_SENDER=your_email@gmail.com
  - EMAIL_RECEIVER=your_email@gmail.com
  - EMAIL_PASSWORD=your_gmail_app_password
  - SMTP_SERVER=smtp.gmail.com
  - SMTP_PORT=587
  
  # 或使用 Line Notify（備選）
  # - LINE_NOTIFY_TOKEN=your_line_token
  
  # Cron 排程（預設每天早上 9:00）
  - CRON_SCHEDULE=0 9 * * *
```

### 步驟 3：啟動服務

```bash
docker-compose -f docker-compose-cron.yml up -d --build
```

### 步驟 4：查看日誌

```bash
# 即時查看日誌
docker-compose -f docker-compose-cron.yml logs -f

# 或只看最後 50 行
docker-compose -f docker-compose-cron.yml logs --tail=50
```

---

---

## ⚙️ 常用操作

### 停止服務
```bash
docker-compose -f docker-compose-cron.yml down
```

### 重新啟動
```bash
docker-compose -f docker-compose-cron.yml restart
```

### 手動執行一次檢查
```bash
docker-compose -f docker-compose-cron.yml exec webpage-monitor-cron python /app/webpage_monitor.py
```

### 查看儲存的資料

```bash
# 查看哈希記錄
cat data/page_hash.json

# 查看網頁快照
ls -lh data/page_snapshot_*.html
```

### 查看容器狀態
```bash
docker-compose -f docker-compose-cron.yml ps
```

---

## 📅 Cron 排程格式

### 方法一：單次執行（手動觸發）

1. **建立 Docker 映像檔**
```bash
docker build -t webpage-monitor .
```

2. **執行容器（單次檢查）**
```bash
docker run --rm \
  -e WEB_USERNAME="your_username" \
  -e WEB_PASSWORD="your_password" \
  -v $(pwd)/data:/data \
  webpage-monitor
```

### 方法二：使用 Docker Compose（推薦）

1. **修改設定檔**

編輯 `docker-compose-cron.yml`，設定你的帳號密碼：
```yaml
environment:
  - WEB_USERNAME=your_actual_username
  - WEB_PASSWORD=your_actual_password
  - CRON_SCHEDULE=0 9 * * *  # 每天早上 9:00
```

2. **啟動服務**
```bash
docker-compose -f docker-compose-cron.yml up -d
```

3. **檢查日誌**
```bash
docker-compose -f docker-compose-cron.yml logs -f
```

4. **停止服務**
```bash
docker-compose -f docker-compose-cron.yml down
```

## Cron 排程格式

```
* * * * *
│ │ │ │ │
│ │ │ │ └─ 星期幾 (0-7, 0 和 7 都代表星期日)
│ │ │ └─── 月份 (1-12)
│ │ └───── 日期 (1-31)
│ └─────── 小時 (0-23)
└───────── 分鐘 (0-59)
```

常用範例：
- `0 9 * * *` - 每天早上 9:00
- `0 */6 * * *` - 每 6 小時一次
- `*/30 * * * *` - 每 30 分鐘一次
- `0 9,21 * * *` - 每天 9:00 和 21:00

## 進階設定

### 加入 Line Notify 通知

1. 取得 Line Notify Token：https://notify-bot.line.me/
2. 在 `docker-compose-cron.yml` 中加入：
```yaml
environment:
  - LINE_NOTIFY_TOKEN=your_line_token
```

### 手動觸發檢查

```bash
docker-compose -f docker-compose-cron.yml exec webpage-monitor-cron python /app/webpage_monitor.py
```

### 查看儲存的資料

```bash
# 查看哈希記錄
cat data/page_hash.json

# 查看網頁快照
ls -lh data/page_snapshot_*.html
```

## 目錄結構

```
.
├── Dockerfile              # 單次執行用
├── Dockerfile.cron         # Cron 定期執行用
├── docker-compose.yml      # 單次執行設定
├── docker-compose-cron.yml # Cron 定期執行設定
├── docker-entrypoint.sh    # Cron 容器啟動腳本
├── webpage_monitor.py      # 主程式
├── requirements.txt        # Python 套件
├── data/                   # 資料目錄（持久化）
│   ├── page_hash.json     # 哈希記錄
│   └── page_snapshot_*.html # 網頁快照
└── logs/                   # 日誌目錄
    └── monitor.log        # 執行日誌
```

## 使用外部 Cron（替代方案）

如果不想在容器內運行 cron，可以使用系統的 cron 來定期觸發容器：

```bash
# 編輯 crontab
crontab -e

# 加入以下行（每天早上 9:00 執行）
0 9 * * * cd /home/under115b/work/lungyu_workspace/deep_learning/other_works && docker-compose run --rm webpage-monitor >> logs/monitor.log 2>&1
```

## 疑難排解

### 查看容器日誌
```bash
docker-compose -f docker-compose-cron.yml logs webpage-monitor-cron
```

### 進入容器除錯
```bash
docker-compose -f docker-compose-cron.yml exec webpage-monitor-cron bash
```

### 重新建立映像檔
```bash
docker-compose -f docker-compose-cron.yml build --no-cache
```

### 檢查 Cron 是否運行
```bash
docker-compose -f docker-compose-cron.yml exec webpage-monitor-cron crontab -l
```

## 注意事項

- 第一次執行會建立基準哈希值
- 資料會儲存在 `./data` 目錄（需確保有寫入權限）
- 日誌會儲存在 `./logs` 目錄
- 記得定期清理舊的快照檔案
- 請確認目標網站允許爬蟲存取
