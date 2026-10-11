# -*- coding: utf-8 -*-
"""点击湖南法规列表项并观察页面变化和网络请求"""
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

            # 获取L1 span位置并真实点击
            js3 = """
            (() => {
                const spans = document.querySelectorAll('span');
                for (const s of spans) {
                    if (s.innerText && s.innerText.trim() === '湖南省物业管理条例' && s.className.includes('font-medium')) {
                        const rect = s.getBoundingClientRect();
                        return {x: rect.x + rect.width/2, y: rect.y + rect.height/2, w: rect.width, h: rect.height};
                    }
                }
                return null;
            })()
            """
            r = page.runtime.evaluate(js3, return_by_value=True)
            pos = r.get('result', {}).get('value')
            print("标题位置:", pos)

            if pos:
                # 先启用网络监听
                page.network.enable()
                time.sleep(1)

                # CDP真实点击标题
                page.input.dispatch_mouse_event('mousePressed', x=pos['x'], y=pos['y'], button='left', click_count=1)
                page.input.dispatch_mouse_event('mouseReleased', x=pos['x'], y=pos['y'], button='left', click_count=1)
                print("已点击标题")
                time.sleep(8)

                # 观察页面变化
                url = page.runtime.evaluate('window.location.href', return_by_value=True).get('result', {}).get('value', '')
                print("当前URL:", url)
                body = page.runtime.evaluate('document.body.innerText.substring(0, 2000)', return_by_value=True).get('result', {}).get('value', '')
                print("页面内容:", body[:1500])

                # 获取网络请求
                js4 = """
                (() => {
                    const entries = performance.getEntriesByType('resource');
                    return entries
                        .filter(e => e.initiatorType === 'xmlhttprequest' || e.initiatorType === 'fetch')
                        .map(e => e.name)
                        .filter(n => !n.includes('.js') && !n.includes('.css') && !n.includes('.png') && !n.includes('.woff'))
                        .slice(-15);
                })()
                """
                r2 = page.runtime.evaluate(js4, return_by_value=True)
                reqs = r2.get('result', {}).get('value', [])
                print("\n网络请求:")
                for req in reqs:
                    print(f"  {req}")


if __name__ == "__main__":
    main()