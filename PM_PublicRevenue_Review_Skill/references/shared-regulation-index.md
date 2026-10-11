# 共享法规引用索引（公共收益审查专家）

> 版本：v1.0 | 更新日期：2026-10-11
> 本文件指向共享法规库 `D:\A22_SKILL训练\shared-regulations\`，避免重复下载。

## 引用路径

共享法规库根目录：`../../../../shared-regulations/national/`
（从 `PM_PublicRevenue_Review_Skill/references/` 出发的相对路径）

## 常用法规

| 法规名称 | 共享库路径 | 使用场景 |
|---------|-----------|---------|
| 民法典 | `law/民法典_全文.txt` | 第282条/第943条 |
| 刑法 | `law/刑法_全文.txt` | 第271条侵占罪 |
| 人民防空法 | `law/人民防空法_全文.txt` | 人防车位 |
| 价格法 | `law/价格法_全文.txt` | 收费定价 |
| 物业管理条例 | `admin_regulation/物业管理条例_全文.txt` | 条例条款 |
| 物业服务收费管理办法 | `admin_regulation/物业服务收费管理办法.txt` | 收费办法 |
| 住宅专项维修资金管理办法 | `admin_regulation/住宅专项维修资金管理办法.txt` | 维修资金 |
| 物业承接查验办法 | `admin_regulation/物业承接查验办法.txt` | 承接查验 |
| 物业服务纠纷司法解释 | `judicial_interpretation/物业服务纠纷司法解释_全文.txt` | 司法解释 |
| 建筑物区分所有权司法解释 | `judicial_interpretation/建筑物区分所有权司法解释_全文.txt` | 区分所有权 |
| 民法典时间效力规定 | `judicial_interpretation/民法典时间效力规定_全文.txt` | 历史业务 |
| 国办函2020_129号 | `admin_regulation/国办函2020_129号.txt` | 转供电 |

## 本SKILL保留的数据

- `database/provincial/`：37份省级文件（可迁移至共享库，暂保留）
- `database/municipal/`：24城公共收益细则（暂保留）
- `data/*.json`：结构化知识（案例/市场对标/城市规则）仍在本SKILL

## 使用规范

1. 引用国家法规时，优先从共享库读取
2. 本SKILL的 `database/national/` 中原有法规文件已复制到共享库，可自行清理
