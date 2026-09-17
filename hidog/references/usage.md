# 输入准备与结果解释

## 通用入口

Linux/WSL 示例（先确认文件确实存在）：

```bash
HIDOG="$HOME/.local/share/hidog/bin/hidog"
"$HIDOG" --version
"$HIDOG" --help
"$HIDOG" vector-trace --help
```

PowerShell 调用 WSL 时只传 Linux 路径。复杂运行命令保存为 Linux 路径下的 Bash 脚本，避免多层字符串插值。

## 必须确认的实验信息

| 情境 | 需要的输入或确认 |
|---|---|
| 所有 FASTQ 分析 | paired gzip R1/R2、原始 reference、barcode 表、实际 read layout、输出目录、线程 |
| Cas9 / Cpf1 / BE | 实际编辑工具、guide 与参考对应关系；需要时提供显式窗口，不能猜测 |
| Custom | 用户确认的切点 offset 和窗口参数；当前版本不能省略有 guide 时的 `--cleavage-offset` |
| amplicon | 目标与引物对、实验建库结构；使用当前版本 help 中的 primer 参数 |
| 单 pegRNA PE | spacer、5′→3′ RTT+PBS 和 scaffold（当前 CLI 要求提供），不要求用户手工反向互补 |
| dualPE | 两条 spacer、对应 RTT+PBS；可选 scaffold、完整编辑后 amplicon 模板 |
| dual-primer UMI | 两端有序 UMI、真实 barcode/bridge 布局；当前要求 18 bp bridge；sample_ratio=1.0 |
| Vector Trace | spacer FASTA/文本、vector anchor、barcode 表、paired gzip reads |

`-t` 的布局模式等参数应结合 `--help` 与真实实验确认。某项输入不符合程序要求时说明差异，不改写原始数据来掩盖问题。

## dualPE

- 当前支持 SpCas9 NGG 的相向延伸双 pegRNA。ID 用 `<Gene>-spacer-NGG` / `<Gene>-spacer-CCN`，两份 FASTA 的 ID 一一对应。
- spacer 为实际 pegRNA 的 20 nt、5′→3′，不含 PAM；extension 为该 pegRNA 的 RTT+PBS、5′→3′。
- NGG/CCN 按原始 reference 正链命名；A/B/D 可共用 Gene 配对，也可各自用精确 reference ID。
- 预期模板如提供，须为方向一致且背景正确的完整编辑后 amplicon，以原 reference 精确 ID 命名。不能把 A 模板当作 B/D 模板。
- 自动重构失败时请用户核对设计或提供完整模板，不能放宽门槛猜测预期产物。
- `prime-edited`、`indel byproducts`、`Scaffold-incorporated` 是非互斥 outcomes。
- 标准 allele class 中历史的 Precise 标签不单独证明 dualPE 完整性；还要看 `PE subtype` 与 `dualpe_evidence.complete`。Unresolved 不是 WT，也不是已确认的完整编辑。

## UMI

ordered UMI_R1/UMI_R2 和 target group 一起确定 family。read 和 family 输出分别报告，低支持变异保留审计但不进入正式 family 频率。不要为了增大编辑比例而减小最小 family 支持或共识门槛。

## Vector Trace

使用 `hidog vector-trace`，首选 `-s/--spacer-ref`（一个或多个 spacer 文件）；旧 `-g/--guide-manifest` 与它互斥。exact 为主，unique 1 mismatch 仅辅助；ambiguous 不分配。

期望文件：`vector_trace_summary.xlsx`（Plate_Result、Sample_Summary、QC）、`spacer_detection.tsv`、`run_parameters.json`、`sample_details/`。不生成载体/基因推断或 HiDOG_Target_List。

## 验证状态与日志

v11.2.0-rc.1 是候选分发版。分发说明分别记录工程验证和真实数据验收范围。每次运行在结果旁写任务记录：用户需求、版本、时间、命令、输入路径、结果、失败项、进一步改进计划。不能把已有文档中的 PASS 当成本次执行结果。
