# 📧 Email 通知設定指南

## 為什麼推薦使用 Email？

✅ 簡單易用，不需要額外註冊服務  
✅ 通知會保留在信箱中，方便查閱  
✅ 支援 HTML 格式，更美觀  
✅ 不受第三方服務限制  

---

## 🎯 Gmail 設定教學（推薦）

### 步驟 1：啟用「兩步驟驗證」

1. 前往 Google 帳戶：https://myaccount.google.com/
2. 左側選單點選 **「安全性」**
3. 找到 **「兩步驟驗證」** 並啟用

### 步驟 2：建立「應用程式密碼」

1. 在「安全性」頁面，往下找到 **「應用程式密碼」**
2. 如果找不到，請確認步驟 1 已完成
3. 點擊「應用程式密碼」
4. 選擇：
   - 應用程式：**其他（自訂名稱）**
   - 輸入名稱：**網頁監控爬蟲**
5. 點擊 **「產生」**
6. **複製顯示的 16 位密碼**（只會顯示一次！）
   - 格式：`abcd efgh ijkl mnop`（包含空格）
   - 或：`abcdefghijklmnop`（無空格，兩種都可以）

### 步驟 3：設定環境變數

編輯 `docker-compose-cron.yml`：

```yaml
environment:
  # Email 通知設定
  - EMAIL_SENDER=your_email@gmail.com          # 你的 Gmail 地址
  - EMAIL_RECEIVER=your_email@gmail.com        # 接收通知的信箱（可以是同一個）
  - EMAIL_PASSWORD=abcdefghijklmnop            # 步驟 2 產生的應用程式密碼
  - SMTP_SERVER=smtp.gmail.com
  - SMTP_PORT=587
```

### 步驟 4：測試

```bash
# 重新啟動容器
docker-compose -f docker-compose-cron.yml down
docker-compose -f docker-compose-cron.yml up -d --build

# 手動執行一次測試（會在首次執行時儲存基準，第二次才會發送通知）
docker-compose -f docker-compose-cron.yml exec webpage-monitor-cron python /app/webpage_monitor.py
```

---

## 📮 其他信箱設定

### Yahoo Mail

```yaml
- EMAIL_SENDER=your_email@yahoo.com
- EMAIL_RECEIVER=your_email@yahoo.com
- EMAIL_PASSWORD=your_yahoo_app_password
- SMTP_SERVER=smtp.mail.yahoo.com
- SMTP_PORT=587
```

**取得 Yahoo 應用程式密碼：**
1. 前往：https://login.yahoo.com/account/security
2. 產生應用程式密碼

---

### Outlook / Hotmail

```yaml
- EMAIL_SENDER=your_email@outlook.com
- EMAIL_RECEIVER=your_email@outlook.com
- EMAIL_PASSWORD=your_outlook_password
- SMTP_SERVER=smtp-mail.outlook.com
- SMTP_PORT=587
```

**注意：** Outlook 可以直接使用帳號密碼，不需要應用程式密碼

---

### 自訂 SMTP 伺服器

如果你有自己的郵件伺服器：

```yaml
- EMAIL_SENDER=noreply@yourdomain.com
- EMAIL_RECEIVER=admin@yourdomain.com
- EMAIL_PASSWORD=your_smtp_password
- SMTP_SERVER=mail.yourdomain.com
- SMTP_PORT=587  # 或 465 (SSL)
```

---

## 🔧 測試 Email 設定

建立一個簡單的測試腳本：

```python
import smtplib
from email.mime.text import MIMEText

sender = "your_email@gmail.com"
receiver = "your_email@gmail.com"
password = "your_app_password"

msg = MIMEText("這是一封測試郵件")
msg['Subject'] = "測試通知"
msg['From'] = sender
msg['To'] = receiver

try:
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
    print("✅ Email 發送成功！")
except Exception as e:
    print(f"❌ 發送失敗：{e}")
```

儲存為 `test_email.py` 並執行：
```bash
python test_email.py
```

---

## ❓ 常見問題

### Q1: 顯示「Username and Password not accepted」

**原因：** 
- 未啟用兩步驟驗證
- 未使用應用程式密碼（直接用帳號密碼）
- 應用程式密碼輸入錯誤

**解決：**
1. 確認已啟用兩步驟驗證
2. 重新產生應用程式密碼
3. 確認複製密碼時沒有多餘的空格

### Q2: 顯示「SMTP AUTH extension not supported」

**原因：** SMTP 伺服器或埠號錯誤

**解決：**
- Gmail 使用：`smtp.gmail.com:587`
- 確認防火牆沒有阻擋 587 埠

### Q3: 我想同時發送到多個信箱

修改程式碼中的接收者：

```python
# 在 webpage_monitor.py 中
receiver = "email1@gmail.com,email2@gmail.com,email3@gmail.com"
```

或在 `docker-compose-cron.yml` 中：
```yaml
- EMAIL_RECEIVER=email1@gmail.com,email2@gmail.com
```

### Q4: Email 沒有收到，也沒有錯誤訊息

**檢查步驟：**
1. 查看 Gmail 的垃圾郵件資料夾
2. 查看容器日誌：
   ```bash
   docker-compose -f docker-compose-cron.yml logs
   ```
3. 確認環境變數是否正確設定：
   ```bash
   docker-compose -f docker-compose-cron.yml exec webpage-monitor-cron env | grep EMAIL
   ```

---

## 📱 Line Notify 設定（備選方案）

如果你還是想用 Line Notify：

### 步驟 1：取得 Token

1. 前往：https://notify-bot.line.me/
2. 登入 Line 帳號
3. 點選右上角「個人頁面」
4. 下方「發行權杖」
5. 輸入權杖名稱（例如：網頁監控）
6. 選擇接收通知的聊天室（建議選「透過1對1聊天接收Line Notify的通知」）
7. 點選「發行」
8. **複製 Token**（只會顯示一次！）

### 步驟 2：設定環境變數

```yaml
environment:
  - LINE_NOTIFY_TOKEN=your_line_notify_token_here
```

### 步驟 3：註解掉 Email 設定

如果只想用 Line，可以把 Email 相關的環境變數註解掉：

```yaml
# - EMAIL_SENDER=...
# - EMAIL_RECEIVER=...
# - EMAIL_PASSWORD=...
```

---

## 🎯 通知優先順序

程式會按照以下順序嘗試發送通知：

1. **Email**（優先）- 如果設定了 `EMAIL_SENDER`, `EMAIL_RECEIVER`, `EMAIL_PASSWORD`
2. **Line Notify**（備選）- 如果 Email 未設定或發送失敗，且設定了 `LINE_NOTIFY_TOKEN`

你可以同時設定兩種通知方式作為備援。

---

## 📊 通知內容範例

### Email 通知（HTML 格式）

```
主旨：🔔 課程網頁更新通知

⚠️ 網頁更新通知
━━━━━━━━━━━━━━━━━━━━
⚠️ 課程網頁已更新！

📅 更新時間：2026-03-02 14:30:15
🔗 網址：https://www.cs.ccu.edu.tw/~damon/secure/course-wk.html
📊 上次檢查：2026-03-02 09:00:00

舊哈希值: a1b2c3d4e5f6g7h8...
新哈希值: z9y8x7w6v5u4t3s2...
━━━━━━━━━━━━━━━━━━━━
這是自動發送的通知郵件，請勿直接回覆。
```

---

需要更多協助嗎？歡迎隨時提問！ 😊
