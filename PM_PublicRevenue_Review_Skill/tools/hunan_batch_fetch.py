# -*- coding: utf-8 -*-
"""批量从湖南省法规库采集物业管理相关法规（修复标签页复用问题）"""
import sys
import time
import json
import re
import os
import zipfile
import xml.etree.ElementTree as ET
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from cdpwave.sync import SyncCDPClient

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DB_URL = "https://chat.hnzhrd.gov.cn:82/sub/legalDatabase/#/index"

LAWS = [
    {
        "keyword": "岳阳市住宅物业管理若干规定",
        "output": "database/municipal/岳阳市住宅物业管理若干规定",
    },
]


def extract_docx_text(docx_path):
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


def fetch_one_law(client, law):
    keyword = law["keyword"]
    output = law["output"]
    print(f"\n=== 采集: {keyword} ===")

    with client.new_page(DB_URL) as page:
        page.wait_for_load_state("load", timeout=30000)
        time.sleep(8)
        page.send('Emulation.setDeviceMetricsOverride', {
            'width': 1280, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False
        })
        time.sleep(2)

        # 搜索
        js = """
        (() => {
            const inputs = document.querySelectorAll('input');
            const target = inputs[1];
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            nativeSetter.call(target, '""" + keyword + """');
            target.dispatchEvent(new Event('input', {bubbles: true}));
            return 'SET';
        })()
        """
        page.runtime.evaluate(js, return_by_value=True)
        time.sleep(1)
        js2 = """
        (() => {
            const btns = document.querySelectorAll('button');
            for (const b of btns) {
                if (b.innerText.trim() === '搜索' && b.className.includes('ant-btn-primary')) {
                    b.click(); return 'clicked';
                }
            }
            return 'NOT_FOUND';
        })()
        """
        page.runtime.evaluate(js2, return_by_value=True)
        time.sleep(8)

        # 定位卡片
        js3 = """
        (() => {
            const cards = document.querySelectorAll('div[class*="hover:bg-gray-50"]');
            for (const card of cards) {
                const text = card.innerText || '';
                if (text.includes('KEYWORD')) {
                    card.scrollIntoView({block: 'center'});
                    const rect = card.getBoundingClientRect();
                    if (rect.width > 0) {
                        return {x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, text: text.substring(0, 150)};
                    }
                }
            }
            return null;
        })()
        """.replace('KEYWORD', keyword)
        r = page.runtime.evaluate(js3, return_by_value=True)
        pos = r.get('result', {}).get('value')
        if not pos:
            print("  ❌ 未找到卡片")
            return False
        print(f"  卡片: {pos.get('text', '')[:100]}")

        # 记录点击前的标签页
        try:
            targets_before = client.send('Target.getTargets')
            before_ids = {t.get('targetId') for t in targets_before.get('targetInfos', []) if t.get('type') == 'page'}
        except Exception:
            before_ids = set()

        # 点击卡片
        page.input.dispatch_mouse_event('mousePressed', x=pos['x'], y=pos['y'], button='left', click_count=1)
        page.input.dispatch_mouse_event('mouseReleased', x=pos['x'], y=pos['y'], button='left', click_count=1)
        time.sleep(10)

        # 查找新打开的详情标签页
        detail_url = None
        try:
            targets = client.send('Target.getTargets')
            for t in targets.get('targetInfos', []):
                if t.get('type') == 'page':
                    url = t.get('url', '')
                    tid = t.get('targetId', '')
                    if 'details' in url and tid not in before_ids:
                        detail_url = url
                        break
            # 兜底：如果没有新标签，找所有含details的标签
            if not detail_url:
                for t in targets.get('targetInfos', []):
                    if t.get('type') == 'page' and 'details' in t.get('url', ''):
                        detail_url = t.get('url', '')
                        break
        except Exception as e:
            print(f"  获取标签页失败: {e}")

        if not detail_url:
            print("  ❌ 未找到详情页")
            return False
        print(f"  详情页: {detail_url}")

        m = re.search(r'id=(\d+)', detail_url)
        if not m:
            print("  ❌ 无法解析法规ID")
            return False
        law_id = m.group(1)

        # 在详情页中获取数据（用主页面session请求lawDetail也行，但需要登录态一致）
        # 直接在新标签页请求
        with client.new_page(detail_url) as detail_page:
            detail_page.wait_for_load_state("load", timeout=30000)
            time.sleep(8)

            js = """
            (async () => {
                const resp = await fetch('/service-law/biz/lawrecordreviewreportregulations/lawDetail?id=LAW_ID');
                return await resp.text();
            })()
            """.replace('LAW_ID', law_id)
            r = detail_page.runtime.evaluate(js, await_promise=True, return_by_value=True)
            resp_text = r.get('result', {}).get('value', '')
            if not resp_text:
                print("  ❌ lawDetail 返回空")
                return False

            data = json.loads(resp_text)
            law = data.get('data', {})
            file_ids = law.get('fileIds', [])
            if not file_ids:
                print("  ❌ 无文件")
                return False

            file_info = file_ids[0]
            download_url = file_info.get('fileUrl', '')
            if download_url and not download_url.startswith('http'):
                download_url = 'https://chat.hnzhrd.gov.cn:82' + download_url

            metadata = {
                'title': law.get('title', keyword),
                'authority': law.get('formulationAuthorityName', ''),
                'published': law.get('publishedTime', ''),
                'implemented': law.get('implementationTime', ''),
                'validity': law.get('validity', ''),
                'fileName': file_info.get('fileName', ''),
            }
            print(f"  标题: {metadata['title']}")
            print(f"  制定机关: {metadata['authority']}")
            print(f"  文件: {metadata['fileName']}")

            # 下载docx
            req = urllib.request.Request(download_url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': detail_url
            })
            resp = urllib.request.urlopen(req, timeout=120)
            file_data = resp.read()

            if not file_data.startswith(b'PK'):
                print("  ❌ 下载内容不是docx")
                return False

            docx_path = f"{output}_原文件.docx"
            os.makedirs(os.path.dirname(docx_path), exist_ok=True)
            with open(docx_path, 'wb') as f:
                f.write(file_data)
            print(f"  ✅ 已保存: {docx_path} ({len(file_data)} 字节)")

            text = extract_docx_text(docx_path)
            header = f"""# {metadata['title']}（全文·完整版）

- **来源**: 湖南省法规规章规范性文件数据库（chat.hnzhrd.gov.cn）
- **制定机关**: {metadata['authority']}
- **发布日期**: {metadata['published']}
- **实施日期**: {metadata['implemented'] or '未标注'}
- **时效性**: {'✅ 有效' if metadata['validity'] == 'valid' else metadata['validity']}

---

"""
            txt_path = f"{output}_全文_完整版.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(header + text)
            print(f"  ✅ 已保存: {txt_path} ({len(text)} 字符)")
            return True


def main():
    with SyncCDPClient.launch(headless=True, browser_path=EDGE_PATH) as client:
        for law in LAWS:
            try:
                fetch_one_law(client, law)
            except Exception as e:
                print(f"  ❌ 采集异常: {e}")
                import traceback
                traceback.print_exc()
        print("\n=== 采集完成 ===")


if __name__ == "__main__":
    main()