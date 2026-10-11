# -*- coding: utf-8 -*-
"""
通用反爬浏览器采集工具（基于 cdpwave）
=====================================
适用于：JS渲染型反爬、需要Cookie会话、需要点击交互、正文在DOM中的网站。
已验证：可驱动 Edge/Chrome 访问国家法律法规数据库等政府网站。

用法：
    # 提取页面正文
    python browser_scraper.py url --output result.txt --wait 5

    # 提取页面HTML
    python browser_scraper.py url --output page.html --mode html --wait 5

    # 截图
    python browser_scraper.py url --output shot.png --mode screenshot --wait 8

    # 生成PDF（适合法规原文存档）
    python browser_scraper.py url --output law.pdf --mode pdf --wait 8

    # 批量采集（从文件读取URL列表）
    python browser_scraper.py urls.txt --output-dir ./scraped --wait 5

    # 搜索flk法规（返回JSON结果）
    python browser_scraper.py --search "物业管理条例" --flk --output results.json

    # 搜索flk法规并自动抓取第一条详情页
    python browser_scraper.py --search "物业管理条例" --flk --fetch --output 物业管理条例.txt

依赖：
    pip install cdpwave
"""
import sys
import os
import time
import argparse
import json
import re

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from cdpwave.sync import SyncCDPClient


def find_browser():
    """自动探测Edge/Chrome浏览器路径"""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def extract_text(page, wait_seconds):
    """等待渲染后提取页面正文文本"""
    time.sleep(wait_seconds)
    result = page.runtime.evaluate(
        "document.body ? document.body.innerText : ''"
    )
    return result.get("result", {}).get("value", "")


def extract_html(page, wait_seconds):
    """提取页面HTML"""
    time.sleep(wait_seconds)
    result = page.runtime.evaluate(
        "document.documentElement ? document.documentElement.outerHTML : ''"
    )
    return result.get("result", {}).get("value", "")


def extract_title(page):
    """提取页面标题"""
    result = page.runtime.evaluate("document.title")
    return result.get("result", {}).get("value", "")


# ─── flk.npc.gov.cn 专用功能 ────────────────────────────────────────────────

def flk_search(client, keyword, page_no=1, page_size=5, timeout=30000):
    """
    搜索flk.npc.gov.cn法规数据库
    返回：[{"bbbs":..., "title":..., "createTime":..., "url":...}, ...]

    注意：flk搜索API有反爬保护，可能返回空结果。
    建议直接使用已知bbbs ID访问详情页。
    """
    results = []
    try:
        with client.new_page('https://flk.npc.gov.cn/') as page:
            page.wait_for_load_state("load", timeout=timeout)
            time.sleep(3)

            # 方法1：使用fetch API搜索
            js = f'''
            (() => {{
                return fetch('/law-search/search/list?keyword={keyword}&pageNo={page_no}&pageSize={page_size}', {{
                    headers: {{
                        'Accept': 'application/json, text/plain, */*',
                        'Referer': 'https://flk.npc.gov.cn/',
                        'Origin': 'https://flk.npc.gov.cn'
                    }}
                }})
                    .then(r => r.json())
                    .then(d => {{
                        if (d.code === 200 || d.code === '200') {{
                            return (d.result || {{}}).list || [];
                        }}
                        console.warn('Search API warning:', d.msg);
                        return [];
                    }})
                    .catch(e => ({{error: e.message}}));
            }})()
            '''
            r = page.runtime.evaluate(js, await_promise=True, return_by_value=True)
            data = r.get('result', {}).get('value', [])

            if isinstance(data, list) and len(data) > 0:
                for item in data:
                    bbbs = item.get('bbbs', '')
                    title = item.get('title', '')
                    if bbbs and title:
                        results.append({
                            'bbbs': bbbs,
                            'title': title,
                            'createTime': item.get('createTime', ''),
                            'url': f"https://flk.npc.gov.cn/detail?id={bbbs}"
                        })
            elif isinstance(data, dict) and 'error' in data:
                print(f"    ⚠️ 搜索错误: {data['error']}")
            else:
                # 方法2：尝试直接访问搜索结果页（通过JS导航）
                print(f"    ⚠️ 搜索API返回空，尝试URL跳转...")
                search_url = f"https://flk.npc.gov.cn/search?keyword={keyword}"
                page.runtime.evaluate(f'window.location.href = "{search_url}"', return_by_value=True)
                page.wait_for_load_state("load", timeout=30000)
                time.sleep(8)

                # 从搜索结果页提取链接
                js2 = '''
                (() => {
                    const links = document.querySelectorAll('a[href*="detail?id="]');
                    return Array.from(links).slice(0, 5).map(a => {
                        const match = a.href.match(/id=([a-f0-9]+)/);
                        return match ? {bbbs: match[1], title: a.innerText.trim(), url: a.href} : null;
                    }).filter(Boolean);
                })()
                '''
                r2 = page.runtime.evaluate(js2, return_by_value=True)
                results = r2.get('result', {}).get('value', []) or []

    except Exception as e:
        print(f"    ❌ 搜索异常: {e}")

    return results


def flk_get_details(client, bbbs, timeout=30000):
    """
    获取flk法规详情（元数据+内容树）
    返回：dict 或 None
    """
    try:
        with client.new_page(f'https://flk.npc.gov.cn/detail?id={bbbs}') as page:
            page.wait_for_load_state("load", timeout=timeout)
            time.sleep(8)

            js = f'''
            (() => {{
                return fetch('/law-search/search/flfgDetails?bbbs={bbbs}')
                    .then(r => r.json())
                    .then(d => d.data)
                    .catch(e => null);
            }})()
            '''
            r = page.runtime.evaluate(js, await_promise=True, return_by_value=True)
            return r.get('result', {}).get('value')
    except Exception as e:
        print(f"    ❌ 获取详情失败: {e}")
        return None


def flk_extract_ofd_text(client, bbbs, timeout=30000):
    """
    从flk法规的OFD iframe提取文本（通过isolated world绕过跨域）
    注意：OFD为Canvas渲染，文本按字符分隔，需后处理。
    返回：(raw_text, success_bool)
    """
    try:
        with client.new_page(f'https://flk.npc.gov.cn/detail?id={bbbs}') as page:
            page.wait_for_load_state("load", timeout=timeout)
            time.sleep(12)

            # 获取frame树，找到子frame
            ft = page.page.get_frame_tree()
            children = ft.get('frameTree', {}).get('childFrames', [])
            if not children:
                return None, False

            child_id = children[0].get('frame', {}).get('id')
            if not child_id:
                return None, False

            # 创建isolated world
            world = page.page.create_isolated_world(
                frame_id=child_id,
                world_name='law_world',
                grant_universal_access=True
            )
            ctx_id = world.get('executionContextId')
            if not ctx_id:
                return None, False

            # 提取文本
            js = r'''
            (() => {
                const lines = document.body.innerText.split('\n');
                const filtered = lines.filter(l => {
                    const t = l.trim();
                    if (!t) return false;
                    if (/^\d+\/\d+$/.test(t)) return false;
                    if (/^\d+%$/.test(t)) return false;
                    if (/^－\d+－$/.test(t)) return false;
                    return true;
                });
                return filtered.join('\n');
            })()
            '''
            r = page.runtime.evaluate(js, execution_context_id=ctx_id, return_by_value=True)
            text = r.get('result', {}).get('value', '')
            return text, bool(text)
    except Exception as e:
        print(f"    ❌ OFD提取失败: {e}")
        return None, False


# ─── 核心采集逻辑 ────────────────────────────────────────────────────────────

def scrape_one(client, url, mode, wait_seconds, output):
    """采集单个URL"""
    print(f"  → 打开: {url}")
    with client.new_page(url) as page:
        page.wait_for_load_state("load", timeout=30000)

        title = extract_title(page)
        print(f"    页面标题: {title}")

        if mode == "text":
            content = extract_text(page, wait_seconds)
            ext = ".txt"
        elif mode == "html":
            content = extract_html(page, wait_seconds)
            ext = ".html"
        elif mode == "screenshot":
            time.sleep(wait_seconds)
            import base64
            result = page.page.capture_screenshot()
            data = result.get("data", "")
            if isinstance(data, str) and data.startswith("data:"):
                b64 = data.split(",", 1)[-1]
            else:
                b64 = data
            try:
                content_bytes = base64.b64decode(b64)
            except Exception:
                content_bytes = bytes(data, "utf-8") if isinstance(data, str) else bytes(data)
            ext = ".png"
            with open(output, "wb") as f:
                f.write(content_bytes)
            print(f"    ✅ 截图已保存: {output} ({len(content_bytes)} 字节)")
            return True
        elif mode == "pdf":
            time.sleep(wait_seconds)
            import base64
            result = page.page.print_to_pdf()
            data = result.get("data", "")
            if isinstance(data, str) and data.startswith("data:"):
                b64 = data.split(",", 1)[-1]
            else:
                b64 = data
            try:
                content_bytes = base64.b64decode(b64)
            except Exception:
                content_bytes = bytes(data, "utf-8") if isinstance(data, str) else bytes(data)
            ext = ".pdf"
            with open(output, "wb") as f:
                f.write(content_bytes)
            print(f"    ✅ PDF已保存: {output} ({len(content_bytes)} 字节)")
            return True
        else:
            content = extract_text(page, wait_seconds)
            ext = ".txt"

        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"    ✅ 已保存: {output} ({len(content)} 字符)")


# ─── 主入口 ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="通用反爬浏览器采集工具（cdpwave）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 搜索flk法规
  python browser_scraper.py --search "物业管理条例" --flk

  # 搜索并自动抓取第一条详情
  python browser_scraper.py --search "物业管理条例" --flk --fetch --output 物业管理条例.txt

  # 批量搜索多关键词
  python browser_scraper.py --search "物业管理条例" --flk --search "人民防空法" --flk --output results.json
        """
    )

    # 采集参数
    parser.add_argument("target", nargs="?", help="要采集的URL或包含URL列表的txt文件")
    parser.add_argument("--output", default="result.txt", help="输出文件路径")
    parser.add_argument("--output-dir", default="./scraped", help="批量采集的输出目录")
    parser.add_argument("--mode", default="text", choices=["text", "html", "screenshot", "pdf"],
                        help="采集模式：text/html/screenshot/pdf")
    parser.add_argument("--wait", type=int, default=5, help="等待页面渲染秒数（SPA建议8-10秒）")
    parser.add_argument("--headless", action="store_true", default=True,
                        help="使用无头模式（默认）")
    parser.add_argument("--visible", action="store_true",
                        help="使用有头模式（可见浏览器窗口，适合需人工过验证码）")

    # flk搜索参数
    flk_group = parser.add_argument_group("flk法规搜索选项")
    flk_group.add_argument("--search", action="append", dest="keywords",
                           help="搜索关键词（可多次使用）")
    flk_group.add_argument("--flk", action="store_true",
                           help="启用flk.npc.gov.cn搜索模式")
    flk_group.add_argument("--fetch", action="store_true",
                           help="搜索后自动抓取第一条法规详情页全文")
    flk_group.add_argument("--page-size", type=int, default=5,
                           help="搜索结果每页条数（默认5）")
    flk_group.add_argument("--page-no", type=int, default=1,
                           help="搜索页码（默认1）")

    args = parser.parse_args()

    # 检查flk搜索模式
    use_flk = args.flk or bool(args.keywords)

    if use_flk:
        # ── flk搜索模式 ──
        browser_path = find_browser()
        if not browser_path:
            print("❌ 未找到Edge/Chrome浏览器")
            sys.exit(1)
        print(f"检测到浏览器: {browser_path}")

        all_results = []
        try:
            with SyncCDPClient.launch(headless=not args.visible, browser_path=browser_path) as client:
                if args.keywords:
                    for kw in args.keywords:
                        print(f"\n=== 搜索: {kw} ===")
                        results = flk_search(client, kw, args.page_no, args.page_size)
                        if results:
                            print(f"找到 {len(results)} 条:")
                            for r in results:
                                print(f"  [{r['bbbs']}] {r['title']}")
                                all_results.append(r)
                        else:
                            print("  未找到结果")

                # 如果指定了 --fetch，自动抓取第一条
                if args.fetch and all_results:
                    first = all_results[0]
                    print(f"\n=== 抓取详情: {first['title']} ===")
                    details = flk_get_details(client, first['bbbs'])
                    if details:
                        # 保存元数据
                        output_json = re.sub(r'\.[^.]+$', '', args.output) + "_meta.json"
                        with open(output_json, 'w', encoding='utf-8') as f:
                            json.dump(details, f, ensure_ascii=False, indent=2)
                        print(f"  ✅ 元数据已保存: {output_json}")

                        # 尝试提取OFD正文
                        raw_text, ok = flk_extract_ofd_text(client, first['bbbs'])
                        if ok and raw_text:
                            with open(args.output, 'w', encoding='utf-8') as f:
                                f.write(f"# {details.get('title', '')}\n\n")
                                f.write(f"- bbbs: {details.get('bbbs', '')}\n")
                                f.write(f"- 制定机关: {details.get('zdjgName', '')}\n")
                                f.write(f"- 公布日期: {details.get('gbrq', '')}\n")
                                f.write(f"- 施行日期: {details.get('sxrq', '')}\n\n---\n\n")
                                f.write(raw_text)
                            print(f"  ✅ 正文已保存: {args.output} ({len(raw_text)} 字符)")
                        else:
                            print(f"  ⚠️ OFD正文提取失败，已保存元数据")
                    else:
                        print("  ❌ 无法获取详情")

        except Exception as e:
            import traceback
            print(f"运行失败: {e}")
            traceback.print_exc()
            sys.exit(1)

        # 保存搜索结果
        if all_results:
            out_json = args.output if args.output.endswith('.json') else args.output + ".json"
            with open(out_json, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 搜索结果已保存: {out_json}")

        return

    # ── 普通采集模式 ──
    if not args.target:
        parser.print_help()
        sys.exit(1)

    browser_path = find_browser()
    if not browser_path:
        print("❌ 未找到Edge/Chrome浏览器，请安装浏览器或手动指定")
        sys.exit(1)
    print(f"检测到浏览器: {browser_path}")

    headless = not args.visible

    # 判断是单个URL还是URL列表文件
    is_url = args.target.startswith(("http://", "https://"))
    urls = [args.target] if is_url else []
    if not is_url:
        with open(args.target, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip().startswith("http")]
        os.makedirs(args.output_dir, exist_ok=True)
        print(f"批量采集 {len(urls)} 个URL，输出目录: {args.output_dir}")

    try:
        print("=== 启动浏览器 ===")
        with SyncCDPClient.launch(headless=headless, browser_path=browser_path) as client:
            print("浏览器启动成功")
            for i, url in enumerate(urls):
                if is_url:
                    output = args.output
                else:
                    safe = url.replace("https://", "").replace("http://", "") \
                              .replace("/", "_").replace("?", "_")[:60]
                    output = os.path.join(args.output_dir, f"{i:03d}_{safe}.txt")
                try:
                    scrape_one(client, url, args.mode, args.wait, output)
                except Exception as e:
                    print(f"    ❌ 采集失败: {url}: {e}")
                    continue
                time.sleep(1)

        print("\n=== 采集完成 ===")

    except Exception as e:
        import traceback
        print("运行失败:", e)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()