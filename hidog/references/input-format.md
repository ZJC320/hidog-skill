# 开始分析前收集的数据

集中询问缺失项，已有文件可以回答的不重复询问。未知建库参数不能套用示例。正式 FASTQ 分析使用 `analyze`，全量检查格式与配对，失败不启动核心。

| 输入 | 规范 |
|---|---|
| R1 / R2 | 两个不同的 `.fq.gz` 或 `.fastq.gz`；四行 FASTQ；同序同数量；ID 去除 `/1`、`/2` 后配对；序列大写 ACGTN、Phred+33，序列与质量等长 |
| 原始参考 | UTF-8 无 BOM 的未编辑 amplicon FASTA；唯一 ID 不附描述，使用 ASCII 字母、数字、`_-.`，序列 ACGTN；多个文件逐个传入，不传目录 |
| barcode | UTF-8 无 BOM 三列，无表头：`sample_id barcode_R1 barcode_R2`；空格或制表符分隔；barcode 大写 ACGT、两端长度与参数一致；样品 ID 与 barcode 组合均唯一；保留预期空孔 |
| 实验模式 | disjoint/overlap、编辑工具、guide 对应；PE/dualPE/UMI 特有输入见 [usage.md](usage.md) 和核心 `--help` |
| read layout | 明确 spacer、barcode、bridge、post-barcode spacer 长度、UMI 开关及两端长度，不能猜测 |
| 板孔表 | 按孔报告时提供表头 TSV：`sample_id plate well`；样品覆盖 barcode 表，板号+孔位唯一。无孔位时按样品 ID 报告并注明 |
| 输出与资源 | 新的绝对输出目录、可用线程；输入保持只读 |

模板：`examples/barcodes.tsv`、`examples/sample_sheet.tsv`。示例序列、样品名及布局不能替代真实实验信息。

建议向用户索取：“请提供 R1/R2、原始参考 FASTA、三列 barcode 表、编辑工具和 guide/pegRNA 设计、建库布局；按孔报告还需样品—板—孔表。判断 A/B/D 偏倚需确认三条参考、预期比例及判定规则。”

## 完整运行入口

Linux/WSL：`bash scripts/agent.sh analyze [--sample-sheet /绝对路径/samples.tsv] [--abd-design /绝对路径/abd.json] -- <HiDOG 原参数>`。

`--` 前为报告选项，后面完整传递原 CLI。除核心要求外，此入口要求显式填写 `--editing-tool`、`--spacer-length`、`--barcode-length`、`--bridge-length`、`--post-barcode-spacer-length` 和 `--umi-mode`，记录用户确认的布局。UMI 开启时另需 `--umi-length-r1`、`--umi-length-r2`，且 sample_ratio=1。

Windows 使用 `agent.ps1 -Action analyze -HidogArgs @(...)`；例如 `@('--sample-sheet','C:\data\samples.tsv','--','-i','C:\data\R1.fq.gz',...)`。每个参数/路径是独立数组项，脚本转换路径。不要将省略号直接执行。

仅检查时用 `validate`，参数相同；`analyze` 已含校验，不需重复扫描。格式检查不证明 guide 方向、参考背景或生物学设计正确；Agent 仍须核对模式要求。

## A/B/D 设计

`examples/abd_design.json` 演示预期 1:1:1、组内 assigned 总量至少 1000、归一化最大/最小大于 2 时提示的规则。这是**待用户确认的示例**，不是普适阈值，不改变 assignment 或 genotype。

按目标组填写 `references` 的 A/B/D 精确 ID、`expected` 三个正数（A/B/D 顺序）、`min_pairs`、`max_fold`。预期 1:1:2 可写 `[1,1,2]`。用户确认后才传入配置；未确认时只显示比例并标记未评估。非完整 A/B/D 组不套用三组均衡规则。

## 其他模式

Hi-TOM 导入、Vector Trace 保持 `run` 及原模式工作流，不伪造 FASTQ 建库质量、A/B/D 或编辑频率。spacer 检出不等于基因编辑。增强报告目前适用于 paired FASTQ 基因编辑主流程及其 UMI family 输出；其他模式运行前说明范围并交付原生结果。

不接受核心长选项缩写，须按 --help 写全。BOM 或小写 FASTQ 被拒绝时，可在新目录生成规范化副本并说明转换，不能覆盖原输入；随后重新检查副本。
