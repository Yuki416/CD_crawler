#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import hashlib
import json
import os
import re
import glob
import difflib
from datetime import datetime

class WebsiteMonitor:
    def __init__(self, username, password, url, data_prefix='page'):
        self.username = username
        self.password = password
        self.url = url
        self.data_prefix = data_prefix
        self.session = requests.Session()
        self.hash_file = f"/data/{data_prefix}_hash.json"

    def login(self):
        """登入網站，依 LOGIN_TYPE 環境變數選擇登入方式"""
        login_type = os.getenv('LOGIN_TYPE', 'basic')

        if login_type == 'phpbb':
            return self._login_phpbb()

        # HTTP Basic Auth 模式
        from requests.auth import HTTPBasicAuth

        response = self.session.get(self.url)

        if response.status_code == 401:
            print("偵測到需要 HTTP Basic Authentication，正在登入...")
            self.session.auth = HTTPBasicAuth(self.username, self.password)
            response = self.session.get(self.url)
            if response.status_code == 200:
                print(f"✅ 登入成功！（帳號: {self.username}）")
                return True
            else:
                print(f"❌ 登入失敗，狀態碼: {response.status_code}")
                return False

        print("✅ 網頁不需要認證，直接訪問成功")
        return True

    def _login_phpbb(self):
        """phpBB 表單登入（支援外層 HTTP Basic Auth）"""
        from urllib.parse import urlparse
        from requests.auth import HTTPBasicAuth

        parsed = urlparse(self.url)
        path_parts = parsed.path.rstrip('/').split('/')
        forum_root = '/'.join(path_parts[:-1]) + '/'
        base = f"{parsed.scheme}://{parsed.netloc}{forum_root}"
        login_url = base + "ucp.php?mode=login"

        # 先試一次，若整站有 Basic Auth 保護則先補上
        probe = self.session.get(login_url)
        if probe.status_code == 401:
            print("偵測到外層 HTTP Basic Auth，先補上認證...")
            basic_user = os.getenv('BASIC_USERNAME', self.username)
            basic_pass = os.getenv('BASIC_PASSWORD', self.password)
            self.session.auth = HTTPBasicAuth(basic_user, basic_pass)
            probe = self.session.get(login_url)
            if probe.status_code != 200:
                print(f"❌ HTTP Basic Auth 失敗，狀態碼: {probe.status_code}")
                return False

        # 取得 phpBB 登入表單隱藏欄位
        soup = BeautifulSoup(probe.text, 'html.parser')

        def hidden(name, default=''):
            tag = soup.find('input', {'name': name})
            return tag['value'] if tag else default

        post_data = {
            'username': self.username,
            'password': self.password,
            'login': 'Login',
            'redirect': hidden('redirect', 'index.php'),
            'creation_time': hidden('creation_time'),
            'form_token': hidden('form_token'),
            'sid': hidden('sid'),
        }

        # phpBB 的 form_token_mintime 要求 GET 取得表單後至少等幾秒才能 POST，
        # 否則會回傳「表單送出無效」(CSRF 驗證失敗)
        import time
        time.sleep(5)

        resp = self.session.post(login_url, data=post_data)

        # phpBB 登入成功後：
        #   _u cookie 會從 '1'（匿名）變成實際 user ID（> 1）
        #   _k cookie 在勾選「記得我」時才會有值，平常為空字串
        # 注意：phpBB 對所有訪客都會設 _k=''，不可只靠 name.endswith('_k') 判斷
        cookies = [(c.name, c.value) for c in self.session.cookies]
        logged_in = any(
            (name.endswith('_u') and value not in ('', '0', '1')) or
            (name.endswith('_k') and value != '')
            for name, value in cookies
        )
        if not logged_in:
            print(f"❌ phpBB 登入失敗（帳號: {self.username}）")
            return False

        print(f"✅ phpBB 登入成功！（帳號: {self.username}）")
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
                return data.get('hash'), data.get('last_check'), data.get('snapshot')
        return None, None, None

    def save_hash(self, hash_value, snapshot_file):
        """儲存新的哈希值與對應快照路徑"""
        data = {
            'hash': hash_value,
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'snapshot': snapshot_file,
        }
        os.makedirs(os.path.dirname(self.hash_file), exist_ok=True)
        with open(self.hash_file, 'w') as f:
            json.dump(data, f, indent=2)

    def save_page_content(self, content):
        """儲存網頁內容快照，回傳檔案路徑"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"/data/{self.data_prefix}_snapshot_{timestamp}.html"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已儲存網頁快照: {filename}")
        return filename

    def get_previous_snapshot(self, snapshot_path):
        """取得指定快照的內容"""
        if snapshot_path and os.path.exists(snapshot_path):
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def extract_course_sections(self, html):
        """將 HTML 依課程區段切割，回傳 {課程名稱: 純文字} 的 dict"""
        # 略過的內部標記
        skip_pattern = re.compile(r'^(只|這些|下一門課|最新訊息$)')
        section_marker = re.compile(r'<!\*{5,}([^*>\n]+)\*{5,}>')

        sections = {}
        current_course = None
        last_pos = 0

        for match in section_marker.finditer(html):
            name = match.group(1).strip()

            # 將目前位置到這個標記之間的 HTML 存入目前課程
            if current_course:
                chunk = html[last_pos:match.start()]
                text = self._html_to_text(chunk)
                if text:
                    sections.setdefault(current_course, [])
                    sections[current_course].append(text)

            # 跳過非課程名稱的標記
            if not skip_pattern.match(name) and name:
                current_course = name
            last_pos = match.end()

        # 最後一段
        if current_course:
            chunk = html[last_pos:]
            text = self._html_to_text(chunk)
            if text:
                sections.setdefault(current_course, [])
                sections[current_course].append(text)

        return {k: '\n'.join(v) for k, v in sections.items()}

    def _html_to_text(self, html_chunk):
        """將 HTML 片段轉成純文字（只含瀏覽器可見內容）。
        先移除 <!tag>...</!tag> 偽標籤，避免 html.parser 崩潰。"""
        # 移除配對的偽標籤及其內容（<!strike>...</!strike> 等）
        cleaned = re.sub(r'<![^>]*>.*?<!/[^>]+>', '', html_chunk, flags=re.DOTALL)
        # 移除剩餘的單個 <!...> 標籤
        cleaned = re.sub(r'<![^>]*>', '', cleaned)
        soup = BeautifulSoup(cleaned, 'html.parser')
        lines = [l.strip() for l in soup.get_text(separator='\n').splitlines()]
        return '\n'.join(l for l in lines if l)

    def _html_to_text_full(self, html_chunk):
        """將 HTML 片段轉成純文字（含偽標籤內容）。用 regex 避免 parser 崩潰。"""
        import html as html_module
        text = html_chunk
        # 移除 <style>/<script>
        text = re.sub(r'<(style|script)[^>]*>.*?</\1>', '', text, flags=re.DOTALL | re.I)
        # 換行語意
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
        text = re.sub(r'</(p|div|li|tr)[^>]*>', '\n', text, flags=re.I)
        # 移除偽標籤的尖括號部分，保留內容（<!tag>content<!/tag> → content）
        text = re.sub(r'<!((?!--)(?!DOCTYPE)[^>]*)>', '', text)
        text = re.sub(r'<!/[^>]*>', '', text)
        # 移除其他 HTML 標籤
        text = re.sub(r'<[^>]+>', '', text)
        text = html_module.unescape(text)
        lines = [l.strip() for l in text.splitlines()]
        return '\n'.join(l for l in lines if l)

    def get_changed_sections(self, old_html, new_html):
        """比對新舊 HTML，回傳有變動的課程區段和 diff 摘要。
        每筆結果為 (課程名, diff行列表, 是否僅偽標籤更動)。"""
        # 可見內容（用來判斷是否只有偽標籤改動）
        old_sections = self.extract_course_sections(old_html)
        new_sections = self.extract_course_sections(new_html)

        # 全文（含偽標籤內容，用來產生 diff）
        old_full = self._extract_sections_full(old_html)
        new_full = self._extract_sections_full(new_html)

        all_courses = set(old_full) | set(new_full)
        changes = []

        for course in sorted(all_courses):
            old_text_full = old_full.get(course, '')
            new_text_full = new_full.get(course, '')
            if old_text_full == new_text_full:
                continue

            # 可見文字相同 → 只有偽標籤區塊內容改變
            pseudo_only = (old_sections.get(course, '') == new_sections.get(course, ''))

            old_lines = old_text_full.splitlines()
            new_lines = new_text_full.splitlines()
            diff = list(difflib.unified_diff(
                old_lines, new_lines,
                lineterm='', n=2
            ))

            if diff:
                # 只取 +/- 行，最多 20 行避免 Email 太長
                diff_lines = [l for l in diff if l.startswith(('+', '-')) and not l.startswith(('+++', '---'))]
                changes.append((course, diff_lines[:20], pseudo_only))

        return changes

    def _extract_sections_full(self, html):
        """與 extract_course_sections 相同邏輯，但用 _html_to_text_full（含偽標籤內容）"""
        skip_pattern = re.compile(r'^(只|這些|下一門課|最新訊息$)')
        section_marker = re.compile(r'<!\*{5,}([^*>\n]+)\*{5,}>')

        sections = {}
        current_course = None
        last_pos = 0

        for match in section_marker.finditer(html):
            name = match.group(1).strip()

            if current_course:
                chunk = html[last_pos:match.start()]
                text = self._html_to_text_full(chunk)
                if text:
                    sections.setdefault(current_course, [])
                    sections[current_course].append(text)

            if not skip_pattern.match(name) and name:
                current_course = name
            last_pos = match.end()

        if current_course:
            chunk = html[last_pos:]
            text = self._html_to_text_full(chunk)
            if text:
                sections.setdefault(current_course, [])
                sections[current_course].append(text)

        return {k: '\n'.join(v) for k, v in sections.items()}

    def extract_forum_topics(self, html):
        """解析 phpBB forum 頁面，回傳 {主題標題: 連結} 的 dict"""
        return {title: meta['url'] for title, meta in self.extract_forum_topics_with_meta(html).items()}

    def extract_forum_topics_with_meta(self, html):
        """解析 phpBB forum 頁面，回傳 {主題標題: {url, replies, last_datetime}} 的 dict"""
        from urllib.parse import urlparse, urljoin
        soup = BeautifulSoup(html, 'html.parser')
        parsed = urlparse(self.url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        topics = {}
        for li in soup.find_all('li', class_='row'):
            a = li.find('a', class_='topictitle')
            if not a:
                continue
            title = a.get_text(strip=True)
            href = urljoin(base + '/forum/', a.get('href', ''))

            replies = 0
            dd_posts = li.find('dd', class_='posts')
            if dd_posts:
                m = re.search(r'(\d+)', dd_posts.get_text())
                if m:
                    replies = int(m.group(1))

            last_datetime = ''
            dd_lastpost = li.find('dd', class_='lastpost')
            if dd_lastpost:
                t = dd_lastpost.find('time')
                if t:
                    last_datetime = t.get('datetime', '')

            if title:
                topics[title] = {
                    'url': href,
                    'replies': replies,
                    'last_datetime': last_datetime,
                }
        return topics

    def get_forum_topic_changes(self, old_html, new_html):
        """比對新舊 forum 頁面，回傳 (新增主題, 消失主題, 有新回覆主題) 三個 list。
        新增/消失：每筆為 (title, url)。
        有新回覆：每筆為 (title, url, old_meta, new_meta)。"""
        old_topics = self.extract_forum_topics_with_meta(old_html)
        new_topics = self.extract_forum_topics_with_meta(new_html)

        added   = [(t, new_topics[t]['url']) for t in new_topics if t not in old_topics]
        removed = [(t, old_topics[t]['url']) for t in old_topics if t not in new_topics]
        updated = []
        for t in new_topics:
            if t not in old_topics:
                continue
            old_m = old_topics[t]
            new_m = new_topics[t]
            if old_m['last_datetime'] != new_m['last_datetime'] or old_m['replies'] != new_m['replies']:
                updated.append((t, new_m['url'], old_m, new_m))
        return added, removed, updated

    def send_email_notification(self, subject, body):
        """發送 Email 通知"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        sender = os.getenv('EMAIL_SENDER')
        receiver = os.getenv('EMAIL_RECEIVER')
        password = os.getenv('EMAIL_PASSWORD')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '465'))

        if not all([sender, receiver, password]):
            print("Email 通知未設定，跳過發送")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = receiver

            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)

            # HTML 版：將 diff 的 +/- 行用顏色標示
            html_body_lines = []
            for line in body.splitlines():
                if line.startswith('+'):
                    html_body_lines.append(f'<span style="color:#2e7d32;background:#e8f5e9">{line}</span>')
                elif line.startswith('-'):
                    html_body_lines.append(f'<span style="color:#c62828;background:#ffebee">{line}</span>')
                else:
                    html_body_lines.append(line)
            html_body_content = '<br>'.join(html_body_lines)

            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #ff6b6b;">⚠️ 課程網頁更新通知</h2>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                  <pre style="white-space: pre-wrap; word-wrap: break-word; font-size: 13px;">{html_body_content}</pre>
                </div>
                <hr>
                <p style="color: #666; font-size: 12px;">這是自動發送的通知郵件，請勿直接回覆。</p>
              </body>
            </html>
            """
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)

            if smtp_port == 587:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(sender, password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
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

    def _load_login_fail_count(self):
        """讀取連續登入失敗次數"""
        fail_file = f"/data/{self.data_prefix}_login_fail.json"
        if os.path.exists(fail_file):
            with open(fail_file, 'r') as f:
                return json.load(f).get('consecutive_fails', 0)
        return 0

    def _save_login_fail_count(self, count):
        """儲存連續登入失敗次數"""
        fail_file = f"/data/{self.data_prefix}_login_fail.json"
        os.makedirs(os.path.dirname(fail_file), exist_ok=True)
        with open(fail_file, 'w') as f:
            json.dump({
                'consecutive_fails': count,
                'last_fail': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }, f, indent=2)

    def _reset_login_fail_count(self):
        """登入成功後重置失敗計數"""
        fail_file = f"/data/{self.data_prefix}_login_fail.json"
        if os.path.exists(fail_file):
            os.remove(fail_file)

    def check_updates(self):
        """檢查網頁是否有更新"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 開始檢查網頁...")

        if not self.login():
            print("登入失敗！")
            fails = self._load_login_fail_count() + 1
            self._save_login_fail_count(fails)
            print(f"連續登入失敗 {fails} 次。")
            if fails >= 2:
                self.send_email_notification(
                    subject=f"⚠️ [{self.url}] 連續登入失敗 {fails} 次",
                    body=(
                        f"⚠️ 爬蟲連續登入失敗 {fails} 次！\n"
                        f"📅 最後失敗時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"🔗 網址：{self.url}\n\n"
                        f"請確認帳號密碼是否正確，或是否被封鎖。"
                    ),
                )
            return

        self._reset_login_fail_count()

        content = self.get_page_content()
        if not content:
            return

        soup = BeautifulSoup(content, 'html.parser')
        page_title = soup.title.string.strip() if soup.title else self.url

        new_hash = self.calculate_hash(content)
        old_hash, last_check, old_snapshot = self.load_previous_hash()

        current_file = self.save_page_content(content)

        if old_hash is None:
            print("首次檢查，儲存初始哈希值。")
            self.save_hash(new_hash, current_file)
        elif old_hash != new_hash:
            print("⚠️ 網頁有更新！")
            print(f"上次檢查: {last_check}")
            self.save_hash(new_hash, current_file)

            old_content = self.get_previous_snapshot(old_snapshot)
            login_type = os.getenv('LOGIN_TYPE', 'basic')

            header = (
                f"⚠️ 網頁已更新！\n"
                f"📅 更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🔗 網址：{self.url}\n"
                f"📊 上次檢查：{last_check}\n"
            )

            if login_type == 'phpbb':
                # Forum 模式：比對主題標題與回覆數
                new_topics_meta = self.extract_forum_topics_with_meta(content)

                # 若頁面上取不到任何主題，可能是登入失效
                if not new_topics_meta:
                    old_topics_meta = self.extract_forum_topics_with_meta(old_content) if old_content else {}
                    if not old_topics_meta:
                        # 新舊都沒有主題（例如 CSRF token 更換造成的雜訊），靜默更新 hash 不發通知
                        print("⚠️ 頁面有更新但新舊快照均無法解析主題（可能為 CSRF token 變動），略過通知。")
                        return
                    subject = f"⚠️ [編譯器製作論壇] 無法取得主題列表（登入可能已失效）"
                    notification_message = header + "\n⚠️ 無法從頁面取得主題列表，請確認登入狀態是否正常。\n"
                else:
                    added, removed, updated = self.get_forum_topic_changes(old_content, content) if old_content else ([], [], [])

                    topic_body = ""
                    if added:
                        topic_body += "\n【新增主題】\n"
                        for title, url in added:
                            topic_body += f"  ➕ {title}\n     {url}\n"
                    if removed:
                        topic_body += "\n【消失主題】\n"
                        for title, url in removed:
                            topic_body += f"  ➖ {title}\n"
                    if updated:
                        topic_body += "\n【有新回覆的主題】\n"
                        for title, url, old_m, new_m in updated:
                            reply_diff = ""
                            if old_m['replies'] != new_m['replies']:
                                reply_diff = f"（回覆數：{old_m['replies']} → {new_m['replies']}）"
                            topic_body += f"  🔄 {title}{reply_diff}\n     {url}\n"

                    if added or removed or updated:
                        titles = [t for t, _ in added] + [t for t, _ in removed] + [t for t, _, _, _ in updated]
                        print(f"主題變動：{', '.join(titles)}")
                        subject = f"🔔 [編譯器製作論壇] 主題更新"
                        notification_message = header + topic_body
                    else:
                        subject = f"🔔 [編譯器製作論壇] 頁面更新通知"
                        notification_message = header + "\n（頁面有更新但主題列表無明顯變動）\n"
            else:
                # 課程頁面模式：比對課程區段
                changes = self.get_changed_sections(old_content, content) if old_content else []

                if changes:
                    changed_course_names = [c for c, _, _ in changes]
                    print(f"變動課程：{', '.join(changed_course_names)}")
                    subject = f"🔔 [{', '.join(changed_course_names)}] 課程網頁更新"

                    diff_body = ""
                    for course, diff_lines, pseudo_only in changes:
                        if pseudo_only:
                            diff_body += f"\n{'='*40}\n📚 {course}  ⚠️ [偽標籤更動，瀏覽器不可見]\n{'='*40}\n"
                        else:
                            diff_body += f"\n{'='*40}\n📚 {course}\n{'='*40}\n"
                        diff_body += '\n'.join(diff_lines)
                        diff_body += '\n'

                    notification_message = header + diff_body
                else:
                    subject = f"🔔 [{page_title}] 課程網頁更新通知"
                    notification_message = header

            email_sent = self.send_email_notification(subject=subject, body=notification_message)
            if not email_sent:
                self.send_line_notification(notification_message)
        else:
            # hash 不變，但更新快照路徑指向最新檔案
            self.save_hash(old_hash, current_file)
            print("✓ 網頁沒有變更。")
            print(f"上次檢查: {last_check}")

def main():
    username = os.getenv('WEB_USERNAME', '')
    password = os.getenv('WEB_PASSWORD', '')
    url = os.getenv('WEB_URL', 'https://www.cs.ccu.edu.tw/~damon/secure/course-wk.html')
    data_prefix = os.getenv('DATA_PREFIX', 'page')

    monitor = WebsiteMonitor(username, password, url, data_prefix)
    monitor.check_updates()

if __name__ == "__main__":
    main()
