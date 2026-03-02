#!/usr/bin/env python3
"""
Email 通知測試腳本
用於測試 Email 設定是否正確
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_email_notification():
    print("=" * 50)
    print("📧 Email 通知設定測試")
    print("=" * 50)
    
    # 輸入設定
    print("\n請輸入 Email 設定資訊：")
    sender = input("發送者 Email (EMAIL_SENDER): ").strip()
    receiver = input("接收者 Email (EMAIL_RECEIVER): ").strip()
    password = input("應用程式密碼 (EMAIL_PASSWORD): ").strip()
    smtp_server = input("SMTP 伺服器 (預設 smtp.gmail.com): ").strip() or "smtp.gmail.com"
    smtp_port = input("SMTP 埠號 (預設 587): ").strip() or "587"
    
    print("\n" + "=" * 50)
    print("📤 正在發送測試郵件...")
    print("=" * 50)
    
    try:
        # 建立郵件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "🔔 測試通知 - 網頁監控爬蟲"
        msg['From'] = sender
        msg['To'] = receiver
        
        # 純文字版本
        text_body = """
這是一封測試郵件！

如果你收到這封信，表示 Email 通知設定成功 ✅

你可以開始使用網頁監控爬蟲了。

---
網頁監控爬蟲系統
        """
        text_part = MIMEText(text_body, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # HTML 版本
        html_body = """
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
              <h2 style="color: #4CAF50; border-bottom: 3px solid #4CAF50; padding-bottom: 10px;">
                🔔 測試通知成功！
              </h2>
              
              <div style="background-color: #f0f8ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="font-size: 18px; margin: 0;">
                  ✅ <strong>恭喜！Email 通知設定成功</strong>
                </p>
              </div>
              
              <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                <p style="margin: 0;">
                  <strong>📋 收到的設定資訊：</strong><br>
                  發送者：{sender}<br>
                  接收者：{receiver}<br>
                  SMTP 伺服器：{smtp_server}:{smtp_port}
                </p>
              </div>
              
              <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #666; margin-top: 0;">📝 接下來的步驟：</h3>
                <ol style="color: #666;">
                  <li>確認收到這封測試郵件</li>
                  <li>檢查是否在垃圾郵件資料夾</li>
                  <li>將發送者加入聯絡人（避免未來通知被歸類為垃圾郵件）</li>
                  <li>在 docker-compose-cron.yml 中設定相同的參數</li>
                  <li>啟動 Docker 容器開始監控</li>
                </ol>
              </div>
              
              <hr style="border: 0; border-top: 1px solid #e0e0e0; margin: 30px 0;">
              
              <p style="color: #999; font-size: 12px; text-align: center;">
                網頁監控爬蟲系統 | 自動發送的測試郵件
              </p>
            </div>
          </body>
        </html>
        """.format(
            sender=sender,
            receiver=receiver,
            smtp_server=smtp_server,
            smtp_port=smtp_port
        )
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 發送郵件
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.set_debuglevel(0)  # 設為 1 可以看到詳細的 SMTP 對話
            server.starttls()
            print("📡 正在連線到 SMTP 伺服器...")
            server.login(sender, password)
            print("🔐 登入成功！")
            server.send_message(msg)
            print("✅ 郵件發送成功！")
        
        print("\n" + "=" * 50)
        print("🎉 測試完成！")
        print("=" * 50)
        print(f"\n請檢查 {receiver} 的收件匣")
        print("如果沒有收到，請檢查垃圾郵件資料夾")
        print("\n✅ 如果收到郵件，表示設定正確，可以開始使用了！")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("\n" + "=" * 50)
        print("❌ 驗證失敗！")
        print("=" * 50)
        print("\n可能的原因：")
        print("1. 📧 Email 或密碼錯誤")
        print("2. 🔑 未使用應用程式密碼（Gmail 需要）")
        print("3. 🔐 未啟用兩步驟驗證（Gmail 需要）")
        print(f"\n錯誤訊息：{e}")
        return False
        
    except smtplib.SMTPException as e:
        print("\n" + "=" * 50)
        print("❌ SMTP 錯誤！")
        print("=" * 50)
        print(f"\n錯誤訊息：{e}")
        print("\n可能的原因：")
        print("1. 🌐 SMTP 伺服器或埠號錯誤")
        print("2. 🔥 防火牆阻擋連線")
        print("3. 📡 網路連線問題")
        return False
        
    except Exception as e:
        print("\n" + "=" * 50)
        print("❌ 未知錯誤！")
        print("=" * 50)
        print(f"\n錯誤訊息：{e}")
        return False

if __name__ == "__main__":
    print("""
    
    ┌─────────────────────────────────────────┐
    │   📧 Email 通知測試工具                  │
    │   用於測試 Email 設定是否正確            │
    └─────────────────────────────────────────┘
    
    """)
    
    try:
        test_email_notification()
    except KeyboardInterrupt:
        print("\n\n⚠️ 測試已取消")
    except Exception as e:
        print(f"\n❌ 發生錯誤：{e}")
    
    print("\n")
