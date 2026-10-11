# -*- coding: utf-8 -*-
"""探测湖南法规库 mergePage 接口，获取湖南省物业管理条例详情"""
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

            # 探测 mergePage 接口（POST）
            js = """
            (async () => {
                // 尝试POST调用mergePage
                const bodies = [
                    {keyword: '物业管理条例', pageNum: 1, pageSize: 10},
                    {name: '物业管理条例', pageNum: 1, pageSize: 10},
                    {searchKey: '物业管理条例', current: 1, size: 10},
                    {}
                ];
                const results = [];
                for (const body of bodies) {
                    try {
                        const resp = await fetch('/service-law/biz/lawrecordreviewreportregulations/mergePage', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(body)
                        });
                        const text = await resp.text();
                        results.push({body: JSON.stringify(body), status: resp.status, text: text.substring(0, 500)});
                    } catch(e) {
                        results.push({body: JSON.stringify(body), error: e.message});
                    }
                }
                return results;
            })()
            """
            r = page.runtime.evaluate(js, await_promise=True, return_by_value=True)
            results = r.get('result', {}).get('value', [])
            print("=== mergePage 接口探测 ===")
            for item in results:
                print(json.dumps(item, ensure_ascii=False, indent=1)[:600])
                print("---")

            # 同时看lawGetDict
            js2 = """
            (async () => {
                const resp = await fetch('/service-law/biz/lawrecordreviewreportregulations/lawGetDict');
                const text = await resp.text();
                return text.substring(0, 800);
            })()
            """
            r2 = page.runtime.evaluate(js2, await_promise=True, return_by_value=True)
            val2 = r2.get('result', {}).get('value', '')
            print("\n=== lawGetDict ===")
            print(val2[:600])


if __name__ == "__main__":
    main()