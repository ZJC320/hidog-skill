# HiDOG 通用 Agent Skill

用于在自己的 Linux 或 Windows WSL 中安装并调用 HiDOG V11.2 编译版。需要 x86_64、glibc >= 2.31、可用 Bash/curl/tar，以及首次安装时的网络连接。安装不需要 sudo；数据在本地分析。

## 给 agent 使用

把下面一句话发给 Codex 或 Claude Code 即可，由 Agent 完成下载、安装 Skill、安装程序和自测：

> 请按照 https://github.com/ZJC320/hidog-skill/blob/main/INSTALL.md 安装 HiDOG，并完成自测。

**Codex 和 Claude Code 使用同一套 Skill、同一个安装包。** Agent 自行选择安装目录，用户不用选客户端版本。首次安装需要联网；Windows 尚未安装 WSL 时，Agent 会提示需要完成的系统步骤。

Agent 请读取 [统一自动安装入口](INSTALL.md)。其他客户端必须具备 Skill 加载和本地命令执行能力；原有 [客户端专用包](CLIENTS.md) 保留供兼容使用，豆包工作包仍为预览。

## 下载与安装

- [直接下载 HiDOG Skill 1.2.0 ZIP](https://github.com/ZJC320/hidog-skill/releases/download/skill-v1.2.0/hidog-skill-1.2.0.zip)
- [SHA256 校验文件](https://github.com/ZJC320/hidog-skill/releases/download/skill-v1.2.0/hidog-skill-1.2.0.zip.sha256)

解压后使用统一安装器，同时安装 Skill、HiDOG 程序和报告依赖，并执行自测。

Linux/WSL：`bash install-skill.sh --client codex`；Claude Code 将 codex 换为 claude。

Windows：`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install-skill.ps1 -Client codex`。多 WSL 发行版使用已确认的 `-Distro`。详细要求见 [INSTALL.md](INSTALL.md)。

已有不同版本 Skill 会保留并提示冲突；升级时先比较并备份旧目录，再用新包安装，避免丢失用户修改。程序环境可复用，旧结果不会被覆盖。

## 用户提供什么、得到什么

按 [输入规范](hidog/references/input-format.md) 提供 paired FASTQ、未编辑参考、barcode、实验布局及模式设计；按孔报告另附样品—板—孔对应表。Agent 会集中询问缺失信息并检查格式。

分析完成生成 HTML 报告、TSV 数值和 PNG/SVG 编辑频率图，包括建库/测序诊断、每孔 reads 分配、少于 1000 read pairs 提醒、每目标有效分析量、A/B/D 比例和偏倚提示。A/B/D 预期必须依据实验确认。UMI family 结果独立呈现，统计口径见 [报告说明](hidog/references/reporting.md)。

核心固定 v11.2.0-rc.1，增强报告不修改算法或原生输出。第一次安装须访问 GitHub、conda-forge、bioconda、PyPI；核心源码不随包提供，公开 Python 脚本仅做输入校验和结果汇总。
