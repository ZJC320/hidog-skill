# HiDOG Skill v11.2.0-rc.1

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
