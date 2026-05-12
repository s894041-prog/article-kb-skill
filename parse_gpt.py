#!/usr/bin/env python3
"""Parse ChatGPT HTML export and convert conversations to Markdown."""

import json
import re
import os
from datetime import datetime, timezone

INPUT_HTML = "/Users/tsai/Library/Mobile Documents/com~apple~CloudDocs/KB/RAW/文章/1141226gpt匯出/chat.html"
OUTPUT_DIR = "/Users/tsai/Library/Mobile Documents/com~apple~CloudDocs/KB/MD/文章/GPT"

def extract_json(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    marker = "var jsonData = "
    idx = content.find(marker)
    if idx == -1:
        raise ValueError("Cannot find jsonData in HTML")
    start = idx + len(marker)
    decoder = json.JSONDecoder()
    data, _ = decoder.raw_decode(content, start)
    return data

def get_thread(mapping):
    """Return ordered list of (role, text, ts) for the main conversation thread."""
    # Find root: node whose parent is null
    root_id = None
    for nid, node in mapping.items():
        if node.get("parent") is None:
            root_id = nid
            break
    if root_id is None:
        return []

    messages = []
    current_id = root_id
    visited = set()

    while current_id and current_id not in visited:
        visited.add(current_id)
        node = mapping.get(current_id)
        if not node:
            break

        msg = node.get("message")
        if msg:
            role = msg.get("author", {}).get("role", "")
            ts = msg.get("create_time")
            content = msg.get("content", {})
            ctype = content.get("content_type", "")
            parts = content.get("parts", [])

            if role in ("user", "assistant") and parts:
                text_parts = []
                for p in parts:
                    if isinstance(p, str) and p.strip():
                        text_parts.append(p.strip())
                    elif isinstance(p, dict):
                        # image or other content
                        if p.get("content_type") == "image_asset_pointer":
                            text_parts.append("[圖片]")
                        elif p.get("content_type") == "audio_transcription":
                            t = p.get("text", "")
                            if t:
                                text_parts.append(t)
                text = "\n".join(text_parts)
                if text:
                    messages.append((role, text, ts))

        # Follow first child (main branch)
        children = node.get("children", [])
        current_id = children[0] if children else None

    return messages

def ts_to_date(ts):
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")

def sanitize_filename(s):
    s = re.sub(r'[<>:"/\\|?*\n\r\t]', '', s)
    s = s.strip()
    return s[:60] if len(s) > 60 else s

def conversation_to_md(conv):
    title = conv.get("title", "無標題")
    create_time = conv.get("create_time")
    date_str = ts_to_date(create_time) or "未知日期"

    mapping = conv.get("mapping", {})
    thread = get_thread(mapping)

    if not thread:
        return None, None, None

    lines = [
        f"# {title}",
        f"日期：{date_str}",
        f"來源：ChatGPT",
        "",
        "## 內容",
        "",
    ]

    for role, text, ts in thread:
        if role == "user":
            lines.append(f"**User：** {text}")
        else:
            lines.append(f"**GPT：** {text}")
        lines.append("")

    lines += ["## 標籤", "#待補", ""]

    filename = f"{date_str}-{sanitize_filename(title)}.md"
    return filename, date_str, "\n".join(lines)

def main():
    print("讀取 chat.html...")
    conversations = extract_json(INPUT_HTML)
    print(f"找到 {len(conversations)} 個對話")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    success = 0
    skipped = 0
    seen_names = {}

    for conv in conversations:
        filename, date_str, md_content = conversation_to_md(conv)
        if not filename or not md_content:
            skipped += 1
            continue

        # Handle duplicate filenames
        if filename in seen_names:
            seen_names[filename] += 1
            base, ext = os.path.splitext(filename)
            filename = f"{base}-{seen_names[filename]}{ext}"
        else:
            seen_names[filename] = 0

        out_path = os.path.join(OUTPUT_DIR, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        success += 1

    print(f"完成：{success} 個對話已輸出，{skipped} 個跳過（無內容）")
    print(f"輸出位置：{OUTPUT_DIR}")

if __name__ == "__main__":
    main()
