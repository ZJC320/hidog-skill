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

v11.2.0-rc.4 是候选分发版。分发说明分别记录工程验证和真实数据验收范围。每次运行记录用户需求、版本、时间、命令、输入路径、结果、失败项、进一步改进计划；成功交付时将必要记录纳入 `clean-result/qc_reports/`，按 [报告整理规则](reporting.md#clean-result-整理与清理) 删除本次其余中间产物。失败任务保留排错日志。不能把已有文档中的 PASS 当成本次执行结果。

## 已有安装的明确升级

用户要求升级到本次性能优化版本时，先确认没有正在运行的分析，并记录当前 `bin/hidog` 的目标。Linux/WSL 从技能目录执行 `bash scripts/install.sh --version v11.2.0-rc.4 --prefix "$HOME/.local/share/hidog"`，成功后执行 `bash scripts/agent.sh setup`；Windows 技能文件通过已确认的 WSL 发行版执行同一安装脚本，再运行 `agent.ps1 -Action setup`。已存在 rc.4 时先核对 build-metadata.json 和自测，不重复覆盖该目录。旧 rc.1/rc.2/rc.3 目录与历史结果保留。

核心 `--version` 仍显示 `hidogV11.2 11.2.0`，不能据此区分 rc.1/rc.2/rc.3/rc.4；通过实际入口指向的版本目录、VERSION 和 build-metadata.json 核对分发版本。rc.4 核心 packages SHA256 为 `cbc6547b607f7dca9d5023d96cf6fd560c9f078285ef6c860f75131d03343807`。

本次新增ER19单PE性能验收；Cas9为rc.3已有证据，真实dualPE、历史E4的既有缺口不因本次单PE验证而关闭。单 PE 默认骨架长度为 1nt、dualPE 为 8nt，均以程序 help 和实际实验设计为准。不要重复提供 --sample-ratio；默认 1nt PE 的某库峰值约 67GB，不能把这项不同文库观察解释为阈值本身造成的内存变化。

## rc.4 单PE性能与复现范围

rc.4保留精确C affine/flank内核、延迟scaffold证据及限定单PE一次任务worker的GC策略，科学参数/归属/频率不变。ER19全量3,427,370对reads、两组6参考，16线程与**显式 `HIDOG_SUMMARY_WORKERS=16`**三次为552.603870376、603.062516518、551.118200074秒，中位552.603870376秒；三次均≤600秒标准FAIL，不保证每库十分钟。**默认summary上限仍4，未改为16**；16需按已确认CPU/内存和数据规模显式选择，不能直接照搬到资源不足的机器。

同参数全192任务、2,435,567归属decisions与1,869,940 classifications精确一致；三轮上游各768文件精确，四份编译实跑正式报告各1232文件/1152视图/0差异。原科学高层仍CPython，限定未改affine由经59,888条原CPython记录验证的PyPy执行；报告对照为修改后的native_v3检查点，不冒称纯557端到端报告重跑。没有新增真实实验真值或CRISPResso2验证，原未优化全流程中止故不提供端到端倍率。

增强报告的NA处理/ASCII校验已同步；独立生成三次37.580324918/37.688736061/37.011046262秒，原对照109.906474471秒为单次。每次重新完整校验FASTQ，报告间未清缓存；不是与核心连续计时，不能拿核心单独成绩承诺整个Agent工作流用时。原历史ER19参考标签、pegRNA、抽样和阈值不同，不是本次等价对照。scope复用试验未达预设5%门槛，未纳入生产。

## rc.3 Cas9 性能与历史结果边界（原版本记录）

rc.3分发采用44ad6cb的Cas9性能实现，复用完整依赖的计算结果、降低数据复制与编码成本，并改进任务调度；不修改正式频率、窗口、双端证据或genotype阈值。真实数据耗时依赖文库、硬件和资源，不能承诺所有文库十分钟内完成。

历史输出与当前输出的差异，不等于rc.2到rc.3提速引入的差异。早期default比对与当前cas9-sensitive比对、大indel软剪切表示、COMPOSITE_TAG_HARD归属和WT进入分母，都可能改变历史计数；应先固定同一版本和参数核对，不能把Summary展示比例当作正式频率。

已有多天然状态的无序集合问题会让部分COMPOSITE内部诊断随Python哈希种子改变；已观察7条未归属qname的最终分类不变，但不保证其他输入无影响。rc.3保留此既有行为，固定种子只用于受控比较，不是算法修复。结果差异须保留证据，不能通过变更种子挑选预期答案。
