# 报告契约

`analyze`：全量输入检查 → 固定编译程序 → 完成状态/统计一致性检查 → HTML、TSV、PNG/SVG。任一步失败返回非零并保留日志。成功后由 Agent 执行下述 clean-result 整理和清理，再向用户交付。

整理前，增强报告位于 `<输出目录>/skill-report/report.html`，同目录包含 `report.json`、TSV、PNG/SVG；输出目录还包含 `input_validation.json`、`analysis.log`、`task_record.json`。这些是脚本生成时的位置，不能直接作为 Skill 的最终交付目录。最终增强报告入口为 `clean-result/html_reports/skill-report/report.html`，分享完整 clean-result 目录。

## clean-result 整理与清理

这是 Agent 的必需收尾步骤，不改变核心统计或现有脚本接口：

1. 确认本次所有分析进程已结束、退出成功，所有样品/目标结果与要求的增强报告生成且校验通过。先生成依赖 `split_raw`、`resume_state.json` 等的报告，不能提前删源再补报告。
2. 在本次独立输出目录内创建新的 `clean-result/`，不覆盖已有同名目录。以实际运行结果为源保留 `<文库名>_summary_by_reference/`、`html_reports/`、`plots/`、`qc_reports/`；其他路径不自动进入最终交付。
3. 将完整增强 `skill-report/` 放入 `html_reports/skill-report/`，保持其 PNG/SVG/TSV/JSON 与相对链接配套；原生图片继续放在 `plots/`。必要的运行版本、命令、输入校验、参数和任务记录归入 `qc_reports/`，记录最终路径和清理状态。解释结论必需的 dualPE/UMI 审计归入 `qc_reports/` 的对应子目录，UMI 最终 family 表归入汇总目录的独立子目录，保留单位和 scope。只保留最终统计、质控及解释依据，不把整个 UMI 工作区、reads ledger 或原始中间目录搬入其中。特殊模式的最终工作簿/检出表也归入汇总目录，不伪造不存在的编辑统计。
4. 对照原产物核对拷贝文件的数量、大小及摘要；检查 HTML 本地链接和图片在新位置可用、表格可读取，关键样品计数/频率一致、UMI 单位没有混用。修正指向旧报告位置的交付链接；来源记录中的历史中间路径注明后续已清理，不将其列为可下载结果。
5. 验证通过后，枚举本次工作目录内的待删除绝对路径，确认它们都在本次目录范围内、不包含 clean-result、输入原件、用户其他文件或指向外部的链接目标。然后删除本次产生的拆样/修剪 FASTQ、SAM/BAM/索引、比对和共识临时目录、参考工作副本、缓存、恢复状态、成功运行的临时日志，以及最终产物整理前的冗余副本。不能对项目目录、数据目录或共享输出父目录执行“除四目录外全部删除”。混有历史/其他任务文件时只删除逐项确认的本次产物。
6. 复查 clean-result 顶层只有上述四类目录，报告仍可打开、已确认的中间产物不再存在；在 `qc_reports/` 更新清理记录后交付。删除遇到权限或占用问题时保留错误信息并明确哪些未清理，不假称完成。

清理后不能依赖旧中间文件断点续跑；需要重新分析时使用保留在原位置的原始输入和新的工作目录。规则只作用于本次成功运行，不自动清理历史任务或失败任务。

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
