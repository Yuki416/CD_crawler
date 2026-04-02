#!/bin/bash

# 預設 cron 排程（每天早上 9:00）
CRON_SCHEDULE=${CRON_SCHEDULE:-"0 9 * * *"}

# 建立 cron job
echo "設定 cron 排程: $CRON_SCHEDULE"

# 將環境變數匯出到 cron 環境
printenv | grep -E '^(WEB_|LINE_|EMAIL_|SMTP_|LOGIN_|DATA_|BASIC_)' | sed 's/=\(.*\)/="\1"/' > /etc/environment

# 建立 crontab（同時執行網頁監控與講義下載）
echo "$CRON_SCHEDULE . /etc/environment && cd /app && /usr/local/bin/python3 webpage_monitor.py >> /var/log/monitor.log 2>&1 && /usr/local/bin/python3 ppt_downloader.py >> /var/log/ppt_downloader.log 2>&1" | crontab -

# 啟動 cron
cron

# 執行一次初始檢查
echo "執行初始檢查..."
/usr/local/bin/python3 webpage_monitor.py
/usr/local/bin/python3 ppt_downloader.py

# 保持容器運行並顯示日誌
echo "Cron 已啟動，等待排程執行..."
tail -f /var/log/monitor.log /var/log/cron.log 2>/dev/null || tail -f /dev/null
