# -*- coding: utf-8 -*-
"""探查flk详情页DOM结构，定位正文容器"""
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

            # 探查页面中的所有主要容器
            js = """
            (() => {
                const divs = Array.from(document.querySelectorAll('div'));
                const info = divs
                    .filter(d => {
                        const rect = d.getBoundingClientRect();
                        return rect.width > 200 && rect.height > 100;
                    })
                    .map(d => ({
                        class: (d.className||'').toString().substring(0, 80),
                        w: Math.round(d.getBoundingClientRect().width),
                        h: Math.round(d.getBoundingClientRect().height),
                        textLen: (d.innerText||'').length,
                        textHead: (d.innerText||'').substring(0, 50).replace(/\\s+/g, ' ')
                    }))
                    .filter(d => d.textLen > 50)
                    .slice(0, 15);
                return JSON.stringify(info);
            })()
            """
            result = page.runtime.evaluate(js)
            val = result.get('result', {}).get('value', '[]')
            print("主要容器:")
            print(val)

            # 检查是否有iframe或shadow DOM
            js2 = """
            (() => {
                const iframes = Array.from(document.querySelectorAll('iframe')).map(f => ({
                    src: f.src,
                    w: f.getBoundingClientRect().width,
                    h: f.getBoundingClientRect().height
                }));
                return JSON.stringify(iframes);
            })()
            """
            result2 = page.runtime.evaluate(js2)
            val2 = result2.get('result', {}).get('value', '[]')
            print("\niframe列表:")
            print(val2)

            # 检查可滚动容器
            js3 = """
            (() => {
                const scrollers = Array.from(document.querySelectorAll('*')).filter(el => {
                    const s = getComputedStyle(el);
                    return (s.overflowY === 'auto' || s.overflowY === 'scroll') && el.scrollHeight > el.clientHeight + 50;
                }).map(el => ({
                    tag: el.tagName,
                    class: (el.className||'').toString().substring(0, 60),
                    scrollHeight: el.scrollHeight,
                    clientHeight: el.clientHeight
                })).slice(0, 10);
                return JSON.stringify(scrollers);
            })()
            """
            result3 = page.runtime.evaluate(js3)
            val3 = result3.get('result', {}).get('value', '[]')
            print("\n可滚动容器:")
            print(val3)

except Exception as e:
    import traceback
    print("测试失败:", e)
    traceback.print_exc()