# 报告契约

`analyze`：全量输入检查 → 固定编译程序 → 完成状态/统计一致性检查 → HTML、TSV、PNG/SVG。任一步失败返回非零并保留日志。原生结果照常保留。

交付 `<输出目录>/skill-report/report.html`；同目录 `report.json` 记录来源、时间、配置，TSV 为复核数值，PNG/SVG 可另行排版。`input_validation.json`、`analysis.log`、`task_record.json` 位于输出目录。分享时打包整个 skill-report 目录以保留图像。

## 解释口径

1. **建库诊断**：原始 pairs、全 read 的 R1/R2 Q30/N 比例、barcode 顺序过滤计数、拆样保留率。条码质量不是整条 read 质量；没有浓度、电泳或实验标准时不自动判整批建库合格。
2. **样品/孔分配**：拆样保留 pairs、占全批拆样 pairs 的比例、占原始 pairs 的比例。低于 1000 对统一 `LOW_READS(<1000)`，包含零；1000 不警告。抽样运行须注明是抽样后的深度。没有板孔表时不猜孔位。
3. **有效分析量**：样品×目标的最终 hard-only assigned pairs 及占本样品拆样量比例。不同目标可能共享 qname，不跨目标累计为独立总量；hard_plus_rescued 不与 hard-only 相加。
4. **A/B/D**：取最终 Stats 的样品×目标×参考计数，分母为组内 A+B+D。参考和预期明确、深度足够时，按 expected 归一化比较最大/最小。零分量且总深度够时提示疑似偏倚；缺失统计行不能当零；零分母为 N/A。
5. **编辑图**：每参考跨样品 `Modified / Assigned × 100%`，标注分母 n，最多 48 样品/页，输出 PNG+SVG。总编辑率不是 dualPE 完整精准编辑效率；继续检查 PE subtype / complete 审计。
6. **UMI**：独立列出 eligible assigned families、edited families、频率与图，不混用 read-level，不把 terminal family 称为原始 molecule。

偏倚提示写“疑似扩增或分配偏倚”，结合引物、模板/拷贝数、参考适配与未分配证据解释；比例不均不能单独证明 PCR 原因。本报告不重新分类 reads、不修改 genotype。

## 为已有结果补报告

`bash scripts/agent.sh report --run-root /实际运行子目录 --output /新报告目录 [--sample-sheet ...] [--abd-design ...] [--preflight /input_validation.json]`

运行子目录包含 `resume_state.json`、`split_raw/`、`qc_reports/`、`*_summary_by_reference/`。需导出阶段完成；UMI family 开启则还需 family 阶段完成。拆样文件已清理或 Hi-TOM 没有 FASTQ 时，不能生成同一完整报告，应交付原生结果并说明缺项。未提供 preflight 时，原始 Q30/N 标为无数据。

独立 `reporting-1.2.0` 环境锁定依赖版本和 SHA256，不改变核心环境。生成报告选择新目录，失败保留日志，不覆盖旧报告。
