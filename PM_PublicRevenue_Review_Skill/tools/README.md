# 反爬浏览器采集工具

> 本目录提供已验证可用的浏览器自动化采集工具，用于**反爬严格的网站**（JS渲染型、需要Cookie会话、需要点击交互、正文在DOM中的页面）。

## 工具文件

| 文件 | 说明 | 状态 |
|---|---|---|
| `browser_scraper.py` | 通用浏览器采集工具（基于cdpwave，驱动Edge/Chrome） | ✅ 已验证 |
| `legal_fulltext_fetcher.py` | 法规全文批量下载工具（基于flk.npc.gov.cn，含常用法规ID映射表） | ✅ 已验证 |
| `provincial_law_fetcher.py` | **省级法规库合规采集工具**（各省人大/司法厅法规库，已验证湖南） | ✅ 已验证 |
| `hunan_batch_fetch.py` | **湖南省法规库批量采集工具**（支持配置多个法规清单） | ✅ 已验证 |
| `gen_version_diff.py` | 法规版本差异分析工具（新旧版本条款对比，供P13审查） | ✅ 已验证 |
| `batch_laws_example.json` | 批量下载配置模板 | ✅ |

## 依赖

```
pip install cdpwave
pip install pywin32   # 仅老式.doc转换需要
```

无需 Node.js、无需 Selenium/Playwright、无需下载 Chromium（使用本机 Edge/Chrome）。

## 快速使用

```bash
# 提取页面正文（默认）
python browser_scraper.py "https://目标网站/页面" --output result.txt --wait 5

# 提取HTML
python browser_scraper.py "https://目标网站/页面" --mode html --output page.html --wait 5

# 截图
python browser_scraper.py "https://目标网站/页面" --mode screenshot --output shot.png --wait 8

# 生成PDF（适合法规原文存档）
python browser_scraper.py "https://目标网站/页面" --mode pdf --output law.pdf --wait 8

# 批量采集（urls.txt每行一个URL）
python browser_scraper.py urls.txt --output-dir ./scraped --wait 5

# 有头模式（可见浏览器，适合人工过验证码/登录）
python browser_scraper.py "https://目标网站/页面" --visible --wait 10

# 搜索flk法规（实验性：搜索API有反爬，建议直接用bbbs）
python browser_scraper.py --search "物业管理条例" --flk

# 批量下载法规全文（推荐方式）
python legal_fulltext_fetcher.py --bbbs ff808181796a636a0179822a19640c92 --name "刑法" --output database/national/law/刑法_全文.txt

# 对比新旧版本法规差异（P13审查辅助）
python tools/gen_version_diff.py --old database/municipal/杭州市物业管理条例_全文_完整版.txt \
    --new database/municipal/杭州市物业管理条例_2026_全文_完整版.txt \
    --output projects/法规版本对比示例_杭州2024vs2026.md \
    --old-name "2024版" --new-name "2026版"
```

## 参数说明

| 参数 | 默认值 | 说明 |
|---|---|---|
| `target` | 必填 | URL 或 包含URL列表的txt文件 |
| `--output` | `result.txt` | 单URL采集的输出文件 |
| `--output-dir` | `./scraped` | 批量采集的输出目录 |
| `--mode` | `text` | `text` / `html` / `screenshot` / `pdf` |
| `--wait` | `5` | SPA渲染等待秒数（建议8-10） |
| `--visible` | 关闭 | 有头模式，人工过验证码时使用 |

## 适用场景

1. **政府网站法规下载**：国家法律法规数据库、各省住建厅、裁判文书网
2. **JS渲染型网站**：正文由前端JS动态加载，curl/urllib拿不到
3. **需要Cookie会话**：网站要求登录后访问（可用 `--visible` 人工登录后会话保持）
4. **需要点击交互**：通过页面的搜索/翻页/展开按钮获取内容

## 反爬策略说明

本工具采用**真实浏览器渲染**策略（CDP协议直连），相比requests/urllib的优势：
- 完整执行JavaScript，获取动态渲染内容
- 使用真实浏览器指纹（User-Agent、TLS指纹、Canvas等）
- 支持headless与有头模式
- 可配合人工介入（验证码、登录）后保持会话

## 已验证案例

| 目标 | 模式 | 结果 |
|---|---|---|
| flk.npc.gov.cn（国家法律法规数据库） | text/html/screenshot/pdf | ✅ 全部成功 |
| flk.npc.gov.cn 法规详情页（OFD iframe） | text（isolated world） | ✅ 元数据+部分正文 |
| flk.npc.gov.cn 法规 Word 原件 | download/pc 接口 | ✅ 21部法规完整全文 |
| 老式 .doc 格式法规 | Word COM 转换 | ✅ 4部（江苏/湖北/河南/无锡） |
| wenshu.court.gov.cn（中国裁判文书网） | text | ✅ 成功 |

## flk 搜索接口技术笔记（2026-10-11 实测）

**可用接口**：
- `GET /law-search/search/flfgDetails?bbbs=xxx` → 法规元数据+内容树 ✅
- `GET /law-search/download/pc?format=docx&bbbs=xxx` → Word原件下载地址 ✅
- `GET /law-search/amazonFile/ofdGenerateLink?filePath=xxx` → OFD预览链接 ✅
- `GET /law-search/prompts/search?title=xxx` → 搜索建议词 ✅
- `GET /law-search/index/aggregateData` → 分类统计+新法速递 ✅

**反爬限制**：
- `POST /law-search/search/list` → 直接fetch返回"系统异常"500（有服务端签名/参数校验）
- `POST /law-search/highSearch/highSearch` → 同上
- `POST /law-search/search/xgzl` → 参数异常500
- 搜索框交互需要模拟真实输入+点击，无法简单通过API调用

**实用建议**：
- 优先使用 **已知 bbbs ID** 直接访问详情页（见 `database/法规bbbs_ID索引.md`）
- 获取新法规ID：从 flk 首页 `aggregateData` 的 `xfsd`/`popularSearch` 字段提取
- 司法解释等分类：目前无法自动枚举，可人工在 flk 网站搜索后记录 bbbs

## 进阶：配合 Chrome DevTools MCP / WaveXisMCP

- **Chrome DevTools MCP**（npm全局安装）：`chrome-devtools-mcp@1.10.1` 已安装，可在Claude中通过MCP直接操控Chrome
- **WaveXisMCP**（pip）：`wavexis-mcp@1.7.0` 已安装，暴露220个浏览器自动化工具、13个能力层级
- 当 `browser_scraper.py` 的自动化脚本难以处理复杂交互（多步点击、表单填写、验证码绕过后的流程）时，改用MCP方式由AI实时操控浏览器

## 注意事项（合规）

- 采集前检查目标网站 robots.txt 和用户协议
- 仅采集公开信息，不采集个人隐私
- 控制请求频率，避免对目标服务器造成压力
- 本工具用于公开法规、政策、判例等合法数据采集
## 合规警示（2026-10-11 确认）

**flk.npc.gov.cn robots.txt 明确禁止自动化采集**：
```
#禁止使用任何自动化工具、脚本、爬虫程序采集或复制网站数据
User-agent: *
Disallow: /
```

⚠️ **后续请勿再对 flk.npc.gov.cn 使用自动化采集**。
已有数据为历史轮次获取，保留用于审查工作流。
补充新法规时，请改用合规来源（各省人大/政府官网、司法部/住建部官网）。
