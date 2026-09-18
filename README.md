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

## 分发边界

- 核心程序以编译形式提供，不附带 HiDOG 核心 Python 源文件；不提供防逆向保证。
- Skill、安装脚本和使用说明公开可读。安装器不上传分析数据；agent 自身的数据处理行为由相应产品决定。
- 目前为 v11.2.0-rc.1；实际验证范围见 Release 说明。ARM、原生 Windows、macOS 以及老于已验证 glibc 的系统不在首版支持范围。
- 包含或安装的第三方组件保留各自许可证；源码版仓库和真实数据不属于此公开分发包。
- 更新使用明确的版本号；已有分析必须保留所用版本和参数，不能用更新后的结果替换旧记录。
