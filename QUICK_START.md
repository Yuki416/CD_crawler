# 🎯 快速參考指南

## 📚 文件導覽

| 文件 | 用途 |
|------|------|
| [README.md](README.md) | 專案總覽和快速開始 |
| [EMAIL_SETUP.md](EMAIL_SETUP.md) | 📧 **Email 通知詳細設定指南** |
| [SETUP.md](SETUP.md) | Docker 容器設定說明 |
| `test_email.py` | Email 設定測試工具 |

---

## ⚡ 三步驟快速開始

### 1️⃣ 測試 Email（5 分鐘）

```bash
python test_email.py
```

按照提示輸入你的 Gmail 資訊，收到測試郵件表示成功。

**取得 Gmail 應用程式密碼：**
1. 前往 https://myaccount.google.com/security
2. 啟用「兩步驟驗證」
3. 建立「應用程式密碼」

詳細步驟 → [EMAIL_SETUP.md](EMAIL_SETUP.md)

---

### 2️⃣ 設定環境變數（2 分鐘）

```bash
cp docker-compose-cron.yml.example docker-compose-cron.yml
nano docker-compose-cron.yml
```

修改這些參數：
```yaml
- WEB_USERNAME=your_ccu_username      # CCU 登入帳號
- WEB_PASSWORD=your_ccu_password      # CCU 登入密碼
- EMAIL_SENDER=you@gmail.com          # 你的 Gmail
- EMAIL_RECEIVER=you@gmail.com        # 接收通知的信箱
- EMAIL_PASSWORD=abcd1234efgh5678     # Gmail 應用程式密碼
```

---

### 3️⃣ 啟動容器（1 分鐘）

```bash
docker-compose -f docker-compose-cron.yml up -d --build
docker-compose -f docker-compose-cron.yml logs -f
```

完成！🎉 容器會自動在背景運行，每天檢查網頁更新。

---

## 🔔 通知方式比較

| 功能 | Email | Line Notify |
|------|-------|-------------|
| 設定難度 | ⭐⭐ (需要應用程式密碼) | ⭐ (一個 Token) |
| 通用性 | ✅ 任何人都有 Email | ❌ 需要 Line 帳號 |
| 訊息格式 | ✅ 支援 HTML（美觀） | ❌ 純文字 |
| 記錄保存 | ✅ 永久保存在信箱 | ❌ 可能被洗掉 |
| 即時性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 推薦度 | ✅ 推薦 | 可作為備援 |

---

## 📋 常用指令

```bash
# 啟動
docker-compose -f docker-compose-cron.yml up -d

# 停止
docker-compose -f docker-compose-cron.yml down

# 查看日誌
docker-compose -f docker-compose-cron.yml logs -f

# 重啟
docker-compose -f docker-compose-cron.yml restart

# 手動執行一次
docker-compose -f docker-compose-cron.yml exec webpage-monitor-cron python /app/webpage_monitor.py

# 檢查狀態
docker-compose -f docker-compose-cron.yml ps

# 查看哈希記錄
cat data/page_hash.json

# 進入容器除錯
docker-compose -f docker-compose-cron.yml exec webpage-monitor-cron bash
```

---

## 🕐 Cron 排程範例

修改 `docker-compose-cron.yml` 中的 `CRON_SCHEDULE`：

```yaml
# 常用範例
- CRON_SCHEDULE=0 9 * * *          # 每天早上 9:00
- CRON_SCHEDULE=0 */6 * * *        # 每 6 小時
- CRON_SCHEDULE=*/30 * * * *       # 每 30 分鐘
- CRON_SCHEDULE=0 9,21 * * *       # 每天 9:00 和 21:00
- CRON_SCHEDULE=0 9 * * 1-5        # 週一到週五 9:00
```

格式說明：
```
* * * * *
│ │ │ │ │
│ │ │ │ └─ 星期幾 (0-7)
│ │ │ └─── 月份 (1-12)
│ │ └───── 日期 (1-31)
│ └─────── 小時 (0-23)
└───────── 分鐘 (0-59)
```

---

## ❓ 疑難排解

### 問題 1: Email 發送失敗

**症狀：** 顯示「Username and Password not accepted」

**解決方法：**
1. 確認已啟用 Gmail「兩步驟驗證」
2. 使用「應用程式密碼」而非帳號密碼
3. 檢查密碼是否複製正確（去除空格）

詳細說明 → [EMAIL_SETUP.md](EMAIL_SETUP.md#常見問題)

---

### 問題 2: 沒有收到通知

**檢查步驟：**
```bash
# 1. 查看容器日誌
docker-compose -f docker-compose-cron.yml logs

# 2. 檢查環境變數
docker-compose -f docker-compose-cron.yml exec webpage-monitor-cron env | grep EMAIL

# 3. 手動測試
docker-compose -f docker-compose-cron.yml exec webpage-monitor-cron python /app/webpage_monitor.py

# 4. 檢查垃圾郵件資料夾
```

---

### 問題 3: 容器無法啟動

```bash
# 查看錯誤訊息
docker-compose -f docker-compose-cron.yml logs

# 重新建立映像檔
docker-compose -f docker-compose-cron.yml build --no-cache

# 檢查設定檔語法
cat docker-compose-cron.yml
```

---

## 🔒 安全性提醒

⚠️ **重要：**
- `docker-compose-cron.yml` 包含密碼，**不要上傳到 GitHub**
- 已加入 `.gitignore`，不會被追蹤
- 只上傳 `docker-compose-cron.yml.example` 範本

---

## 📞 需要更多幫助？

- 📧 Email 設定：[EMAIL_SETUP.md](EMAIL_SETUP.md)
- 🐳 Docker 設定：[SETUP.md](SETUP.md)
- 📖 完整說明：[README.md](README.md)

---

**Happy Monitoring! 🎉**
