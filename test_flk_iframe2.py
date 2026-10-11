# -*- coding: utf-8 -*-
"""抓取flk详情页iframe完整src并尝试直接访问"""
import sys, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from cdpwave.sync import SyncCDPClient

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BBBS = "ff808181796a636a0179822a19640c92"
URL = f"https://flk.npc.gov.cn/detail?id={BBBS}&title=%E4%B8%AD%E5%8D%8E%E4%BA%BA%E6%B0%91%E5%85%B1%E5%92%8C%E5%9B%BD%E5%88%91%E6%B3%95"

try:
    with SyncCDPClient.launch(headless=True, browser_path=EDGE_PATH) as client:
        # 第一步：打开详情页，获取iframe完整src
        with client.new_page(URL) as page:
            page.wait_for_load_state("load", timeout=30000)
            time.sleep(8)
            result = page.runtime.evaluate("document.querySelector('iframe') ? document.querySelector('iframe').src : 'NO_IFRAME'")
            iframe_src = result.get('result', {}).get('value', 'NO_IFRAME')
            print("iframe完整src:")
            print(iframe_src)

            # 第二步：如果src含内网IP，尝试用flkofd域名+filePath构造可访问的reader URL
            # reader的file参数是内网地址，但也许可以替换为公网地址
            import urllib.parse
            if 'file=' in iframe_src:
                # 提取file参数值
                parsed = urllib.parse.urlparse(iframe_src)
                qs = urllib.parse.parse_qs(parsed.query)
                file_val = qs.get('file', [''])[0]
                print("\nfile参数:", file_val)
                print("file参数是否内网:", '172.16' in file_val or 'localhost' in file_val)

                # 尝试构造公网替代：将内网IP替换为flk.npc.gov.cn
                if '172.16' in file_val:
                    alt_file = file_val.replace('http://172.16.220.27:38080', 'https://flk.npc.gov.cn')
                    alt_url = f"https://flkofd.npc.gov.cn/reader?file={urllib.parse.quote(alt_file, safe='')}"
                    print("\n构造的替代URL:")
                    print(alt_url)

except Exception as e:
    import traceback
    print("测试失败:", e)
    traceback.print_exc()