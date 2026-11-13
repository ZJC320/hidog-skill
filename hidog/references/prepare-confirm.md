# 准备、确认、分析

此入口运行在已完成 setup 的 Linux/WSL 报告环境。不是豆包客户端安装成功的证明，客户端仍需实测。

1. Agent 收集文库、建库方式、编辑工具及文件位置，从已核实的实验资料生成完整参数列表。标准无UMI原始Hi-TOM可使用 profiles/hitom-standard-96/profile.json，不能使用合成示例。
2. FASTA 规范化可使用 `python scripts/prepare_analysis.py normalize-fasta --source /绝对路径/原始.fa --target /绝对路径/新副本.fa`。只移除 BOM、规范大小写与空白，不自动重命名带描述的 ID，也不做反向互补或猜测编辑窗口。更复杂的表格/设计输入需先建立明确映射。此步骤不证明生物学设计正确。
3. 用报告环境 Python 运行 `scripts/prepare_analysis.py prepare --manifest /绝对路径/request.json --directory /绝对路径/新准备目录`。它只调用核心 help 和全量输入检查，不分析、不覆盖结果。清单字段如下：

```json
{
  "project": "/absolute/project",
  "library": "library01",
  "launcher": "/home/user/.local/share/hidog/bin/hidog",
  "arguments": ["实际完整HiDOG参数，逐项填写，不包含-o"],
  "input_files": []
}
```

`arguments` 不是上方字符串字面值，必须是按核心 help 和真实文件构成的 argv 数组。`output` 可省略；默认创建项目内 hidog-results 的唯一新路径。`sample_sheet`、`abd_design` 为可选绝对文件路径。任何附加设计输入都应作为独立绝对路径参数或放入 `input_files`，以便纳入 SHA256 校验。

4. 给用户展示文库、编辑模式、输入文件、使用的标准布局与结果位置，并明确“其余参数使用默认值，是否开始分析？”等待明确答复。
5. 只有用户确认后才运行 `scripts/prepare_analysis.py run --plan /绝对路径/准备目录/plan.json --confirmed-plan <本次确认标识>`。配置摘要或任何纳入清单的输入文件改变会拒绝执行。该标识绑定方案，不是身份认证机制；Agent 不能把自己生成的摘要当作用户授权。
6. 仍按正常 analyze 输出和 clean-result 规则验收交付。直接调用底层 analyze/run 不受此辅助入口技术拦截，但本 Skill 的对话规则同样要求明确确认。

尚需验收：真实豆包导入和触发、其它 Hi-TOM 变体、任意表格/GenBank 的自动准备与完整 guide 生物学映射。不能把本入口单元测试视为这些功能已完成。

## 外部标准 profile

manifest 设置 `library_method: "Hi-TOM"` 时自动选择内置标准96孔预设；也可提供 `profile` 的绝对 JSON 路径。该文件必须包含 `source`、`version`、`barcode` 绝对路径、`barcode_sha256` 和 `layout`。layout 包含 `spacer-length`、`barcode-length`、`bridge-length`、`post-barcode-spacer-length`、`umi-mode`。当前只支持此入口加载无 UMI 布局；UMI 输入使用明确参数。

确认使用标准无 UMI 原始 Hi-TOM reads 时，核实的普通结构为4 nt前置 spacer、4 nt barcode、1 nt后置 spacer、18 nt bridge。其准确CLI映射为 spacer-length=4、barcode-length=4、post-barcode-spacer-length=1、bridge-length=18、umi-mode=off。**只适用于未被剪切且与该标准相符的 reads**；套用前仍须抽样核对实际结构。加载器校验表的哈希和格式，并抽查每端前1000条reads的前置/间隔/bridge；精确匹配不足80%时停止并要求澄清。80%是保守输入检查门槛，不是HiDOG分析参数，也不是自动识别其它文库结构的算法。标准96孔表由原论文补充表S1/S2核对的barcode序列生成，随此候选提供；不能使用合成示例表替代。profile 中已有布局时 arguments 不得再次覆盖。

准备清单固定真实版本目录中的程序入口，并校验该版本的 launcher、VERSION、build-metadata.json 和核心二进制（存在时）。之后更新 Skill 切换全局入口不会改变已准备任务的核心版本；要采用新版需重新准备并确认。
