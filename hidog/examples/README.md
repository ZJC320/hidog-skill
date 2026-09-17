# 合成安装自测

这些文件完全由测试生成，不含真实样品。40 对 reads：20 对 WT、20 对预期 replacement。barcode 直接位于每端 read 起始处，无 spacer/bridge。这不是一般实验的推荐布局或分析阈值。

安装后，在此目录运行下面的 Linux/WSL 命令。输出目录必须尚不存在；重复自测时选择新目录。

```bash
"$HOME/.local/share/hidog/bin/hidog" \
  -t disjoint --editing-tool dualPE \
  -r reference.fa -i replacement_R1.fq.gz -I replacement_R2.fq.gz \
  -b barcodes.tsv -o ./hidog-example-results -T 1 \
  --spacer-length 0 --barcode-length 4 --bridge-length 0 \
  --prime_editing_pegRNA_spacer_seq spacers.fa \
  --prime_editing_pegRNA_extension_seq extensions.fa \
  --prime_editing_override_prime_edited_ref_seq expected.fa \
  --min-genotype-depth 1 --min-ratio 0
```

预期 Stats：Assigned reads=40，Modified reads=20，Editing frequency=50%。应同时生成 Excel、HTML 和 dualPE 审计文件。仅表示安装与合成流程正常，不能作为真实数据准确性证明。
