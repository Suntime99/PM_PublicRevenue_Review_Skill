# -*- coding: utf-8 -*-
"""
法规全文批量下载工具（基于flk.npc.gov.cn）

功能：
1. 通过浏览器自动化从国家法律法规数据库提取法规详情（元数据）
2. 支持OFD格式法规的文本提取（通过isolated world绕过跨域iframe）
3. 输出Markdown格式，包含元数据和正文

使用方法：
  python tools/legal_fulltext_fetcher.py --bbbs ff808181796a636a0179822a19640c92 --output database/national/law/刑法_全文.txt

批量模式：
  python tools/legal_fulltext_fetcher.py --batch laws_batch.json

依赖：
  pip install cdpwave
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    from cdpwave.sync import SyncCDPClient
except ImportError:
    print("错误: 需要安装 cdpwave 库")
    print("运行: pip install cdpwave")
    sys.exit(1)

# Edge浏览器路径
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# 常用法规bbbs ID映射表（物业公共收益审查相关）
# 验证状态：✅ 已验证（从数据库文件提取）
LAW_BBBS_MAP = {
    # 国家级法律
    "刑法": "ff808181796a636a0179822a19640c92",  # ✅
    "民法典": "ff808081729d1efe01729d50b5c500bf",  # ✅
    "人民防空法": "2c909fdd678bf17901678bf6fd390523",  # ✅
    "价格法": "2c909fdd678bf17901678bf5e05801ef",  # ✅

    # 行政法规
    "物业管理条例": "ff8080816f3cbb3c016f40daebf30779",  # ✅

    # 省级物业管理条例
    "北京市物业管理条例": "ff8081818e750bc6018ef52824412e07",  # ✅
    "上海市住宅物业管理规定": "ff8081818d736dae018d786cda671707",  # ✅
    "江苏省物业管理条例": "ff8081817cbae136017ccb1bc36f505e",  # ✅
    "浙江省物业管理条例": "ff8081819b697249019b913bff0e4202",  # ✅
    "广东省物业管理条例": "ff8081818c24e05b018c5d2c34971bef",  # ✅
    "四川省物业管理条例": "ff8081817d5567ce017d752c64da1a18",  # ✅
    "河南省物业管理条例": "ff8081817b2f490f017b3356cd8c0612",  # ✅
    "湖北省物业服务和管理条例": "ff8080816facb59c016fb2a4f2360dbd",  # ✅
    "江西省物业管理条例": "ff8081819b697220019bc4daf9611464",  # ✅
    "福建省物业管理条例": "ff8081818a1cb546018a219067b70d82",  # ✅

    # 市级物业管理条例
    "南京市住宅物业管理条例": "ff8081819150415e01919d5ba4fb6f37",  # ✅
    "杭州市物业管理条例": "ff8081818f19d3bc018f2cbd7ebc3f69",  # ✅
    "成都市物业管理条例": "ff8081818f19d3bc018f290bb414323d",  # ✅
    "武汉市物业管理条例": "ff8081819a7c97b2019ab8f8b3204d61",  # ✅
    "无锡市物业管理条例": "ff8081817cbadfae017cc5fc5d783a3d",  # ✅
    "西安市物业管理条例": "ff8081819150458d019193468ba31c1c",  # ✅

    # 待补充的法规（需从flk搜索获取正确ID）
    "城市房地产管理法": None,  # ⚠️ 需验证
    "城乡规划法": None,  # ⚠️ 需验证
    "物业服务收费管理办法": None,  # ⚠️ 需验证
    "物业承接查验办法": None,  # ⚠️ 需验证
    "住宅专项维修资金管理办法": None,  # ⚠️ 需验证
}


def fetch_law_details(client, bbbs, timeout=30000):
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
                return fetch('/law-search/search/flfgDetails?bbbs={bbbs}', {{
                    headers: {{'Accept': 'application/json'}}
                }})
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


def download_law_docx(client, bbbs, save_path, timeout=30000):
    """
    通过download/pc接口下载法规Word原件（.docx）
    返回：True/False
    """
    try:
        with client.new_page(f'https://flk.npc.gov.cn/detail?id={bbbs}') as page:
            page.wait_for_load_state("load", timeout=timeout)
            time.sleep(8)

            # 获取下载URL
            js = f'''
            (async () => {{
                const resp = await fetch('/law-search/download/pc?format=docx&bbbs={bbbs}');
                const d = await resp.json();
                return d.data.url;
            }})()
            '''
            r = page.runtime.evaluate(js, await_promise=True, return_by_value=True)
            download_url = r.get('result', {}).get('value', '')

            if not download_url:
                print("    ❌ 未获取到下载URL")
                return False

            # 用Python下载
            import urllib.request
            req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=120)
            data = resp.read()

            if not data.startswith(b'PK'):  # ZIP/DOCX magic
                print(f"    ⚠️ 下载内容不是docx (前8字节: {data[:8]})")
                return False

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(data)
            print(f"    ✅ 已下载Word原件: {save_path} ({len(data)} 字节)")
            return True
    except Exception as e:
        print(f"    ❌ 下载Word原件失败: {e}")
        return False


def extract_docx_text(docx_path):
    """从docx文件中提取纯文本（不依赖外部库，仅用zipfile+xml）"""
    import zipfile
    import xml.etree.ElementTree as ET

    try:
        with zipfile.ZipFile(docx_path) as z:
            xml_content = z.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            texts = []
            for p in tree.findall('.//w:p', ns):
                line = ''.join(t.text for t in p.findall('.//w:t', ns) if t.text)
                if line.strip():
                    texts.append(line.strip())
            return '\n'.join(texts)
    except Exception as e:
        print(f"    ❌ 解析docx失败: {e}")
        return None


def convert_doc_to_docx(doc_path, docx_path):
    """
    用Word COM将老式.doc转换为.docx
    返回：True/False
    """
    import os
    try:
        import win32com.client
    except ImportError:
        print("    ⚠️ 需要安装 pywin32: pip install pywin32")
        return False

    doc_path = os.path.abspath(doc_path)
    docx_path = os.path.abspath(docx_path)

    try:
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False
        try:
            doc = word.Documents.Open(doc_path)
            doc.SaveAs2(docx_path, FileFormat=16)  # 16 = .docx
            doc.Close()
            print(f"    ✅ 已转换 {os.path.basename(doc_path)} → .docx")
            return True
        except Exception as e:
            print(f"    ❌ Word转换失败: {e}")
            return False
        finally:
            word.Quit()
    except Exception as e:
        print(f"    ❌ 无法启动Word COM: {e}")
        return False


def download_and_extract(client, bbbs, tmp_path):
    """
    下载法规Word原件并提取纯文本（优先docx，老式doc自动转换）
    返回：文本字符串 或 None
    """
    import urllib.request

    try:
        # 获取下载URL
        with client.new_page(f'https://flk.npc.gov.cn/detail?id={bbbs}') as page:
            page.wait_for_load_state("load", timeout=30000)
            time.sleep(6)

            js = f'''
            (async () => {{
                const resp = await fetch('/law-search/download/pc?format=docx&bbbs={bbbs}');
                const d = await resp.json();
                return d.data.url;
            }})()
            '''
            r = page.runtime.evaluate(js, await_promise=True, return_by_value=True)
            download_url = r.get('result', {}).get('value', '')

            if not download_url:
                print("    ❌ 未获取到下载URL")
                return None

            # 下载文件
            req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=120)
            data = resp.read()

            # 判断格式
            if data.startswith(b'PK'):
                # docx（ZIP格式）
                with open(tmp_path, 'wb') as f:
                    f.write(data)
                return extract_docx_text(tmp_path)
            elif data[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
                # 老式.doc（OLE2格式），用Word COM转换
                doc_path = tmp_path + '.doc'
                with open(doc_path, 'wb') as f:
                    f.write(data)
                docx_path = tmp_path + '_conv.docx'
                if convert_doc_to_docx(doc_path, docx_path):
                    text = extract_docx_text(docx_path)
                    try:
                        os.remove(doc_path)
                        os.remove(docx_path)
                    except:
                        pass
                    return text
                return None
            else:
                print(f"    ⚠️ 未知文件格式: {data[:8].hex()}")
                return None
    except Exception as e:
        print(f"    ❌ 下载失败: {e}")
        return None


def extract_ofd_text(client, bbbs, timeout=30000):
    """
    从flk法规的OFD iframe提取文本（通过isolated world绕过跨域）
    注意：OFD为Canvas渲染，文本按字符分隔，需后处理。
    返回：(raw_text, success_bool)
    """
    try:
        with client.new_page(f'https://flk.npc.gov.cn/detail?id={bbbs}') as page:
            page.wait_for_load_state("load", timeout=timeout)
            time.sleep(12)

            # 获取frame树
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


def format_law_text(raw_text, metadata):
    """格式化文本为Markdown"""
    lines = []
    lines.append(f"# {metadata.get('title', '未知标题')}（全文）")
    lines.append("")
    lines.append(f"- **来源**: 国家法律法规数据库（flk.npc.gov.cn）")
    lines.append(f"- **bbbs**: {metadata.get('bbbs', '')}")
    lines.append(f"- **制定机关**: {metadata.get('zdjgName', '')}")
    lines.append(f"- **公布日期**: {metadata.get('gbrq', '')}")
    lines.append(f"- **施行日期**: {metadata.get('sxrq', '')}")
    lines.append(f"- **时效状态**: ✅ 现行有效")
    lines.append(f"- **效力层级**: {metadata.get('flxz', '法律')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    if raw_text:
        # 清理OFD格式的特殊换行
        text = re.sub(r'\n+', '\n', raw_text)
        lines.append(text)
    else:
        lines.append("*（全文提取失败，请手动访问网站获取）*")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='法规全文批量下载工具')
    parser.add_argument('--bbbs', help='法规ID（bbbs）')
    parser.add_argument('--name', help='法规名称（用于生成文件名）')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--batch', help='批量处理JSON文件')
    parser.add_argument('--timeout', type=int, default=30, help='超时时间（秒）')

    args = parser.parse_args()

    # 批量模式
    if args.batch:
        with open(args.batch, 'r', encoding='utf-8') as f:
            laws = json.load(f)

        for law in laws:
            bbbs = law.get('bbbs')
            name = law.get('name', bbbs)
            output = law.get('output', f'database/national/law/{name}_全文.txt')

            print(f"\n=== 处理: {name} ===")
            fetch_and_save(bbbs, output)
        return

    # 单个法规
    if args.bbbs:
        name = args.name or args.bbbs[:8]
        output = args.output or f'database/national/law/{name}_全文.txt'
        fetch_and_save(args.bbbs, output)
        return

    # 使用内置映射表
    if not args.bbbs:
        print("请提供 --bbbs 或 --batch 参数")
        print("\n可用法规:")
        for name, bbbs in LAW_BBBS_MAP.items():
            print(f"  {name}: {bbbs}")
        return

    parser.print_help()


def fetch_and_save(bbbs, output_path):
    """获取法规并保存到文件"""
    try:
        with SyncCDPClient.launch(headless=True, browser_path=EDGE_PATH) as client:
            # 获取详情
            print(f"正在获取元数据...")
            details = fetch_law_details(client, bbbs)
            if not details:
                print("无法获取法规详情")
                return

            # 方式1：下载Word原件并提取全文（推荐，可获完整文本）
            print(f"正在下载Word原件...")
            tmp_path = output_path + ".tmp"
            raw_text = download_and_extract(client, bbbs, tmp_path)
            # 清理临时文件
            for suffix in ['', '.doc', '_conv.docx']:
                try:
                    os.remove(tmp_path + suffix)
                except:
                    pass

            # 方式2（兜底）：从OFD iframe提取
            if not raw_text:
                print(f"正在尝试OFD iframe提取...")
                raw_text, _ = extract_ofd_text(client, bbbs)

            # 格式化
            text = format_law_text(raw_text, details)

            # 保存
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)

            print(f"已保存: {output_path} ({len(text)} 字符)")
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
