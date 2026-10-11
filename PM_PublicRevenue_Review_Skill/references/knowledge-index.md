# 知识库登记表（物业公共收益审查专家）

> 版本：v2.0 | 更新日期：2026-10-11
> 本文件登记本SKILL全部知识资产，作为知识库唯一入口。编号规则：KB-PR-XX。
> 配套架构：详见 [`references/cap-capability-matrix.md`](cap-capability-matrix.md)（四层CAP能力矩阵）。

---

## 一、审查模块知识库（chapters/，KB-PR-01~14）

### Layer A/B — 场景识别与业务审查（KB-PR-01~10）

| KB编号 | 文件 | 内容 | 适用场景 | 对应CAP |
|:------:|------|------|---------|:-------:|
| KB-PR-01 | `chapters/P1_公共资源盘点与收益范围识别.md` | 公共资源盘点/收益范围 | 全面审查 | CAP-PR-02/04 |
| KB-PR-02 | `chapters/P2_收益归属判定审查.md` | 收益归属 | 归属判定 | CAP-PR-05 |
| KB-PR-03 | `chapters/P3_周边市场对标与收入合理性审查.md` | 市场对标/收入合理性 | 定价审查 | CAP-PR-06 |
| KB-PR-04 | `chapters/P4_历史趋势与波动分析.md` | 趋势/波动 | 异常识别 | CAP-PR-07 |
| KB-PR-05 | `chapters/P5_分成比例合规性审查.md` | 分成比例合规 | 分成审查 | CAP-PR-08 |
| KB-PR-06 | `chapters/P6_合理成本界定审查.md` | 合理成本 | 成本审查 | CAP-PR-09 |
| KB-PR-07 | `chapters/P7_共管账户与资金安全审查.md` | 共管账户/资金安全 | 资金审查 | CAP-PR-10 |
| KB-PR-08 | `chapters/P8_重大舞弊与侵占可能性分析.md` | 舞弊/侵占 | 舞弊审查 | CAP-PR-11 |
| KB-PR-09 | `chapters/P9_公示义务与业主知情权审查.md` | 公示义务 | 知情权 | CAP-PR-12 |
| KB-PR-10 | `chapters/P10_资源经营授权与第三方合同审查.md` | 经营授权/第三方合同 | 授权审查 | CAP-PR-13 |

### Layer C — 风险识别（KB-PR-11~14）

| KB编号 | 文件 | 内容 | 适用场景 | 对应CAP |
|:------:|------|------|---------|:-------:|
| KB-PR-11 | `chapters/P11_税务处理审查.md` | 税务处理 | 税务审查 | CAP-PR-15 |
| KB-PR-12 | `chapters/P12_地域法规时效性核验.md` | 地域法规时效 | 时效核验 | CAP-PR-01/16 |
| KB-PR-13 | `chapters/P13_历史业务与跨法履行审查.md` | 历史业务/跨法履行 | 历史审查 | CAP-PR-03/17 |
| KB-PR-14 | `chapters/P14_对手视角审查与弱点识别.md` | 对手视角/弱点 | 对抗性场景 | CAP-PR-18 |

---

## 二、结构化数据（data/，KB-PR-D01~D07）

| KB编号 | 文件 | 内容 | 用途 |
|:------:|------|------|------|
| KB-PR-D01 | `data/local_policies.json` | 11省公共收益政策核心参数 | 快速比对 |
| KB-PR-D02 | `data/market_benchmark.json` | 35类收益来源行业均价 | 市场对标 |
| KB-PR-D03 | `data/case_law.json` | 25个典型案例 | 判例引用 |
| KB-PR-D04 | `data/city_rules.json` | 24个城市公共收益细则 | 按城市检索 |
| KB-PR-D05 | `data/regional_policies.json` | 31省物业管理条例核心参数 | 地域锁定 |
| KB-PR-D06 | `data/key_legal_clauses.json` | 国家法律+司法解释+部门规章条款+6个合同范本 | 法规引用 |
| KB-PR-D07 | `data/historical_benchmark.json` | 物权法时代法规+跨法案例 | 历史审查 |

---

## 三、法规数据库（database/）

| 位置 | 内容 | 状态 |
|------|------|:----:|
| `database/national/` | 国家级法规12个（已复制到共享库） | 可清理，改用共享库 |
| `database/provincial/` | 31省条例+6个专项办法（37份） | 保留 |
| `database/municipal/` | 24个城市公共收益细则 | 保留 |
| `database/policy-knowledge/` | 7个知识库详解 | 保留 |

---

## 四、参考框架（references/）

| 文件 | 用途 | 归类 |
|------|------|------|
| `references/cap-capability-matrix.md` | CAP能力矩阵（四层） | 架构 |
| `references/adversarial-review.md` | 对手视角审查框架 | Layer C |
| `references/anti-scraping-toolkit.md` | 反爬采集 | 治理 |
| `references/commands.md` | 预设指令 | Layer A |
| `references/historical-review.md` | 历史业务审查 | Layer C |
| `references/legal-framework.md` | 法律框架 | Layer A |
| `references/output-specs.md` | 输出规范 | Layer D |
| `references/region-confirmation.md` | 地域确认 | Layer A |
| `references/risk-framework.md` | 风险分级 | Layer C |
| `references/trigger-boundary.md` | 触发边界 | Layer A |
| `references/skill-collaboration.md` | 协作登记 | 治理 |
| `references/shared-regulation-index.md` | 共享法规索引 | 治理 |

---

## 五、模板（templates/）

| 文件 | 用途 | 归类 |
|------|------|------|
| `templates/公共收益审查意见书_模板.md` | 审查意见书 | Layer D |
| `templates/公共收益审查清单_Checklist模板.md` | 审查清单 | Layer D |
| `templates/公共收益分成台账_模板.md` | 分成台账 | Layer D |
| `templates/公共资源台账_模板.md` | 资源台账 | Layer D |
| `templates/公共收益合规风险清单_模板.md` | 风险清单 | Layer D |

---

## 六、工具（tools/）

| 文件 | 用途 |
|------|------|
| `tools/browser_scraper.py` | 反爬浏览器采集工具 |
