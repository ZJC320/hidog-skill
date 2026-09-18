## 此客户端的本地入口

本节使用随包提供的入口完成环境检查和 Windows/WSL 路径转换。第一次使用先执行 check；未安装时执行 install，再执行 example 并核对 Stats 为 40/20/50%。首次安装需要联网。以下路径相对于本 SKILL.md，运行时替换为该文件所在的真实绝对路径。

Windows PowerShell：

```powershell
& '<skill目录>\scripts\agent.ps1' -Action check
& '<skill目录>\scripts\agent.ps1' -Action install
& '<skill目录>\scripts\agent.ps1' -Action example
& '<skill目录>\scripts\agent.ps1' -Action run -HidogArgs @('--help')
```

Linux 或已经处于 WSL 的终端：

```bash
bash '<skill目录>/scripts/agent.sh' check
bash '<skill目录>/scripts/agent.sh' install
bash '<skill目录>/scripts/agent.sh' example
bash '<skill目录>/scripts/agent.sh' run --help
```

- Windows 入口使用默认 WSL；多个发行版时选择能访问数据的 Ubuntu，并在所有调用中保持相同的 `-Distro '<名称>'`。读取 `wsl --list --quiet` 确认可用名称，不猜测名称。
- 如果 Windows 拒绝运行未签名脚本，单次进程使用 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File '<skill目录>\scripts\agent.ps1' -Action check`（install/example 同理），不修改系统执行策略。传递分析参数数组时先在该 PowerShell 进程内构造数组并调用脚本；不要把数组拼成一个字符串。组织策略仍禁止执行时停止并报告。
- Windows 运行 `-HidogArgs` 时，每个选项和值分别作为数组元素；本地盘符绝对路径自动转为 Linux 路径。不要将 `--option=value` 和 Windows 路径合并到同一参数，使用独立的选项和值。目录包含空格可正常传递。
- PowerShell 调用后立刻检查 `$LASTEXITCODE`，非零为失败。若把调用写入另一个 .ps1 启动脚本，末尾加 `exit $LASTEXITCODE`，避免外层脚本将失败误报为成功。
- 使用 Linux 入口时仅传 Linux 路径。真实分析输入/输出均用已确认的绝对路径；大型分析输出优先 WSL 内部目录。
- 找不到 WSL、使用 ARM/macOS、客户端没有本地执行工具或只允许云端执行时，明确报告环境不支持并停止；不要假称已分析，也不要擅自上传数据改走云端。
- 首次安装可能持续数分钟；用客户端进程管理查看同一个安装进程，不要重复启动。下载失败保留具体错误。已有运行环境直接复用。
- 示例结果写入用户主目录下新的 `hidog-results/example-*`；可将绝对输出目录作为 example 的唯一参数。真实实验不得沿用示例阈值。
