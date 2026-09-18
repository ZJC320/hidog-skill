---
name: hidog
description: 在 Linux 或 Windows WSL 安装并运行 HiDOG，检查扩增子基因编辑输入，生成建库质量、每孔 reads、A/B/D 分配和编辑频率图报告；支持 dualPE、UMI 及独立的 sgRNA cassette 追踪。需要本地文件与命令执行能力。
---

# HiDOG

使用本地编译版 HiDOG 分析用户指定的数据。核心源码不随 Skill 分发。此包不依赖某个 agent 产品；不能执行终端命令时，提供可执行命令并说明尚未运行。

公开地址：[GitHub 仓库](https://github.com/ZJC320/hidog-skill) · [Agent 自动下载安装](https://github.com/ZJC320/hidog-skill/blob/main/INSTALL.md) · [Skill 1.2.0 ZIP](https://github.com/ZJC320/hidog-skill/releases/download/skill-v1.2.0/hidog-skill-1.2.0.zip)。安装须同时完成 Skill 注册、编译程序、报告环境及自测，仅复制说明不算完成。

## 安装与运行环境

用户要求安装或首次使用时，主动完成环境准备，不把可自行执行的下载/安装命令交还用户。Linux/WSL 从本 Skill 目录执行 `bash scripts/agent.sh setup`；Windows 从实际 Skill 目录执行 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File '<skill目录>\scripts\agent.ps1' -Action setup`。这会安装或复用核心及独立报告环境，并核对自测的40/20/50%结果和报告；退出码为0且出现 `SELFTEST PASS` 才能报告安装完成。结果和日志位于运行环境下 `self-tests/` 的独立目录。

Windows 多个 WSL 发行版时传 `-Distro '<已确认的名称>'` 并在后续调用沿用。真实 FASTQ 分析使用 `agent.ps1 -Action analyze -HidogArgs @('选项', '值', ...)`，Windows盘符绝对路径会转换为WSL路径；Linux使用 `agent.sh analyze --` 后接原参数。PowerShell运行后立刻检查 `$LASTEXITCODE`，外层 .ps1 包装必须 `exit $LASTEXITCODE`，不能吞掉错误。缺少WSL或受到宿主权限限制时报告实际阻塞，不擅自重启、关闭安全控制或上传数据切换云端运行。

1. 判断实际终端是 PowerShell 还是 Linux。HiDOG 必须在 Linux/WSL x86_64、glibc >= 2.31 中运行；Windows 原生和 ARM 不支持。Windows 用户先确认 WSL 已安装且可用。
2. 默认程序入口为 `$HOME/.local/share/hidog/bin/hidog`。检查 `--version`、`--help`；分析任务固定版本，勿自动升级正在使用的版本。
3. 未安装时，在 Linux/WSL 执行本 Skill 相对路径 `bash scripts/agent.sh setup`；默认安装 v11.2.0-rc.1。脚本联网下载并校验，创建用户私有依赖环境，无须 sudo。不从源码安装、不索取核心源码。
4. 安装器使用 GitHub、conda-forge、bioconda 和 PyPI（锁定报告依赖）。下载或校验失败即停止并报告日志；不要关闭证书校验、跳过哈希验证或修改系统 Python 来绕过失败。已有版本目录不覆盖，失败目录保留供诊断。
5. WSL 参数用 `/home/...` 或 `/mnt/<drive>/...` 路径。先验证路径，不把 Windows 反斜杠路径直接传给 Linux 程序。

首次使用、准备命令或解释模式输出时读取 [使用与结果说明](references/usage.md)，并以已安装程序的 `--help` 为准确参数依据。

安装后可按 [合成自测](examples/README.md) 验证 40 对 reads 的预期结果；不要将示例的布局或低深度阈值套用到真实实验。

## 分析工作流

FASTQ 分析前读取 [输入规范与模板](references/input-format.md)，收集缺失实验信息；使用 `agent.sh analyze [报告选项] -- <原 CLI 参数>` 或 Windows 的 `-Action analyze` 完成校验、分析和报告。原 `run` 保留为兼容核心入口，不自动生成增强报告；不能用它替代正常 FASTQ 工作流而漏交付报告。

结束时读取 [报告口径](references/reporting.md)，交付 HTML、TSV 和 PNG/SVG：建库诊断、每孔拆样 pairs 及全库比例、少于 1000 对警告、每目标有效量、A/B/D 分配及编辑频率图。A/B/D 预期不明或深度不足时标记未评估，不能默认实验必须 1:1:1。

- 确认用户目的、分析模式、输入文件、输出目录及线程资源。缺少会影响正确性的实验参数时询问；不能根据默认值猜测 barcode、bridge、UMI 布局或编辑工具。
- 主流程收集 gzip R1/R2 FASTQ、原始未编辑参考 FASTA、barcode 表及模式需要的 guide/primer 文件。已有 Hi-TOM 表格可走程序原有导入接口，不能代替 UMI 原始 reads。
- 检查输入存在、配对、命名关系、输出是否已存在；新分析使用新目录，不覆盖原始文件或旧结果。重跑/恢复先核对版本和输入参数。
- 运行前展示模式、输入、输出、关键建库参数和资源；用户已授权该分析时直接运行，缺少关键参数时保留待确认。优先使用绝对路径和参数列表，正确引用含空格的路径。
- 使用统一 `hidog` 入口传递原 CLI 参数。保留命令、程序版本、运行时间、日志、退出码及结果目录；大型集群任务遵守用户的调度规则，不在登录节点直接启动重分析。
- 长任务不要因为暂时没有新输出就重启。通过 agent 的进程管理能力或用户现有调度器查看进度；不能自行声称后台任务已完成。
- 非零退出码报告为失败，列出具体日志原因和下一步。禁止悄悄放宽阈值、跳过失败样本或用源码版回退。
- 完成后检查必要的 Stats、工作簿、QC、HTML/审计文件；汇总实际结果、失败样本、限制和本地文件位置。不要把 smoke test 或程序正常退出说成完整生物学验收。

## 解释边界

- read-level 正式频率来自 assigned qname 的 Modified / Total；family-level 频率使用通过过滤的 eligible assigned families。Summary 的展示比例不能替代正式频率。
- UMI 要求 `sample_ratio=1.0`；不按 reads 抽样拆散 family，不跨 sample/target 合并，terminal UMI family 不等同于一个原始 DNA molecule。
- dualPE 的 `prime-edited` 父类不等于完整精准产物；结合 `PE subtype` 和 complete 审计区分 Precise、Partial、Unresolved。
- Vector Trace 仅证明检测到 sgRNA cassette，不证明完整 T-DNA、拷贝数或目标基因编辑。
- 核心算法和 genotype 阈值由固定程序版本决定，agent 不修改它们以获得更符合预期的结果。
- 分析计算留在用户本地；默认不把 FASTQ 全文或其他大规模原始数据送入模型上下文。agent/模型本身的数据处理规则由用户所用产品决定。
