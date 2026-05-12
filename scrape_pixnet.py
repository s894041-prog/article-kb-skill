#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬取 jhz0718.pixnet.net/blog 所有文章
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://jhz0718.pixnet.net/blog"
OUTPUT_DIR = "/Users/tsai/Documents/KB/RAW/文章"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}

def sanitize_filename(name):
    """清理檔名中的非法字符"""
    name = re.sub(r'[\\/*?:"<>|]', '', name)
    name = name.replace('\n', '').replace('\r', '').strip()
    name = name.replace('/', '-').replace('\\', '-')
    return name[:80] if len(name) > 80 else name

def get_page(url, retries=3):
    """取得網頁內容"""
    for i in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code == 200:
                return resp.content.decode('utf-8')
            print(f"  HTTP {resp.status_code} for {url}")
        except Exception as e:
            print(f"  錯誤 (嘗試 {i+1}/{retries}): {e}")
            time.sleep(2)
    return None

def get_article_links_from_page(page_num):
    """從列表頁取得所有文章連結"""
    url = f"{BASE_URL}?page={page_num}"
    print(f"\n[列表頁 {page_num}] 讀取: {url}")
    html = get_page(url)
    if not html:
        print(f"  列表頁 {page_num} 讀取失敗")
        return []

    # 用 regex 找 /blog/posts/ 格式的連結
    links = set(re.findall(
        r'https?://jhz0718\.pixnet\.net/blog/posts/\d+',
        html
    ))

    print(f"  找到 {len(links)} 篇文章連結")
    return list(links)

def extract_article(url):
    """抓取單篇文章內容"""
    html = get_page(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'lxml')

    # 標題：優先用 .title class，再試其他
    title = None
    for selector in ['.title', 'h1.article-title', 'h2.article-title',
                     '.article-title h2', '.article-title h1',
                     '.article-title', 'h2', 'h1']:
        el = soup.select_one(selector)
        if el:
            t = el.get_text(strip=True)
            # 排除網站名稱等無效標題
            if t and t not in ['Chi-i Tsai的部落格', '歡迎光臨Chi-i Tsai在痞客邦的小天地', '你可能也喜歡']:
                title = t
                break

    if not title:
        meta = soup.find('meta', property='og:title')
        if meta:
            title = meta.get('content', '').strip()

    # 日期：優先用 og:article:published_time
    parsed_date = '未知日期'
    for prop in ['og:article:published_time', 'article:published_time',
                 'og:article:modified_time', 'og:updated_time']:
        meta = soup.find('meta', property=prop)
        if meta and meta.get('content'):
            date_str = meta['content']
            m = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
            if m:
                parsed_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                break

    # 備用：從 HTML 中找 ISO 日期
    if parsed_date == '未知日期':
        iso_dates = re.findall(r'(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}:\d{2}', html)
        if iso_dates:
            parsed_date = iso_dates[0]

    # 文章內文
    content_text = ''
    for selector in ['.article-content-inner', '.article-content',
                     '.article-body', '#article-content', '.post-content']:
        el = soup.select_one(selector)
        if el and el.get_text(strip=True):
            # 移除不必要的標籤
            for tag in el.find_all(['script', 'style', 'iframe', 'form']):
                tag.decompose()
            content_text = el.get_text('\n', strip=True)
            # 清理多餘空行
            content_text = re.sub(r'\n{3,}', '\n\n', content_text)
            break

    if not content_text:
        content_text = '（無法提取內文）'

    return {
        'title': title or '無標題',
        'date': parsed_date,
        'url': url,
        'content': content_text,
    }

def save_article(article):
    """儲存文章為 .md 檔"""
    title = sanitize_filename(article['title'])
    date = article['date']
    filename = f"{date}_{title}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    md_content = f"""# {article['title']}

**日期：** {date}
**來源：** {article['url']}

---

{article['content']}
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)

    return filename

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_links = []
    seen = set()

    # 第一步：收集所有文章連結
    print("=" * 60)
    print("步驟 1: 收集所有文章連結")
    print("=" * 60)

    for page in range(1, 12):
        links = get_article_links_from_page(page)
        for link in links:
            if link not in seen:
                seen.add(link)
                all_links.append(link)
        time.sleep(1.5)

    print(f"\n共找到 {len(all_links)} 篇不重複文章")

    # 第二步：逐一抓取文章
    print("\n" + "=" * 60)
    print("步驟 2: 抓取文章內容")
    print("=" * 60)

    success = []
    failed = []

    for i, url in enumerate(all_links, 1):
        print(f"\n[{i}/{len(all_links)}] {url}")
        try:
            article = extract_article(url)
            if article:
                filename = save_article(article)
                print(f"  OK 已儲存: {filename}")
                success.append(filename)
            else:
                print(f"  FAIL 抓取失敗（無內容）")
                failed.append(url)
        except Exception as e:
            print(f"  FAIL 例外錯誤: {e}")
            failed.append(url)

        time.sleep(1.5)

    # 最終報告
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
    print(f"成功: {len(success)} 篇")
    print(f"失敗: {len(failed)} 篇")
    print("\n--- 成功的檔案清單 ---")
    for f in sorted(success):
        print(f"  {f}")
    if failed:
        print("\n--- 失敗的 URL ---")
        for u in failed:
            print(f"  {u}")

if __name__ == '__main__':
    main()
