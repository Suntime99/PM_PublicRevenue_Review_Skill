# -*- coding: utf-8 -*-
"""检查湖南省物业管理条例卡片的完整HTML结构和可见性"""
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

            # 查看卡片的完整outerHTML和可见性
            js3 = """
            (() => {
                const cards = document.querySelectorAll('div[class*="hover:bg-gray-50"]');
                const results = [];
                for (const card of cards) {
                    const text = card.innerText || '';
                    if (text.includes('物业管理条例')) {
                        const rect = card.getBoundingClientRect();
                        const style = window.getComputedStyle(card);
                        results.push({
                            text: text.substring(0, 100),
                            rect: {x: rect.x, y: rect.y, w: rect.width, h: rect.height},
                            display: style.display,
                            visibility: style.visibility,
                            offsetParent: card.offsetParent ? 'exists' : 'null',
                            html: card.outerHTML.substring(0, 1500)
                        });
                    }
                }
                return results;
            })()
            """
            r = page.runtime.evaluate(js3, return_by_value=True)
            results = r.get('result', {}).get('value', [])
            print("=== 卡片详情 ===")
            for item in results:
                print(json.dumps(item, ensure_ascii=False, indent=2)[:2000])
                print("---")


if __name__ == "__main__":
    main()