# -*- coding: utf-8 -*-
"""设置桌面视口后点击湖南省物业管理条例卡片，提取详情全文"""
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

            # 设置桌面视口宽度1280px
            try:
                page.send('Emulation.setDeviceMetricsOverride', {
                    'width': 1280, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False
                })
                print("已设置桌面视口 1280x900")
                time.sleep(2)
            except Exception as e:
                print(f"设置视口失败: {e}")

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

            # 查找卡片位置
            js3 = """
            (() => {
                const cards = document.querySelectorAll('div[class*="hover:bg-gray-50"]');
                for (const card of cards) {
                    if ((card.innerText || '').includes('物业管理条例')) {
                        card.scrollIntoView({block: 'center'});
                        const rect = card.getBoundingClientRect();
                        return {
                            x: rect.x + rect.width / 2,
                            y: rect.y + rect.height / 2,
                            w: rect.width,
                            h: rect.height,
                            offsetParent: card.offsetParent ? 'ok' : 'null'
                        };
                    }
                }
                return null;
            })()
            """
            r = page.runtime.evaluate(js3, return_by_value=True)
            pos = r.get('result', {}).get('value')
            print("卡片位置:", pos)

            if pos and pos.get('x'):
                # 启用网络监听
                page.network.enable()
                time.sleep(1)

                # CDP真实点击
                page.input.dispatch_mouse_event('mousePressed', x=pos['x'], y=pos['y'], button='left', click_count=1)
                page.input.dispatch_mouse_event('mouseReleased', x=pos['x'], y=pos['y'], button='left', click_count=1)
                print("已点击卡片")
                time.sleep(12)

                # 捕获网络请求
                js4 = """
                (() => {
                    const entries = performance.getEntriesByType('resource');
                    return entries
                        .filter(e => e.initiatorType === 'xmlhttprequest' || e.initiatorType === 'fetch')
                        .map(e => e.name)
                        .filter(n => n.includes('/service-law/'))
                        .slice(-20);
                })()
                """
                r2 = page.runtime.evaluate(js4, return_by_value=True)
                reqs = r2.get('result', {}).get('value', [])
                print("点击后的 service-law 请求:")
                for req in reqs:
                    print(f"  {req}")

                url = page.runtime.evaluate('window.location.href', return_by_value=True).get('result', {}).get('value', '')
                print("当前URL:", url)
                body = page.runtime.evaluate('document.body.innerText.substring(0, 3000)', return_by_value=True).get('result', {}).get('value', '')
                print("页面内容:", body[:2500])
            else:
                print("卡片仍不可见")


if __name__ == "__main__":
    main()