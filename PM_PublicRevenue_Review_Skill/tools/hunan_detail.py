# -*- coding: utf-8 -*-
"""从湖南省法规库详情页提取湖南省物业管理条例全文"""
import sys
import time
import json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from cdpwave.sync import SyncCDPClient

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DETAIL_URL = "https://chat.hnzhrd.gov.cn:82/sub/legalDatabase/#/details?id=629219129475203072&typeName=%E6%B3%95%E8%A7%84&dataType=reg"


def main():
    with SyncCDPClient.launch(headless=True, browser_path=EDGE_PATH) as client:
        with client.new_page(DETAIL_URL) as page:
            page.wait_for_load_state("load", timeout=30000)
            time.sleep(10)

            # 设置桌面视口
            page.send('Emulation.setDeviceMetricsOverride', {
                'width': 1280, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False
            })
            time.sleep(3)

            url = page.runtime.evaluate('window.location.href', return_by_value=True).get('result', {}).get('value', '')
            print("当前URL:", url)

            # 提取页面正文
            js = """
            (() => {
                const body = document.body.innerText;
                return body;
            })()
            """
            r = page.runtime.evaluate(js, return_by_value=True)
            text = r.get('result', {}).get('value', '')
            print(f"页面文本长度: {len(text)}")
            print("=== 前1500字符 ===")
            print(text[:1500])
            print("=== 后500字符 ===")
            print(text[-500:])


if __name__ == "__main__":
    main()