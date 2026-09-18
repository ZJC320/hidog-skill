# HiDOG 通用 Agent Skill

用于在自己的 Linux 或 Windows WSL 中安装并调用 HiDOG V11.2 编译版。需要 x86_64、glibc >= 2.31、可用 Bash/curl/tar，以及首次安装时的网络连接。安装不需要 sudo；数据在本地分析。

## 给 agent 使用

WorkBuddy、Claude Code 和豆包工作用户请先看 [客户端专用下载与安装](CLIENTS.md)。豆包工作包为兼容预览，普通聊天版不能直接执行本地 HiDOG。

将 `hidog/` 文件夹放入你的 agent 支持的 Skill 目录，或直接要求 agent 阅读 `hidog/SKILL.md`。不同产品的自动发现机制不同；本包提供通用说明，不承诺任意产品零配置接入。agent 必须能够访问数据并执行 Linux/WSL 命令。

## 手动安装

下载本仓库后，在 Linux/WSL 运行：

```bash
bash hidog/scripts/install.sh
"$HOME/.local/share/hidog/bin/hidog" --help
```

安装器下载固定 Release 并校验 SHA256，在用户目录创建独立生信工具环境。已有版本不覆盖；更换版本用 `--version`，改变安装根目录用 `--prefix`。失败下载和日志保留供检查。

安装后可使用 [40 对 reads 的合成示例](hidog/examples/README.md) 自测，预期正式 Editing frequency 为 50%。示例没有真实样品数据。

