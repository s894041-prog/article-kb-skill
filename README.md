# 個人文章知識庫建立指南

把你散落在 Facebook、痞客邦、GPT 對話裡的文章，整理成結構化的 Markdown 知識庫，讓 AI 可以查詢、分析你的過去。

---

## 需要準備什麼

- Facebook 貼文匯出（設定 → 下載你的資訊 → 選「貼文」→ JSON 格式）
- 痞客邦文章（用爬蟲腳本或手動備份）
- GPT 對話紀錄（ChatGPT 設定 → 資料控制 → 匯出資料）
- Python 3
- iCloud 或任何雲端儲存

---

## 資料夾結構

```
KB/
├── MD/                    ← 整理好的 Markdown
│   ├── 決策框架.md        ← 核心文件
│   ├── GPT對話索引.md
│   └── 文章/
│       ├── Facebook/
│       ├── 痞客邦/
│       └── GPT/
├── RAW/                   ← 原始匯出檔
│   ├── scrape_pixnet.py
│   ├── parse_gpt.py
│   └── 文章/
```

---

## Step 1：匯出原始資料

**Facebook**
下載 JSON 格式的貼文匯出，放進 `RAW/文章/Facebook/`

**痞客邦**
```bash
python3 scrape_pixnet.py
```

**GPT 對話**
```bash
python3 parse_gpt.py
```

---

## Step 2：轉換成 Markdown

每篇文章的標準格式：

```markdown
# 文章標題

**日期：** YYYY-MM-DD
**來源：** Facebook / 痞客邦 / ChatGPT
**標籤：** #標籤1 #標籤2

---

文章內容
```

命名規則：
- Facebook：`YYYY-MM-DD-標題開頭.md`
- 痞客邦：`YYYY-MM-DD_標題.md`
- GPT：`YYYY-MM-DD-主題.md`

---

## Step 3：建立兩份核心索引

**1. 個人決策框架**
把所有文章丟給 Claude，請它幫你整理出：你是誰、重複模式、警告信號、核心價值、決策檢查清單。

**2. GPT 對話索引**
依主題分類所有 GPT 對話：個人成長、家庭溝通、子女、健康、教學、財務、AI工具、旅遊、雜項。

---

## Step 4：日常使用

每次對話把決策框架丟給 Claude：
> 「這是我的個人框架，請閱讀後幫我分析：[你的問題]」

---

## 維護頻率

| 頻率 | 動作 |
|------|------|
| 每次寫新文章 | 存進對應資料夾 |
| 每個月 | 更新 GPT 對話索引 |
| 每三個月 | 更新決策框架 |
| 重大事件後 | 立即補充框架 |

---

## 相關腳本

- `scrape_pixnet.py`：痞客邦爬蟲
- `parse_gpt.py`：GPT 對話解析器
