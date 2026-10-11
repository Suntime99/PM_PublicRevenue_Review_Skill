# -*- coding: utf-8 -*-
"""从湖南省法规规章规范性文件数据库采集条例全文"""
import sys
import time
import json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from cdpwave.sync import SyncCDPClient

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DB_URL = "https://chat.hnzhrd.gov.cn:82/sub/legalDatabase/#/index"


def set_search_and_click(page, keyword):
    """设置搜索词并点击搜索按钮"""
    js = """
    (() => {
        const inputs = document.querySelectorAll('input');
        const target = inputs[1];
        if (!target) return 'NO_INPUT';
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeSetter.call(target, '""" + keyword + """');
        target.dispatchEvent(new Event('input', {bubbles: true}));
        return 'SET';
    })()
    """
    r = page.runtime.evaluate(js, return_by_value=True)
    print(f"  设置搜索词: {r.get('result', {}).get('value', 'FAIL')}")
    time.sleep(1)

    js2 = """
    (() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.innerText.trim() === '搜索' && b.className.includes('ant-btn-primary')) {
                b.click();
                return 'clicked';
            }
        }
        return 'NOT_FOUND';
    })()
    """
    r2 = page.runtime.evaluate(js2, return_by_value=True)
    print(f"  点击搜索: {r2.get('result', {}).get('value', 'FAIL')}")
    time.sleep(8)


def get_law_item_info(page):
    """获取搜索结果区域的所有法规标题元素"""
    js = """
    (() => {
        // 查找所有可能的法规卡片/列表项
        const results = [];
        // 搜索包含'物业管理条例'的所有元素（叶子节点）
        const all = document.querySelectorAll('*');
        const seen = new Set();
        for (const el of all) {
            if (el.children.length === 0 && el.innerText && el.innerText.includes('物业管理条例')) {
                const key = el.tagName + '|' + (el.className || '');
                if (!seen.has(key)) {
                    seen.add(key);
                    results.push({
                        tag: el.tagName,
                        text: el.innerText.trim().substring(0, 50),
                        cls: (el.className || '').toString().substring(0, 80),
                        parentCls: (el.parentElement?.className || '').toString().substring(0, 80),
                        gpCls: (el.parentElement?.parentElement?.className || '').toString().substring(0, 80)
                    });
                }
            }
        }
        return results.slice(0, 20);
    })()
    """
    r = page.runtime.evaluate(js, return_by_value=True)
    return r.get('result', {}).get('value', [])


def click_law_item(page):
    """点击法规标题链接，进入详情页"""
    js = """
    (() => {
        const spans = document.querySelectorAll('span');
        for (const s of spans) {
            if (s.innerText && s.innerText.trim() === '物业管理条例' && s.children.length === 0) {
                // 向上找到 a 链接并点击
                let el = s;
                for (let i = 0; i < 5; i++) {
                    el = el.parentElement;
                    if (!el) break;
                    if (el.tagName === 'A') {
                        el.click();
                        return 'clicked: ' + el.href;
                    }
                }
                s.parentElement.click();
                return 'clicked parent: ' + s.parentElement.tagName;
            }
        }
        return 'NOT_FOUND';
    })()
    """
    r = page.runtime.evaluate(js, return_by_value=True)
    return r.get('result', {}).get('value', '')


def extract_detail(page):
    """提取详情页全文"""
    js = """
    (() => {
        const body = document.body.innerText;
        return body;
    })()
    """
    r = page.runtime.evaluate(js, return_by_value=True)
    return r.get('result', {}).get('value', '')


def main():
    with SyncCDPClient.launch(headless=True, browser_path=EDGE_PATH) as client:
        with client.new_page(DB_URL) as page:
            page.wait_for_load_state("load", timeout=30000)
            time.sleep(8)

            print("=== 设置搜索词 ===")
            set_search_and_click(page, '物业管理条例')

            print("=== 点击法规标题 ===")
            result = click_law_item(page)
            print(f"  {result}")
            time.sleep(10)

            print("=== 提取详情页内容 ===")
            url = page.runtime.evaluate('window.location.href', return_by_value=True).get('result', {}).get('value', '')
            print(f"  当前URL: {url}")
            text = extract_detail(page)
            print(f"  页面文本长度: {len(text)}")
            print(text[:2000])


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()