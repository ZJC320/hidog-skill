# HiDOG Skill 1.2.1：clean-result 交付规则

发布日期：2026-09-20。仅更新 Skill 指令、交付说明与下载版本；分析核心仍为 v11.2.0-rc.1，报告脚本与 reporting-1.2.0 环境保持不变。

- 最终只交付 clean-result 下四类目录：`<文库名>_summary_by_reference/`、`html_reports/`、`plots/`、`qc_reports/`。
- 增强报告和必要最终审计先归入对应目录；确认报告、图像、数值及链接完整后，由 Agent 删除本次工作目录内的其余中间产物。
- 不删除原始输入、旧结果、软件环境或其他任务文件；失败/未完成任务保留排错资料。清理失败须明确报告。
- 该规则由调用 Skill 的 Agent 执行，不是底层 CLI 新增的自动删除功能，不追溯清理已有结果。
- 更新通用包与三个客户端包；旧版附件保留。Skill 格式和打包验证通过，本次没有执行真实结果清理或核心算法回归。

# HiDOG Skill 1.2.0：输入检查与分析报告

发布日期：2026-09-18。核心仍固定 v11.2.0-rc.1；本次不修改、重编译或公开 HiDOG 核心源码。

- 明确统一 ZIP 下载地址与 Agent 安装入口；安装同时准备 Skill、编译程序、独立的绘图环境并自测。
- 新增 analyze/validate/report 入口，完整扫描 FASTQ 配对、质量编码和格式，检查 barcode、参考、板孔表与显式布局；保留原 run 兼容入口。
- HTML 报告包括原始 Q30/N、barcode QC、每样品拆样比例、低于 1000 read pairs 的警告、每目标最终可用量、A/B/D 比例和明确规则下的疑似偏倚提示。
- 输出样品×参考编辑频率 PNG/SVG、可追溯 JSON 与 TSV；read-level 和 UMI family 独立，零分母为 N/A，未确认 A/B/D 预期不自动判均衡。
- 核心输出保持原状。新增 Python 文件仅为公开输入校验、执行协调和报表工具，不包含 HiDOG 分类算法。
- 增强报告适用于 paired FASTQ 基因编辑主流程；Hi-TOM、Vector Trace 保留原生专用报告，不伪造不适用指标。
- 264 项测试通过；真实编译程序 analyze、自测、UMI 补报告及 Windows 安装/重复执行/冲突保护通过。合成验证不代替真实实验验收；客户端模型自动触发仍需各产品会话验证。

# HiDOG Skill 1.1.0：统一自动安装

发布日期：2026-09-18。分析核心保持 v11.2.0-rc.1，不修改算法、CLI 或报表。

- 用户把 [INSTALL.md](INSTALL.md) 链接交给 Agent；同一 Skill 自动注册到 Codex 或 Claude Code 对应目录，随后安装编译程序并自测。
- 新增 Bash/PowerShell 统一安装入口；相同 Skill 和已有运行环境可复用，不同内容的同名 Skill 保留并报错。
- 自测实际核对两份 Stats 为40/20/50%，并检查 Excel/HTML 报告存在；失败保留日志，不会仅凭进程退出成功就声称安装通过。
- 252 项测试通过；真实 Windows PowerShell → WSL 的安装、自测、重复运行与用户修改保护通过。客户端模型自动触发仍需在各自会话中确认。
- 从空的程序目录开始完成核心公开下载、摘要校验、独立依赖安装和自动自测，返回 `SELFTEST PASS`。
- 既有独立编译版的15种模式/274份报表等价验证继续适用，核心程序没有重构或重新编译。

下面保留首个编译分发版本的记录。

# HiDOG 核心分发 v11.2.0-rc.1

发布日期：2026-09-18（Asia/Shanghai）。首个候选分发版本，核心为 HiDOG V11.2 / 11.2.0。

## 本次交付

- 通用 `hidog` Skill、联网安装器、输入与结果解释说明、40 对 reads 的合成自测数据。
- Linux x86_64 standalone 编译程序；安装器要求 glibc >= 2.31，不需要系统 Python 或 sudo。
- 使用固定依赖环境，保留 BWA 0.7.19、samtools 1.23.1、Trimmomatic 0.40；安装后本地运行。
- 核心源码、字节码、生成的 C 源码、源码仓库历史和真实样品不随包分发。第三方许可证文本单独保留。
- 原有算法、频率分母、genotype 阈值、分析参数和报表格式不变。

## 验证记录

- 243 项单元测试通过（226 项既有测试、17 项分发专项测试）。
- 72 项 V11.2 继承测试通过；41 项历史测试与 V11 结果一致，其中 8 项是已有历史预期差异。
- harness / smoke 检查通过；保留 4 条既有 harness 提示。
- 编译版在 Linux mount namespace 中屏蔽原源码、原 Conda 环境和构建环境后运行，验证 15 个合成全流程用例。
- 八组 dualPE / UMI 包括 deletion、base substitution、replacement、自动重构、UMI replacement、NGG scaffold、CCN scaffold、UMI scaffold。
- 七组补充模式包括 Cas9、Cpf1、BE、单 pegRNA PE、Custom、amplicon 和 Vector Trace。
- 共比较 274 份 TSV / Excel / HTML 报表；核对 Excel 单元格、规范化后的 TSV / HTML 内容、本地图像存在及 dualPE assigned outcomes 一致性。
- 六个 HiDOG 主体文件在封装前后 SHA256 一致。第三方 pysam 仅修正编译包内的动态库引用名称，记录随二进制包提供。
- 安装器已在屏蔽源码/原 Conda 的环境中完成整包校验与独立依赖安装；安装后的统一入口再次通过同样的 15 个用例与 274 份报表对照。安装前验收使用本地成品替代 GitHub 传输，外部依赖仍从锁定的公开地址下载。

## 支持边界

已进行上述流程验证的系统是 Ubuntu 20.04 / WSL2、x86_64、glibc 2.31。其他满足最低条件的 Linux 系统仍需使用附带示例自测；这不是对所有 Linux 发行版的无条件兼容承诺。

ARM、原生 Windows、macOS 不在首版支持范围。首次安装需要访问 GitHub 和 conda-forge / bioconda 的下载地址。安装不会建立授权服务器或上传分析数据；agent/模型的数据处理方式由相应产品决定。

合成用例验证工程一致性，不代替独立实验真值、真实复杂重排准确性或集群规模性能验收。dualPE `prime-edited` 不等于完整精准产物；使用时结合 PE subtype 和完整性审计。

## 后续改进

扩大干净 Linux 发行版和集群环境的安装验证；保持版本固定与回归比较，再评估后续 V11.2 更新。使用反馈应附程序版本、脱敏日志和最小可复现示例，不公开原始测序数据。
