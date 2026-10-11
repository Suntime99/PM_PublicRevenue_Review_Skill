# -*- coding: utf-8 -*-
"""
省级法规库合规采集工具
=====================================
从各省"法规规章规范性文件数据库"（省人大/司法厅建设）采集地方性法规完整全文。

已验证：湖南省法规库（chat.hnzhrd.gov.cn）流程：
  1. 打开法规库首页
  2. 设置桌面视口（响应式布局需要）
  3. 输入关键词搜索
  4. 点击搜索结果卡片（打开新标签页详情）
  5. 详情页获取 lawDetail API → 提取 docx 下载地址
  6. 下载 docx 并解析全文

用法：
  python tools/provincial_law_fetcher.py \
      --db-url "https://chat.hnzhrd.gov.cn:82/sub/legalDatabase/#/index" \
      --keyword "物业管理条例" \
      --output "database/provincial/hunan/湖南省物业管理条例"

依赖：
  pip install cdpwave pywin32
"""
import argparse
import json
import os
import re
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from cdpwave.sync import SyncCDPClient

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def extract_docx_text(docx_path):
    """从docx提取纯文本（无外部依赖）"""
    with zipfile.ZipFile(docx_path) as z:
        xml_content = z.read('word/document.xml')
        tree = ET.fromstring(xml_content)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        texts = []
        for p in tree.findall('.//w:p', ns):
            line = ''.join(t.text for t in p.findall('.//w:t', ns) if t.text)
            if line.strip():
                texts.append(line.strip())
        return '\n'.join(texts)


def search_and_open_detail(client, db_url, keyword, timeout=30):
    """
    在法规库中搜索关键词并打开第一个匹配的详情页
    返回：详情页URL 或 None
    """
    with client.new_page(db_url) as page:
        page.wait_for_load_state("load", timeout=timeout * 1000)
        time.sleep(8)

        # 设置桌面视口（很多法规库是响应式，窄视口会隐藏列表）
        try:
            page.send('Emulation.setDeviceMetricsOverride', {
                'width': 1280, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False
            })
            time.sleep(2)
        except Exception:
            pass

        # 查找可见搜索框（通常是第二个 input[placeholder*="搜索"]）
        js_find = """
        (() => {
            const inputs = document.querySelectorAll('input');
            for (let i = 0; i < inputs.length; i++) {
                const rect = inputs[i].getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && (inputs[i].placeholder || '').includes('搜索')) {
                    return {index: i, x: rect.x + rect.width / 2, y: rect.y + rect.height / 2};
                }
            }
            return null;
        })()
        """
        r = page.runtime.evaluate(js_find, return_by_value=True)
        pos = r.get('result', {}).get('value')

        if not pos:
            print("  ⚠️ 未找到可见搜索框")
            return None

        # 点击搜索框
        page.input.dispatch_mouse_event('mousePressed', x=pos['x'], y=pos['y'], button='left', click_count=1)
        page.input.dispatch_mouse_event('mouseReleased', x=pos['x'], y=pos['y'], button='left', click_count=1)
        time.sleep(1)
        page.input.insert_text(keyword)
        time.sleep(1)
        page.input.dispatch_key_event('keyDown', key='Enter', code='Enter', windows_virtual_key_code=13)
        page.input.dispatch_key_event('keyUp', key='Enter', code='Enter', windows_virtual_key_code=13)
        time.sleep(5)

        # 点击搜索按钮（如果存在）
        js_btn = """
        (() => {
            const btns = document.querySelectorAll('button');
            for (const b of btns) {
                const cls = (b.className || '').toString();
                const text = (b.innerText || '').trim();
                if (text === '搜索' && (cls.includes('primary') || cls.includes('search'))) {
                    b.click();
                    return 'clicked';
                }
            }
            return 'NOT_FOUND';
        })()
        """
        r2 = page.runtime.evaluate(js_btn, return_by_value=True)
        if r2.get('result', {}).get('value', '') == 'clicked':
            time.sleep(8)
        else:
            time.sleep(5)

        # 查找搜索结果中匹配的卡片（含关键词的 div，可点击）
        js_card = """
        (() => {
            const cards = document.querySelectorAll('div[class*="cursor-pointer"], div[class*="hover:bg"]');
            for (const card of cards) {
                const text = card.innerText || '';
                if (text.includes(KEYWORD) && text.length < 200) {
                    card.scrollIntoView({block: 'center'});
                    const rect = card.getBoundingClientRect();
                    if (rect.width > 0) {
                        return {x: rect.x + rect.width / 2, y: rect.y + rect.height / 2};
                    }
                }
            }
            return null;
        })()
        """.replace('KEYWORD', keyword)
        r3 = page.runtime.evaluate(js_card, return_by_value=True)
        card_pos = r3.get('result', {}).get('value')

        if not card_pos:
            print("  ⚠️ 未找到匹配的法规卡片")
            return None

        # 点击卡片（打开新标签页）
        page.input.dispatch_mouse_event('mousePressed', x=card_pos['x'], y=card_pos['y'], button='left', click_count=1)
        page.input.dispatch_mouse_event('mouseReleased', x=card_pos['x'], y=card_pos['y'], button='left', click_count=1)
        time.sleep(10)

        # 获取新标签页URL
        try:
            targets = client.send('Target.getTargets')
            for t in targets.get('targetInfos', []):
                url = t.get('url', '')
                if url and 'details' in url and t.get('type') == 'page':
                    return url
        except Exception:
            pass

        return None


def fetch_law_from_detail(client, detail_url, keyword):
    """
    从详情页获取法规元数据 + docx 下载地址
    返回: (metadata_dict, download_url) 或 (None, None)
    """
    import urllib.parse
    # 提取id
    m = re.search(r'id=(\d+)', detail_url)
    if not m:
        return None, None
    law_id = m.group(1)

    with client.new_page(detail_url) as page:
        page.wait_for_load_state("load", timeout=30000)
        time.sleep(10)

        # 调用 lawDetail 接口
        js = """
        (async () => {
            const resp = await fetch('/service-law/biz/lawrecordreviewreportregulations/lawDetail?id=LAW_ID');
            return await resp.text();
        })()
        """.replace('LAW_ID', law_id)
        r = page.runtime.evaluate(js, await_promise=True, return_by_value=True)
        resp_text = r.get('result', {}).get('value', '')

        if not resp_text:
            return None, None

        data = json.loads(resp_text)
        law = data.get('data', {})
        file_ids = law.get('fileIds', [])
        if not file_ids:
            return None, None

        # 提取docx下载信息
        file_info = file_ids[0]
        download_url = file_info.get('fileUrl', '')
        if download_url and not download_url.startswith('http'):
            download_url = 'https://chat.hnzhrd.gov.cn:82' + download_url

        metadata = {
            'title': law.get('title', keyword),
            'region': law.get('regionName', ''),
            'authority': law.get('formulationAuthorityName', ''),
            'published': law.get('publishedTime', ''),
            'implemented': law.get('implementationTime', ''),
            'validity': law.get('validity', ''),
            'fileType': law.get('fileTypeNewName', ''),
            'fileName': file_info.get('fileName', ''),
        }
        return metadata, download_url


def main():
    parser = argparse.ArgumentParser(description='省级法规库合规采集工具')
    parser.add_argument('--db-url', required=True, help='法规库URL')
    parser.add_argument('--keyword', required=True, help='搜索关键词')
    parser.add_argument('--output', required=True, help='输出路径前缀（不含扩展名）')
    parser.add_argument('--timeout', type=int, default=30, help='页面加载超时秒数')
    args = parser.parse_args()

    with SyncCDPClient.launch(headless=True, browser_path=EDGE_PATH) as client:
        print(f"=== 搜索 '{args.keyword}' ===")
        detail_url = search_and_open_detail(client, args.db_url, args.keyword, args.timeout)
        if not detail_url:
            print("❌ 未找到详情页")
            sys.exit(1)
        print(f"详情页: {detail_url}")

        print("\n=== 获取法规元数据和下载链接 ===")
        metadata, download_url = fetch_law_from_detail(client, detail_url, args.keyword)
        if not metadata or not download_url:
            print("❌ 无法获取法规文件")
            sys.exit(1)
        print(f"标题: {metadata['title']}")
        print(f"制定机关: {metadata['authority']}")
        print(f"发布日期: {metadata['published']}")
        print(f"文件: {metadata['fileName']}")

        print("\n=== 下载docx并解析 ===")
        req = urllib.request.Request(download_url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': detail_url
        })
        resp = urllib.request.urlopen(req, timeout=120)
        data = resp.read()

        if not data.startswith(b'PK'):
            print("❌ 下载内容不是docx")
            sys.exit(1)

        docx_path = f"{args.output}_原文件.docx"
        with open(docx_path, 'wb') as f:
            f.write(data)
        print(f"已保存: {docx_path} ({len(data)} 字节)")

        text = extract_docx_text(docx_path)
        header = f"""# {metadata['title']}（全文·完整版）

- **来源**: {args.db_url.split('/')[2]} 法规库
- **制定机关**: {metadata['authority']}
- **发布日期**: {metadata['published']}
- **实施日期**: {metadata['implemented'] or '未标注'}
- **时效性**: {'✅ 有效' if metadata['validity'] == 'valid' else metadata['validity']}
- **效力层级**: {metadata['fileType']}

---

"""
        txt_path = f"{args.output}_全文_完整版.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(header + text)
        print(f"已保存: {txt_path} ({len(text)} 字符)")


if __name__ == '__main__':
    main()