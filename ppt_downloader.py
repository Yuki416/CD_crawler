#!/usr/bin/env python3
"""
編譯器設計課程講義下載器
自動偵測課程頁面中的新增或更新講義，並下載到 ppt/ 資料夾。
"""
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import hashlib
import json
import os
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

# 下載的目標課程關鍵字（可擴充）
TARGET_COURSE_KEYWORDS = ['編譯器製作', '編譯器設計', 'compiler design', 'compiler', 'CD']
DOWNLOADABLE_EXTENSIONS = {'.pdf', '.ppt', '.pptx', '.doc', '.docx', '.zip'}
# 只下載 URL 路徑包含此關鍵字的檔案，避免抓到其他課程的連結
URL_PATH_FILTER = 'compile'

MANIFEST_FILE = os.environ.get('PPT_MANIFEST_FILE', '/data/ppt_manifest.json')
PPT_DIR = os.environ.get('PPT_DIR', '/app/ppt')


def load_manifest():
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_manifest(manifest):
    os.makedirs(os.path.dirname(MANIFEST_FILE), exist_ok=True)
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def is_target_course(section_name):
    name_lower = section_name.lower()
    return any(kw.lower() in name_lower for kw in TARGET_COURSE_KEYWORDS)


def extract_links_from_section(html, base_url):
    """從整個 HTML 中找到目標課程區段，並回傳其中的可下載連結。"""
    section_marker = re.compile(r'<!\*{5,}([^*>\n]+)\*{5,}>')
    markers = list(section_marker.finditer(html))

    target_sections = []
    for i, match in enumerate(markers):
        name = match.group(1).strip()
        if is_target_course(name):
            start = match.end()
            end = markers[i + 1].start() if i + 1 < len(markers) else len(html)
            target_sections.append((name, html[start:end]))

    if not target_sections:
        print(f"⚠️  找不到目標課程區段（已搜尋關鍵字：{TARGET_COURSE_KEYWORDS}）")
        return []

    seen_urls = set()
    links = []
    for course_name, section_html in target_sections:
        soup = BeautifulSoup(section_html, 'html.parser')
        section_links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href'].strip()
            ext = os.path.splitext(urlparse(href).path)[1].lower()
            if ext in DOWNLOADABLE_EXTENSIONS:
                full_url = urljoin(base_url, href)
                if URL_PATH_FILTER not in urlparse(full_url).path:
                    continue
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                link_text = a_tag.get_text(strip=True) or os.path.basename(href)
                section_links.append({
                    'url': full_url,
                    'text': link_text,
                    'course': course_name,
                    'filename': os.path.basename(urlparse(href).path),
                })
        links.extend(section_links)

    print(f"  📚 找到 {len(links)} 個可下載連結（已去重）")
    return links


def download_file(session, url, dest_path):
    resp = session.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)


def run():
    username = os.getenv('WEB_USERNAME')
    password = os.getenv('WEB_PASSWORD')
    url = os.getenv('WEB_URL', 'https://www.cs.ccu.edu.tw/~damon/secure/course-wk.html')

    if not username or not password:
        print("❌ 請設定 WEB_USERNAME 和 WEB_PASSWORD 環境變數")
        return

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 開始檢查講義更新...")

    session = requests.Session()

    # 登入
    resp = session.get(url, timeout=30)
    if resp.status_code == 401:
        session.auth = HTTPBasicAuth(username, password)
        resp = session.get(url, timeout=30)
    if resp.status_code != 200:
        print(f"❌ 無法取得課程頁面，狀態碼：{resp.status_code}")
        return

    html = resp.text
    base_url = url.rsplit('/', 1)[0] + '/'

    links = extract_links_from_section(html, base_url)
    if not links:
        return

    manifest = load_manifest()
    new_count = 0
    updated_count = 0

    for link in links:
        filename = link['filename']
        dest_path = os.path.join(PPT_DIR, filename)
        url_key = link['url']

        # 先用 HEAD 取得遠端 Last-Modified 和 Content-Length
        try:
            head = session.head(link['url'], timeout=15)
            remote_last_modified = head.headers.get('Last-Modified', '')
            remote_content_length = head.headers.get('Content-Length', '')
        except Exception as e:
            print(f"  ⚠️  HEAD 請求失敗 {filename}: {e}")
            remote_last_modified = ''
            remote_content_length = ''

        prev = manifest.get(url_key, {})
        need_download = False

        if not os.path.exists(dest_path):
            print(f"  🆕 新講義：{filename}")
            need_download = True
        elif (remote_last_modified and remote_last_modified != prev.get('last_modified')) or \
             (remote_content_length and remote_content_length != prev.get('content_length')):
            print(f"  🔄 講義已更新：{filename}")
            need_download = True
            updated_count += 1 if not need_download else 0  # counted below

        if need_download:
            try:
                download_file(session, link['url'], dest_path)
                local_hash = file_hash(dest_path)
                manifest[url_key] = {
                    'filename': filename,
                    'course': link['course'],
                    'text': link['text'],
                    'last_modified': remote_last_modified,
                    'content_length': remote_content_length,
                    'local_hash': local_hash,
                    'downloaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }
                save_manifest(manifest)
                if not os.path.exists(dest_path) or prev == {}:
                    new_count += 1
                else:
                    updated_count += 1
                print(f"  ✅ 已下載：{dest_path}")
            except Exception as e:
                print(f"  ❌ 下載失敗 {filename}: {e}")
        else:
            print(f"  ✓ 無變更：{filename}")

    print(f"完成。新增 {new_count} 份，更新 {updated_count} 份。")


if __name__ == '__main__':
    run()
