# -*- coding: utf-8 -*-
"""通过CDP frame机制读取flk详情页iframe中的法规正文"""
import sys, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from cdpwave.sync import SyncCDPClient

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BBBS = "ff808181796a636a0179822a19640c92"
URL = f"https://flk.npc.gov.cn/detail?id={BBBS}&title=%E4%B8%AD%E5%8D%8E%E4%BA%BA%E6%B0%91%E5%85%B1%E5%92%8C%E5%9B%BD%E5%88%91%E6%B3%95"

try:
    with SyncCDPClient.launch(headless=True, browser_path=EDGE_PATH) as client:
        with client.new_page(URL) as page:
            page.wait_for_load_state("load", timeout=30000)
            time.sleep(10)

            # 获取frame树
            ft = page.page.get_frame_tree()
            print("frame树类型:", type(ft))
            print(json.dumps(ft, ensure_ascii=False, indent=2)[:2000])

except Exception as e:
    import traceback
    print("测试失败:", e)
    traceback.print_exc()