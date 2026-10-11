# -*- coding: utf-8 -*-
"""检查湖南法规库列表项祖先结构"""
import sys
import time
import json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from cdpwave.sync import SyncCDPClient

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DB_URL = "https://chat.hnzhrd.gov.cn:82/sub/legalDatabase/#/index"


def main():
    with SyncCDPClient.launch(headless=True, browser_path=EDGE_PATH) as client:
        with client.new_page(DB_URL) as page:
            page.wait_for_load_state("load", timeout=30000)
            time.sleep(8)

            # 设置搜索词
            js = """
            (() => {
                const inputs = document.querySelectorAll('input');
                const target = inputs[1];
                const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeSetter.call(target, '物业管理条例');
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

            # 输出标题元素的祖先链
            js3 = """
            (() => {
                const spans = document.querySelectorAll('span');
                for (const s of spans) {
                    if (s.innerText && s.innerText.trim() === '物业管理条例' && s.children.length === 0) {
                        const chain = [];
                        let el = s;
                        for (let i = 0; i < 8 && el; i++) {
                            const cls = (el.className || '').toString();
                            chain.push({
                                level: i,
                                tag: el.tagName,
                                cls: cls.substring(0, 80),
                                text: (el.innerText || el.textContent || '').trim().substring(0, 40),
                                isClickable: el.onclick !== null || cls.includes('cursor') || cls.includes('hover') || el.tagName === 'A'
                            });
                            el = el.parentElement;
                        }
                        return chain;
                    }
                }
                return 'NOT_FOUND';
            })()
            """
            r = page.runtime.evaluate(js3, return_by_value=True)
            val = r.get('result', {}).get('value', [])
            print("=== 祖先链 ===")
            if isinstance(val, list):
                for item in val:
                    print(f"  L{item['level']} <{item['tag']}> cls=\"{item['cls']}\" text=\"{item['text']}\" clickable={item['isClickable']}")
            else:
                print(val)

            # 尝试直接调用可能的详情接口（React应用通常有API）
            js4 = """
            (async () => {
                // 尝试常见的详情接口
                const apis = [
                    '/api/law/detail?title=湖南省物业管理条例',
                    '/api/legal/detail?name=湖南省物业管理条例',
                    '/api/law/getLawByName?name=湖南省物业管理条例',
                    '/prod-api/law/search?keyword=湖南省物业管理条例',
                ];
                const results = [];
                for (const api of apis) {
                    try {
                        const resp = await fetch(api);
                        const text = await resp.text();
                        results.push({api: api, status: resp.status, body: text.substring(0, 200)});
                    } catch(e) {
                        results.push({api: api, error: e.message});
                    }
                }
                return results;
            })()
            """
            r2 = page.runtime.evaluate(js4, await_promise=True, return_by_value=True)
            val2 = r2.get('result', {}).get('value', [])
            print("\n=== API探测 ===")
            for item in val2:
                print(f"  {item}")


if __name__ == "__main__":
    main()