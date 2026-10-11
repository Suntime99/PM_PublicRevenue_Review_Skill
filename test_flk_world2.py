# -*- coding: utf-8 -*-
"""动态获取frameId后创建isolated world读取iframe正文"""
import sys, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from cdpwave.sync import SyncCDPClient

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BBBS = "ff808181796a636a0179822a19640c92"
URL = f"https://flk.npc.gov.cn/detail?id={BBBS}&title=%E4%B8%AD%E5%8D%8E%E4%BA%BA%E6%B0%91%E5%85%B1%E5%92%8C%E5%9B%BD%E5%88%91%E6%B3%95"

def get_child_frame_id(page):
    ft = page.page.get_frame_tree()
    tree = ft.get('frameTree', {})
    frame = tree.get('frame', {})
    children = tree.get('childFrames', [])
    if children:
        child = children[0].get('frame', {})
        return child.get('id'), child.get('name', ''), child.get('url', '')
    return None, None, None

try:
    with SyncCDPClient.launch(headless=True, browser_path=EDGE_PATH) as client:
        with client.new_page(URL) as page:
            page.wait_for_load_state("load", timeout=30000)
            time.sleep(10)

            # 动态获取子frame
            child_id, child_name, child_url = get_child_frame_id(page)
            print(f"子frame: id={child_id}, name={child_name}")
            print(f"url={child_url[:120]}")

            if not child_id:
                print("未找到子frame")
                sys.exit(1)

            # 在子frame中创建isolated world
            world = page.page.create_isolated_world(
                frame_id=child_id,
                world_name="law_world",
                grant_universal_access=True
            )
            print("create_isolated_world 结果:", json.dumps(world, ensure_ascii=False)[:300])
            context_id = world.get('executionContextId')
            print("执行上下文ID:", context_id)

            # 在该context中执行JS读取正文
            if context_id:
                js = """
                (() => {
                    const body = document.body;
                    return body ? body.innerText.substring(0, 2000) : 'NO_BODY';
                })()
                """
                # 通过runtime.evaluate的contextId参数
                result = page.runtime.evaluate(js, execution_context_id=context_id)
                val = result.get('result', {}).get('value', str(result))
                print("\niframe正文前2000字:")
                print(val)

except Exception as e:
    import traceback
    print("测试失败:", e)
    traceback.print_exc()