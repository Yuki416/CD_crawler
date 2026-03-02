#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import hashlib
import json
import os
from datetime import datetime

class WebsiteMonitor:
    def __init__(self, username, password, url):
        self.username = username
        self.password = password
        self.url = url
        self.session = requests.Session()
        self.hash_file = "/data/page_hash.json"
        
    def login(self):
        """登入網站（需根據實際登入頁面調整）"""
        response = self.session.get(self.url)
        
        # 如果使用 HTTP Basic Authentication
        if response.status_code == 401:
            response = self.session.get(
                self.url,
                auth=(self.username, self.password)
            )
            return response.status_code == 200
        
        return True
    
    def get_page_content(self):
        """取得網頁內容"""
        try:
            response = self.session.get(self.url)
            if response.status_code == 200:
                return response.text
            else:
                print(f"取得網頁失敗，狀態碼: {response.status_code}")
                return None
        except Exception as e:
            print(f"取得網頁時發生錯誤: {e}")
            return None
    
    def calculate_hash(self, content):
        """計算內容的 SHA256 哈希值"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def load_previous_hash(self):
        """讀取上次儲存的哈希值"""
        if os.path.exists(self.hash_file):
            with open(self.hash_file, 'r') as f:
                data = json.load(f)
                return data.get('hash'), data.get('last_check')
        return None, None
    
    def save_hash(self, hash_value):
        """儲存新的哈希值"""
        data = {
            'hash': hash_value,
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        os.makedirs(os.path.dirname(self.hash_file), exist_ok=True)
        with open(self.hash_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save_page_content(self, content):
        """儲存網頁內容快照"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"/data/page_snapshot_{timestamp}.html"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已儲存網頁快照: {filename}")
    
    def send_email_notification(self, subject, body):
        """發送 Email 通知"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        sender = os.getenv('EMAIL_SENDER')
        receiver = os.getenv('EMAIL_RECEIVER')
        password = os.getenv('EMAIL_PASSWORD')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # 如果沒有設定 Email，就跳過
        if not all([sender, receiver, password]):
            print("Email 通知未設定，跳過發送")
            return False
        
        try:
            # 建立郵件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = receiver
            
            # 純文字版本
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # HTML 版本（更美觀）
            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #ff6b6b;">⚠️ 網頁更新通知</h2>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                  <pre style="white-space: pre-wrap; word-wrap: break-word;">{body}</pre>
                </div>
                <hr>
                <p style="color: #666; font-size: 12px;">
                  這是自動發送的通知郵件，請勿直接回覆。
                </p>
              </body>
            </html>
            """
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 發送郵件
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # 啟用 TLS 加密
                server.login(sender, password)
                server.send_message(msg)
            
            print(f"✅ Email 通知已發送到 {receiver}")
            return True
            
        except Exception as e:
            print(f"❌ 發送 Email 失敗: {e}")
            return False
    
    def send_line_notification(self, message):
        """發送 Line Notify 通知（保留作為備選）"""
        token = os.getenv('LINE_NOTIFY_TOKEN')
        if not token:
            return False
        
        url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": f"Bearer {token}"}
        data = {"message": message}
        
        try:
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                print("✅ Line 通知已發送")
                return True
            else:
                print(f"❌ 發送 Line 通知失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 發送 Line 通知時發生錯誤: {e}")
            return False
    
    def check_updates(self):
        """檢查網頁是否有更新"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 開始檢查網頁...")
        
        # 登入
        if not self.login():
            print("登入失敗！")
            return
        
        # 取得網頁內容
        content = self.get_page_content()
        if not content:
            return
        
        # 計算新的哈希值
        new_hash = self.calculate_hash(content)
        
        # 讀取舊的哈希值
        old_hash, last_check = self.load_previous_hash()
        
        if old_hash is None:
            print("首次檢查，儲存初始哈希值。")
            self.save_hash(new_hash)
        elif old_hash != new_hash:
            print("⚠️ 網頁有更新！")
            print(f"上次檢查: {last_check}")
            print(f"舊哈希值: {old_hash[:16]}...")
            print(f"新哈希值: {new_hash[:16]}...")
            self.save_hash(new_hash)
            self.save_page_content(content)
            
            # 準備通知訊息
            notification_message = (
                f"⚠️ 課程網頁已更新！\n\n"
                f"📅 更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🔗 網址：{self.url}\n"
                f"📊 上次檢查：{last_check}\n\n"
                f"舊哈希值: {old_hash[:16]}...\n"
                f"新哈希值: {new_hash[:16]}..."
            )
            
            # 發送通知（優先 Email，備用 Line）
            email_sent = self.send_email_notification(
                subject="🔔 課程網頁更新通知",
                body=notification_message
            )
            
            # 如果 Email 沒設定或失敗，嘗試 Line
            if not email_sent:
                self.send_line_notification(notification_message)
        else:
            print("✓ 網頁沒有變更。")
            print(f"上次檢查: {last_check}")

def main():
    # 從環境變數讀取設定
    username = os.getenv('WEB_USERNAME')
    password = os.getenv('WEB_PASSWORD')
    url = os.getenv('WEB_URL', 'https://www.cs.ccu.edu.tw/~damon/secure/course-wk.html')
    
    if not username or not password:
        print("錯誤：請設定 WEB_USERNAME 和 WEB_PASSWORD 環境變數")
        return
    
    monitor = WebsiteMonitor(username, password, url)
    monitor.check_updates()

if __name__ == "__main__":
    main()
