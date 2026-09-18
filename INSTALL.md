# 给 Agent 的 HiDOG 自动安装入口

用户只需发来这个页面并说“安装 HiDOG”。以下步骤由接到请求的 Agent 完成，不要求用户自行选包、解压、复制目录或输入终端命令。遵守宿主已有的权限要求。

## 1. 判断当前会话

- 确认你是 Codex、Claude Code 还是其他客户端，以及当前工具实际运行在 Windows、WSL 或 Linux。不能根据电脑里装了哪些软件猜测当前 Agent 身份。
- 确认有下载、文件操作和本地命令执行能力。普通聊天/手机会话没有这些工具时，说明无法在该会话完成安装；不要声称已安装。
- HiDOG 需要 Linux/WSL x86_64、glibc >= 2.31。macOS/ARM 暂不支持。Windows 先检查可用 WSL Ubuntu；未启用 WSL或需要管理员权限/重启时，明确告知具体阻塞，不能把剩余安装步骤说成完成。不要自行重启电脑。

## 2. 下载同一个固定安装包

- [HiDOG Skill 1.1.0 ZIP](https://github.com/ZJC320/hidog-skill/releases/download/skill-v1.1.0/hidog-skill-1.1.0.zip)
- [SHA256](https://github.com/ZJC320/hidog-skill/releases/download/skill-v1.1.0/hidog-skill-1.1.0.zip.sha256)

用客户端现有下载工具保存两个文件到新的临时目录。计算 ZIP 的 SHA256，并与摘要文件第一列的64位十六进制值比较；不一致立即停止，不绕过验证。校验后解压完整内容，阅读其中 `hidog/SKILL.md` 和将要运行的安装脚本。

这个包对 Codex 和 Claude Code 完全相同。Skill 版本为1.1.0，分析核心固定为v11.2.0-rc.1，核心下载仍由已有安装器完成。安装器访问 GitHub、conda-forge、bioconda，不从源码安装，不要求用户提供API密钥。

## 3. 注册 Skill 并安装、自测

下面的命令由 Agent 运行；占位目录替换为实际解压路径。根据自己的身份选择 `codex` 或 `claude`，无需询问用户选择客户端包。

Linux / WSL 中的 Codex：

```bash
bash '/实际解压目录/install-skill.sh' --client codex
```

Linux / WSL 中的 Claude Code：

```bash
bash '/实际解压目录/install-skill.sh' --client claude
```

Windows 本地运行的 Codex 或 Claude Code（将 `codex` 替换为当前身份）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'C:\实际解压目录\install-skill.ps1' -Client codex
```

Windows 入口只在当前进程允许运行随包脚本，不修改全局执行策略；如组织策略仍禁止执行，报告阻塞。多个 WSL 发行版时用 `wsl --list --quiet` 确认兼容发行版，传 `-Distro '已确认的名称'`，后续调用保持相同选择。

- 默认 Codex 用户目录为 `~/.agents/skills/hidog`，Claude Code 为 `~/.claude/skills/hidog`。在 Windows 运行客户端就注册到 Windows 用户目录，在 WSL 运行客户端就注册到 WSL 用户目录，二者不可混淆。
- 如果宿主自带 Skill 安装器已经指定其他目录（例如此版本 Codex 的 `$CODEX_HOME/skills`），复用该目录，给安装器传 `--skills-dir '/已确认的技能父目录'` 或 `-SkillsDir 'C:\已确认的技能父目录'`；不要再安装重复副本。
- 也可由宿主原生 Skill 安装器直接安装公开仓库的 `hidog/`，随后从已安装目录运行 `bash scripts/agent.sh setup` 或 Windows 的 `scripts/agent.ps1 -Action setup`。只下载说明文件不算安装完成。
- 其他能加载标准 Skill 的 Agent 可以使用同一 `hidog/`；只有确认它的技能目录/导入机制与本地执行能力后才注册，不猜测 WorkBuddy 或豆包的内部配置路径。客户端只能上传 ZIP 时使用其导入流程；普通聊天无法靠本文件增加执行权限。
- 相同内容的已安装 Skill 会复用；不同内容、链接或用户修改会保留并报错。报告冲突位置，不擅自覆盖用户修改。

## 4. 必须验证后再交付

统一安装器会注册 Skill、安装或复用编译程序、执行合成自测，核对两份 Stats 均为 Assigned=40、Modified=20、Editing frequency=50%，并检查 Excel/HTML 报告存在。

只有进程退出码为0且出现 `SELFTEST PASS`，才报告“安装和自测通过”。保留并告知 Skill 安装目录、运行版本、自测结果目录与日志。安装/自测失败时报告具体阶段、错误与保留的日志；不要改阈值或用伪造报告继续。

下载和环境安装可能耗时数分钟；跟踪同一进程，不重复启动。客户端未立即发现新技能时，先说明下个会话/重启客户端后检查；不要谎称已验证模型自动触发。安装完成后用户直接说“用 HiDOG 分析这些数据”即可按技能收集实验参数。

参考：[Codex 官方技能目录](https://learn.chatgpt.com/docs/build-skills)、[Claude Code 官方技能目录](https://code.claude.com/docs/en/skills)。
