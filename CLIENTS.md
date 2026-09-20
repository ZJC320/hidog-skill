# HiDOG 客户端下载与安装

**优先使用 [统一自动安装入口](INSTALL.md)**：把链接交给 Agent，说“安装 HiDOG 并自测”，由它完成安装。Codex、Claude Code 共用同一份 Skill，无需用户选择专用包。以下1.2.1包用于需要 ZIP 导入的客户端；旧1.0.0附件仍保留在历史 Release。

客户端适配包版本为 **1.2.1**，分析核心仍固定为 **v11.2.0-rc.1**，未修改算法或输出。

| 客户端 | 下载 | 开始使用 |
| --- | --- | --- |
| WorkBuddy | [专用 ZIP](https://github.com/ZJC320/hidog-skill/releases/download/skill-v1.2.1/hidog-workbuddy-1.2.1.zip) | 技能 → 添加技能 → 上传技能，选择 ZIP，启用后要求安装和自测 |
| Claude Code | [专用 ZIP](https://github.com/ZJC320/hidog-skill/releases/download/skill-v1.2.1/hidog-claude-code-1.2.1.zip) | 解压；Windows 双击 install-claude.cmd；Linux/WSL 执行 bash install-claude.sh；在 Claude Code 输入 /hidog |
| 豆包工作电脑版 | [兼容预览 ZIP](https://github.com/ZJC320/hidog-skill/releases/download/skill-v1.2.1/hidog-doubao-work-preview-1.2.1.zip) | 仅面向有自定义技能导入与本地执行能力的工作模式；在技能管理上传后选择本地电脑，要求安装和自测。客户端导入尚待验证 |

普通豆包聊天网页/手机聊天没有本包需要的本地执行入口时，不能直接使用。豆包模型 API、豆包工作、普通豆包聊天不是同一种接入方式。此预览不承诺所有豆包版本兼容。

## 运行前提

- Intel/AMD 64 位；Linux x86_64、glibc >= 2.31，或 Windows 已安装并初始化兼容的 WSL Ubuntu。
- 首次安装需要访问 GitHub、conda-forge、bioconda、PyPI；后续计算在本地进行。需要客户端允许读取文件和执行命令。
- 未安装 WSL 时需要先完成系统安装，可能需要管理员权限和重启；下载 ZIP 不能免除系统条件。
- macOS、ARM、原生 Windows 执行分析不受本版支持。
- ZIP 中的说明与启动脚本公开可见，HiDOG 核心只分发编译程序。数据不会由安装器上传；模型读取的数据由各客户端自身规则决定。

## 给客户端的第一句话

“使用 HiDOG 技能，检查本地环境。如果尚未安装，请安装编译版并运行合成自测；核对 Assigned=40、Modified=20、Editing frequency=50%，告诉我结果位置。”

正式分析时再提供真实数据位置和实验布局，不使用示例的低深度阈值。已有同名 Claude Skill 不会被覆盖；请先保留旧技能，再处理名称冲突。

## 验证范围

已验证底层 Windows PowerShell → WSL 入口、包含空格的安装路径、Linux 命令执行、失败返回和旧结果保护，并用编译程序运行合成示例。打包结构按公开说明制作。未在登录后的 WorkBuddy、Claude Code、豆包工作客户端执行导入和模型触发，不能把入口测试当作客户端端到端测试。

## 接入依据

- [WorkBuddy 官方技能格式](https://open.workbuddy.cn/docs/skill)、[技能导入说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。
- [Claude Code 官方 Skills 文档](https://code.claude.com/docs/en/skills)。
- [豆包工作官网](https://www.doubao.com/work)：普通豆包聊天与工作产品需分别判断；未取得可验证的公开导入契约，因此豆包包标记为兼容预览并先检测本地能力。

资料核对日期：2026-09-18。
