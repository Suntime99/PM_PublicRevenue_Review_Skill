# -*- coding: utf-8 -*-
"""关键测试：用浏览器访问flk detail?id=URL，提取刑法正文"""
import sys, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from cdpwave.sync import SyncCDPClient

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

BBBS = "ff808181796a636a0179822a19640c92"
URL = f"https://flk.npc.gov.cn/detail?id={BBBS}&title=%E4%B8%AD%E5%8D%8E%E4%BA%BA%E6%B0%91%E5%85%B1%E5%92%8C%E5%9B%BD%E5%88%91%E6%B3%95"

try:
    with SyncCDPClient.launch(headless=True, browser_path=EDGE_PATH) as client:
        with client.new_page(URL) as page:
            print("打开flk刑法详情页，等待SPA渲染...")
            page.wait_for_load_state("load", timeout=30000)
            time.sleep(12)  # SPA需要较长时间加载数据

            # 获取当前URL
            url = page.runtime.evaluate("window.location.href")
            print("当前URL:", url.get('result', {}).get('value'))

            # 获取页面标题
            title = page.runtime.evaluate("document.title")
            print("页面标题:", title.get('result', {}).get('value'))

            # 提取页面正文
            body = page.runtime.evaluate("document.body ? document.body.innerText : ''")
            text = body.get('result', {}).get('value', '')
            print(f"页面文本长度: {len(text)} 字符")
            print("\n页面文本前1500字:")
            print(text[:1500])

            # 检查是否含刑法条文
            if '第一条' in text and '第二百七十一条' in text:
                print("\n✅ 刑法正文渲染成功！")
            elif '刑法' in text:
                print("\n⚠️ 页面含刑法关键词但未找到完整条文")
            else:
                print("\n❌ 未找到刑法正文")

except Exception as e:
    import traceback
    print("测试失败:", e)
    traceback.print_exc()