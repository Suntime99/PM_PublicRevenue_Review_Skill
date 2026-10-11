# -*- coding: utf-8 -*-
"""
法规版本差异分析工具
====================
对比两部法规（旧版 vs 新版）的条款差异，用于 P13 历史业务与跨法履行审查。

用法：
    python tools/gen_version_diff.py --old database/municipal/杭州市物业管理条例_全文_完整版.txt \
        --new database/municipal/杭州市物业管理条例_2026_全文_完整版.txt \
        --output projects/法规版本对比示例_杭州2024vs2026.md \
        --old-name "2024版" --new-name "2026版"

依赖：无（仅标准库）
"""
import sys
import re
import difflib
import argparse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def read_law(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_body(text):
    """去掉Markdown头部元数据，返回正文"""
    idx = text.find('---\n\n')
    return text[idx + 5:] if idx > 0 else text


def normalize(text):
    """规范化：统一全角/半角空白、去掉冗余空格"""
    # 去掉所有空白字符（法规条款间差异常因排版空格）
    return re.sub(r'\s+', '', text)


def split_articles(body):
    """按'第X条'分割为条款字典"""
    articles = re.split(r'(?=第[一二三四五六七八九十百零]+条)', body)
    result = {}
    for a in articles:
        m = re.match(r'(第[一二三四五六七八九十百零]+条)', a)
        if m and len(a) > 20:
            key = m.group(1)
            # 若同号多条（如"第X条之一"），合并
            result[key] = result.get(key, '') + a
    return result


def main():
    parser = argparse.ArgumentParser(description='法规版本差异分析工具')
    parser.add_argument('--old', required=True, help='旧版法规txt路径')
    parser.add_argument('--new', required=True, help='新版法规txt路径')
    parser.add_argument('--output', default='版本差异报告.md', help='输出报告路径')
    parser.add_argument('--old-name', default='旧版', help='旧版名称')
    parser.add_argument('--new-name', default='新版', help='新版名称')
    args = parser.parse_args()

    old_body = extract_body(read_law(args.old))
    new_body = extract_body(read_law(args.new))

    old_articles = split_articles(old_body)
    new_articles = split_articles(new_body)

    common = set(old_articles.keys()) & set(new_articles.keys())

    # 找出实质差异的条款（规范化后比较）
    changed = []
    for k in sorted(common, key=lambda x: list(old_articles.keys()).index(x) if x in old_articles else 999):
        old_norm = normalize(old_articles[k])
        new_norm = normalize(new_articles[k])
        if old_norm == new_norm:
            continue
        # 检查差异是否仅为标点/单字符
        sm = difflib.SequenceMatcher(None, old_norm, new_norm)
        ops = [op for op in sm.get_opcodes() if op[0] != 'equal']
        # 过滤：所有差异片段都 <=1字符且为标点 → 视为无实质差异
        substantive = False
        for tag, i1, i2, j1, j2 in ops:
            if tag in ('replace', 'delete'):
                if i2 - i1 > 1:
                    substantive = True
                    break
            if tag == 'insert':
                if j2 - j1 > 1:
                    substantive = True
                    break
        if substantive:
            changed.append(k)

    lines = []
    lines.append(f'# 法规版本差异分析：{args.old_name} vs {args.new_name}')
    lines.append('')
    lines.append(f'> 分析目的：P13（历史业务与跨法履行审查）新旧版本对比。')
    lines.append(f'> 旧版文件：`{args.old}`')
    lines.append(f'> 新版文件：`{args.new}`')
    lines.append('> 分析方法：按"第X条"分条，规范化空白后 difflib 对比。')
    lines.append('')
    lines.append('## 概览')
    lines.append('')
    lines.append(f'| 指标 | {args.old_name} | {args.new_name} |')
    lines.append('|---|---|---|')
    lines.append(f'| 总条款数 | {len(old_articles)} | {len(new_articles)} |')
    lines.append(f'| 正文长度 | {len(old_body):,} 字符 | {len(new_body):,} 字符 |')
    lines.append('')
    lines.append(f'- 两版共同条款：{len(common)} 条')
    lines.append(f'- 文本有实质差异的条款：**{len(changed)} 条**')
    lines.append('')

    for k in changed:
        old = old_articles[k]
        new = new_articles[k]
        lines.append(f'## {k} 变更')
        lines.append('')

        # 规范化后对比，找差异片段
        old_norm = normalize(old)
        new_norm = normalize(new)
        sm = difflib.SequenceMatcher(None, old_norm, new_norm)
        ops = [op for op in sm.get_opcodes() if op[0] != 'equal']
        lines.append(f'**变更操作数**: {len(ops)}')
        lines.append('')

        for tag, i1, i2, j1, j2 in ops[:5]:
            old_part = old_norm[i1:i2]
            new_part = new_norm[j1:j2]
            if tag == 'replace':
                lines.append(f'- 🔄 **修改**（{len(old_part)}→{len(new_part)}字符）：')
                lines.append(f'  - 旧: {old_part[:150]}')
                lines.append(f'  - 新: {new_part[:150]}')
            elif tag == 'delete':
                lines.append(f'- ➖ **删除**（{len(old_part)}字符）：{old_part[:150]}')
            elif tag == 'insert':
                lines.append(f'- ➕ **新增**（{len(new_part)}字符）：{new_part[:150]}')
        lines.append('')

    lines.append('## 审查应用建议')
    lines.append('')
    lines.append('1. **跨法履行**：行为跨越两个版本施行期间时，按行为发生时点适用对应版本')
    lines.append('2. **重点核对**：变更条款应逐一复核其对合同/收益归属的影响')
    lines.append('3. **合同基准**：合同签订时的法规版本决定其当时效力，不得以新版追溯否定')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append(f'*生成时间：2026-10-11 | 工具：tools/gen_version_diff.py*')
    lines.append('')

    report = '\n'.join(lines)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f'✅ 报告已生成: {args.output}')
    print(f'   总条款: {len(old_articles)} → {len(new_articles)}，有差异条款: {len(changed)} 条')
    for k in changed:
        print(f'   - {k}')


if __name__ == '__main__':
    main()