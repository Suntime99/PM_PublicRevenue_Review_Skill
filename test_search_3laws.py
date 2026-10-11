# -*- coding: utf-8 -*-
"""用必应搜索定位刑法/人民防空法/价格法权威全文URL"""
import sys, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from cdpwave.sync import SyncCDPClient

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

LAWS = {
    "刑法": "q=%E4%B8%AD%E5%8D%8E%E4%BA%BA%E6%B0%91%E5%85%B1%E5%92%8C%E5%9B%BD%E5%88%91%E6%B3%95+%E5%85%A8%E6%96%87+site%3Agov.cn",
    "人民防空法": "q=%E4%B8%AD%E5%8D%8E%E4%BA%BA%E6%B0%91%E5%85%B1%E5%92%8C%E5%9B%BD%E4%BA%BA%E6%B0%91%E9%98%B2%E7%A9%BA%E6%B3%95+%E5%85%A8%E6%96%87+site%3Agov.cn",
    "价格法": "q=%E4%B8%AD%E5%8D%8E%E4%BA%BA%E6%B0%91%E5%85%B1%E5%92%8C%E5%9B%BD%E4%BB%B7%E6%A0%BC%E6%B3%95+%E5%85%A8%E6%96%87+site%3Agov.cn",
}

try:
    with SyncCDPClient.launch(headless=True, browser_path=EDGE_PATH) as client:
        for name, query in LAWS.items():
            print(f"\n=== 搜索: {name} ===")
            url = f"https://www.bing.com/search?{query}"
            with client.new_page(url) as page:
                page.wait_for_load_state("load", timeout=30000)
                time.sleep(4)
                js = """
                (() => {
                    const results = Array.from(document.querySelectorAll('#b_results li.b_algo h2 a, #b_results .b_algo a'));
                    return JSON.stringify(results.slice(0, 8).map(a => ({title: (a.innerText||'').substring(0,60), href: a.href})));
                })()
                """
                result = page.runtime.evaluate(js)
                val = result.get('result', {}).get('value', '[]')
                print(val)

except Exception as e:
    import traceback
    print("测试失败:", e)
    traceback.print_exc()