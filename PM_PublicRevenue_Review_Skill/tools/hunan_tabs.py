# -*- coding: utf-8 -*-
"""检查湖南法规库卡片祖先容器可见性 + tab切换"""
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

            # 设置搜索
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

            # 查找卡片祖先的display状态
            js3 = """
            (() => {
                const cards = document.querySelectorAll('div[class*="hover:bg-gray-50"]');
                for (const card of cards) {
                    if ((card.innerText || '').includes('物业管理条例')) {
                        const chain = [];
                        let el = card;
                        for (let i = 0; i < 8 && el; i++) {
                            const style = window.getComputedStyle(el);
                            chain.push({
                                level: i,
                                tag: el.tagName,
                                cls: (el.className || '').toString().substring(0, 70),
                                display: style.display,
                                visibility: style.visibility,
                                hasId: el.id
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
            chain = r.get('result', {}).get('value', [])
            print("=== 卡片祖先链 ===")
            for item in chain:
                print(f"  L{item['level']} <{item['tag']}> display={item['display']} vis={item['visibility']} cls=\"{item['cls']}\"")

            # 查找tab元素
            js4 = """
            (() => {
                const tabs = document.querySelectorAll('[class*="tab"], [role="tab"]');
                const results = [];
                tabs.forEach(t => {
                    const text = (t.innerText || t.textContent || '').trim();
                    if (text && text.length < 20) {
                        results.push({text: text.substring(0, 20), cls: (t.className || '').toString().substring(0, 60), tag: t.tagName});
                    }
                });
                return results.slice(0, 20);
            })()
            """
            r2 = page.runtime.evaluate(js4, return_by_value=True)
            tabs = r2.get('result', {}).get('value', [])
            print("\n=== Tab元素 ===")
            for t in tabs:
                print(f"  {t}")


if __name__ == "__main__":
    main()