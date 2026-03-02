# 設定步驟

## 第一次使用

1. **複製範本檔案**
   ```bash
   cp docker-compose-cron.yml.example docker-compose-cron.yml
   ```

2. **編輯設定檔，填入真實帳號密碼**
   ```bash
   nano docker-compose-cron.yml
   ```
   或使用任何編輯器開啟 `docker-compose-cron.yml`，修改：
   - `WEB_USERNAME`: 你的登入帳號
   - `WEB_PASSWORD`: 你的登入密碼
   - `LINE_NOTIFY_TOKEN`: （可選）如需 Line 通知

3. **啟動容器**
   ```bash
   docker-compose -f docker-compose-cron.yml up -d --build
   ```

## ⚠️ 安全性注意事項

- `docker-compose-cron.yml` 包含真實帳密，**絕對不要上傳到 GitHub**
- 此檔案已加入 `.gitignore`，不會被 git 追蹤
- 只上傳 `docker-compose-cron.yml.example` 範本檔案到 GitHub

## 其他命令

```bash
# 查看日誌
docker-compose -f docker-compose-cron.yml logs -f

# 停止容器
docker-compose -f docker-compose-cron.yml down

# 重新啟動
docker-compose -f docker-compose-cron.yml restart

# 手動執行一次檢查
docker-compose -f docker-compose-cron.yml exec webpage-monitor-cron python /app/webpage_monitor.py
```
