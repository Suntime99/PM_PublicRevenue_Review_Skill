# 反爬严格网站采集处置流程

> 本指南定义当目标网站"反爬严格"时的标准处置流程与工具选型，配合 `tools/browser_scraper.py` 使用。
> 适用场景：JS渲染型反爬、需要Cookie会话、需要点击交互、正文在DOM中、curl/urllib被拦截。

---

## 一、反爬严格程度分级与工具选型

| 等级 | 特征 | 推荐方案 | 工具 |
|---|---|---|---|
| L0 无反爬 | curl/urllib 直接返回完整HTML | 直接用 requests/urllib | — |
| L1 基础反爬 | 需要UA/Referer/Header | urllib+完整Header | 已验证 |
| L2 JS渲染 | 正文由前端JS加载，源码中无正文 | 浏览器自动化渲染 | `cdpwave`（已装） |
| L3 交互反爬 | 需点击/输入/翻页才返回数据 | 浏览器自动化+交互 | `cdpwave` + `tools/browser_scraper.py` |
| L4 会话反爬 | 需登录/Cookie/验证码 | 有头浏览器+人工介入 | `--visible` 模式 / Chrome DevTools MCP |
| L5 强反爬 | TLS指纹/行为检测/风控 | MCP实时操控+人工 | WaveXisMCP / Chrome DevTools MCP |

---

## 二、SKILL最新反爬工具链（本机状态）

| 工具 | 本机状态 | 说明 |
|---|---|---|
| **cdpwave** v3.3.0 | ✅ 已安装 | Chrome DevTools Protocol 直连，无Selenium/Playwright |
| **wavexis** v2.20.1 | ✅ 已安装 | 浏览器自动化CLI（封装cdpwave+bidiwave） |
| **wavexis-mcp** v1.7.0 | ✅ 已安装 | MCP服务器，220工具/13能力层级（即WaveXisMCP） |
| **chrome-devtools-mcp** v1.10.1 | ✅ npm全局已装 | 官方Chrome DevTools MCP |
| **shuaipotian-edge** | ⚠️ 未发现安装痕迹 | 若SKILL文档提及，需确认安装来源后使用 |
| **OmniScout** | ⚠️ 未发现安装痕迹 | 同上 |

> 说明：`cdpwave`/`wavexis`/`chrome-devtools-mcp` 已构成完整的反爬下载能力。`shuaipotian-edge` 与 `OmniScout` 如为SKILL更新中引入的新组件，本机暂未安装，安装后可补充进本表。

---

## 三、标准处置流程（五步）

### Step 1 诊断反爬类型

```python
# 快速诊断：目标网站对urllib是否直接可用
python -c "
import urllib.request
req = urllib.request.Request('目标URL', headers={'User-Agent':'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        text = r.read().decode('utf-8', 'ignore')
        print('可直接访问，正文含关键词:', '关键词' in text)
except Exception as e:
    print('urllib失败:', e)
"
```

- ✅ 可直接访问 → 用 urllib/requests（L0）
- ❌ 失败 → 进入 Step 2

### Step 2 用浏览器工具获取渲染后正文（L2）

```bash
python tools/browser_scraper.py "目标URL" --output result.txt --wait 8
```

- 正文在DOM中 → 成功，流程结束
- 页面空白/无正文 → 进入 Step 3

### Step 3 交互式采集（L3）

需要输入/点击/翻页时，使用 CDP 交互：
- 在浏览器中执行 JS 设置输入框值
- 用 `Input.dispatchMouseEvent` / `Input.insertText` 模拟真实输入
- 等待异步渲染后提取 DOM 文本

> 注意：Element UI 等框架对原生输入事件敏感，`Input.insertText` 可能不触发 v-model，需改用 JS 设置 `nativeInputValueSetter` 后派发 `input` 事件。

### Step 4 有头模式 + 人工介入（L4）

```bash
python tools/browser_scraper.py "目标URL" --visible --wait 10
```

- 浏览器窗口可见，人工处理验证码/登录
- 登录会话保持，后续页面直接访问

### Step 5 MCP 实时操控（L5）

启用 `chrome-devtools-mcp` 或 `wavexis-mcp`，由 AI 实时操控浏览器：
- 多步点击、表单填写、复杂流程
- 需保持登录态的采集
- 反爬升级时动态调整行为

---

## 四、已验证案例

| 目标网站 | 反爬等级 | 实测结果 |
|---|---|---|
| 国家法律法规数据库 flk.npc.gov.cn（首页/搜索页） | L2（SPA） | ✅ 浏览器可访问、提取正文、截图、PDF |
| 国家法律法规数据库 详情API | L3（前端签名校验） | ⚠️ 浏览器内fetch返回空，需交互式采集 |
| 中国裁判文书网 wenshu.court.gov.cn | L2（SPA） | ✅ 浏览器可访问、提取正文 |

---

## 五、合规红线（必须遵守）

1. **robots.txt 检查**：采集前检查目标网站 robots.txt，禁止采集时改走人工路径
2. **仅采集公开数据**：不采集个人隐私（身份证号、手机号、地址等）
3. **控制频率**：避免对目标服务器造成压力
4. **人工兜底**：AI 工具采集不到时，提供人工检索路径（如致电档案馆、发函申请）
5. **可追溯**：每个采集结果标注来源URL、采集时间

---

## 六、本项目中的应用

本项目（物业公共收益审查专家）的法规数据库已通过 urllib + API 采集完成（81个文件）。
当遇到以下场景时，启用本流程：

1. **补充法规全文**：省级条例正文（当前为条款速查）→ 用浏览器工具访问省人大官网下载全文
2. **判例详情**：裁判文书网单篇文书 → 用浏览器工具提取
3. **地方政策原文**：各市住建局通知附件（PDF/Word）→ 用 `--mode pdf` 下载

---

*（本指南由 data-collection-toolchain SKILL 结合本机实测生成，2026-10-11）*