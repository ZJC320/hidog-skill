# HiDOG 通用 Agent Skill

用于在自己的 Linux 或 Windows WSL 中安装并调用 HiDOG V11.2 编译版。需要 x86_64、glibc >= 2.31、可用 Bash/curl/tar，以及首次安装时的网络连接。安装不需要 sudo；数据在本地分析。

## 给 agent 使用

把下面一句话发给 Codex 或 Claude Code 即可，由 Agent 完成下载、安装 Skill、安装程序和自测：

> 请按照 https://github.com/ZJC320/hidog-skill/blob/main/INSTALL.md 安装 HiDOG，并完成自测。

**Codex 和 Claude Code 使用同一套 Skill、同一个安装包。** Agent 自行选择安装目录，用户不用选客户端版本。首次安装需要联网；Windows 尚未安装 WSL 时，Agent 会提示需要完成的系统步骤。

Agent 请读取 [统一自动安装入口](INSTALL.md)。其他客户端必须具备 Skill 加载和本地命令执行能力；原有 [客户端专用包](CLIENTS.md) 保留供兼容使用，豆包工作包仍为预览。

## 手动安装

下载本仓库后，在 Linux/WSL 运行：

```bash
bash hidog/scripts/install.sh
"$HOME/.local/share/hidog/bin/hidog" --help
```

安装器下载固定 Release 并校验 SHA256，在用户目录创建独立生信工具环境。已有版本不覆盖；更换版本用 `--version`，改变安装根目录用 `--prefix`。失败下载和日志保留供检查。

安装后可使用 [40 对 reads 的合成示例](hidog/examples/README.md) 自测，预期正式 Editing frequency 为 50%。示例没有真实样品数据。
