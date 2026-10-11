# -*- coding: utf-8 -*-
"""枚举flk详情页所有执行上下文，定位iframe上下文"""
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

            # 启用Runtime并获取执行上下文
            page.runtime.enable()
            # 通过send直接调用Runtime.executionContextCreated可能已被触发，
            # 尝试用Runtime.evaluate的contextId参数。先看看有没有接口列出contexts。
            # CDP没有直接的listContexts，但可以监听事件。
            # 用session的方式：cdpwave的wait_for_event可能可以。

            # 尝试使用Page.createIsolatedWorld在iframe中创建独立世界
            # 先看是否有这个方法
            print("尝试 create_isolated_world ...")
            try:
                world = page.page.create_isolated_world(
                    frame_id="B254A6E430260C312D1DFE8D1FDCC1CA",
                    world_name="test_world",
                    grant_universal_access=True
                )
                print("create_isolated_world 结果:", json.dumps(world, ensure_ascii=False)[:500])
            except Exception as e:
                print("create_isolated_world 失败:", e)

except Exception as e:
    import traceback
    print("测试失败:", e)
    traceback.print_exc()