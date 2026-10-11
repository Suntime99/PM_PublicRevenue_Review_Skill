# -*- coding: utf-8 -*-
"""点击湖南法规卡片后检查新标签页/模态框"""
import sys
import time
import json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from cdpwave.sync import SyncCDPClient

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DB_URL = "https://chat.hnzhrd.gov.cn:82/sub/legalDatabase/#/index"


def main():
    with SyncCDPClient.launch(headless=True, browser_path=EDGE_PATH) as client:
        # 先打开主页面
        with client.new_page(DB_URL) as page:
            page.wait_for_load_state("load", timeout=30000)
            time.sleep(8)

            # 设置桌面视口
            page.send('Emulation.setDeviceMetricsOverride', {
                'width': 1280, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False
            })
            time.sleep(2)

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

            # 点击卡片前，记录当前targets数量
            targets_before = client.send('Target.getTargets') if hasattr(client, 'send') else None

            # 点击卡片
            js3 = """
            (() => {
                const cards = document.querySelectorAll('div[class*="hover:bg-gray-50"]');
                for (const card of cards) {
                    if ((card.innerText || '').includes('物业管理条例')) {
                        card.scrollIntoView({block: 'center'});
                        const rect = card.getBoundingClientRect();
                        return {x: rect.x + rect.width / 2, y: rect.y + rect.height / 2};
                    }
                }
                return null;
            })()
            """
            r = page.runtime.evaluate(js3, return_by_value=True)
            pos = r.get('result', {}).get('value')
            print("卡片位置:", pos)

            if pos:
                page.input.dispatch_mouse_event('mousePressed', x=pos['x'], y=pos['y'], button='left', click_count=1)
                page.input.dispatch_mouse_event('mouseReleased', x=pos['x'], y=pos['y'], button='left', click_count=1)
                print("已点击")
                time.sleep(10)

                # 检查页面中是否出现模态框/抽屉/新内容
                js4 = """
                (() => {
                    const body = document.body.innerText;
                    const hasModal = !!document.querySelector('.ant-modal, [class*="modal"], [class*="drawer"], [class*="dialog"]');
                    const modalText = document.querySelector('.ant-modal, [class*="modal-content"]') ?
                        document.querySelector('.ant-modal, [class*="modal-content"]').innerText.substring(0, 500) : '';
                    return {
                        hasModal,
                        modalText,
                        bodyLen: body.length,
                        bodyPreview: body.substring(0, 1000)
                    };
                })()
                """
                r2 = page.runtime.evaluate(js4, return_by_value=True)
                val = r2.get('result', {}).get('value', {})
                print("模态框状态:", val.get('hasModal'))
                print("模态框内容:", val.get('modalText', '')[:500])
                print("页面长度:", val.get('bodyLen'))

                # 检查所有打开的target
                try:
                    targets = client.send('Target.getTargets')
                    print("\n当前targets:")
                    for t in targets.get('targetInfos', []):
                        print(f"  {t.get('type')}: {t.get('url', '')[:120]}")
                except Exception as e:
                    print(f"获取targets失败: {e}")


if __name__ == "__main__":
    main()