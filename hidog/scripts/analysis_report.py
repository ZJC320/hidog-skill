"""Read-only companion reports built from HiDOG exports, never allele reclassification."""
import argparse
import csv
from datetime import datetime, timezone
import html
import json
import math
from pathlib import Path

from input_checks import count_pairs, read_barcodes, read_sample_sheet


def table(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle, delimiter='\t'))


def integer(value):
    number = int(value)
    if number < 0:
        raise ValueError('Negative count in result')
    return number


def percent(numerator, denominator):
    return 100 * numerator / denominator if denominator else None


def assess_abd(counts, design):
    result = {'max_normalized_fold': None, 'status': '未评估：未确认实验预期'}
    if design is None:
        return result
    expected = design['expected']
    if len(expected) != 3 or any(not math.isfinite(x) or x <= 0 for x in expected):
        raise ValueError('A/B/D expected ratios must be three positive finite numbers')
    if design['min_pairs'] < 1 or not math.isfinite(design['max_fold']) or design['max_fold'] <= 1:
        raise ValueError('A/B/D min_pairs must be positive and max_fold must exceed 1')
    if sum(counts) < design['min_pairs']:
        result['status'] = '未评估：分配深度不足'
        return result
    normalized = [count / ratio for count, ratio in zip(counts, expected)]
    fold = max(normalized) / min(normalized) if min(normalized) else None
    result['max_normalized_fold'] = fold
    result['status'] = ('疑似扩增或分配偏倚' if fold is None or fold > design['max_fold']
                        else '未见超过设定阈值的偏倚')
    return result


def read_design(path):
    if path is None:
        return {}
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('A/B/D design must be an object keyed by target group')
    for group, design in data.items():
        if set(design['references']) != {'A', 'B', 'D'} or len(set(design['references'].values())) != 3:
            raise ValueError(f'{group}: exactly three distinct A/B/D reference IDs required')
        assess_abd([0, 0, 0], design)
    return data


def collect(root, sample_sheet=None, abd_design=None, preflight=None):
    root = Path(root).resolve()
    state = json.loads((root / 'resume_state.json').read_text(encoding='utf-8'))
    if not state.get('completed_steps', {}).get('export_reports'):
        raise ValueError('HiDOG result is not complete: export_reports missing')
    config = state.get('config', {})
    if config.get('enable_umi_family_analysis') and not state['completed_steps'].get('umi_family_analysis_v11_phase5'):
        raise ValueError('UMI family analysis is not complete')
    sources = [root / 'resume_state.json']
    context_path = root / 'analysis_context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    sources.append(context_path)
    split_files = sorted((root / 'split_raw').glob('*_1.fq'))
    if not split_files:
        raise ValueError('No split_raw paired FASTQ; cannot assess library/well depth (Hi-TOM is a separate workflow)')
    counts = {}
    for first in split_files:
        sample = first.name[:-5]
        second = first.with_name(sample + '_2.fq')
        counts[sample] = count_pairs(first, second)['pairs']
        sources.extend([first, second])
    # Keep zero-read samples in the denominator; detect missing split files when original table is available.
    barcode = config.get('barcode')
    if barcode and Path(barcode).is_file() and set(read_barcodes(barcode)) != set(counts):
        raise ValueError('Split files do not cover the original barcode sample list')
    metadata = read_sample_sheet(sample_sheet, counts)
    split_total = sum(counts.values())
    qc_path = root / 'qc_reports/barcode_qc_report.tsv'
    qc = {row['Metric']: integer(row['Count']) for row in table(qc_path)}
    sources.append(qc_path)
    written_metric = 'umi_valid_pairs_written' if config.get('umi_mode') == 'dual-primer' else 'barcode_matched_written'
    if 'total_pairs' not in qc or qc.get(written_metric, 0) != split_total:
        raise ValueError('Barcode QC and split FASTQ counts disagree or required counters are missing')
    raw_total = qc['total_pairs']
    if raw_total < split_total:
        raise ValueError('Split pairs exceed raw pairs')
    samples = [{'sample_id': sample, **metadata[sample], 'split_pairs': count,
                'library_split_percent': percent(count, split_total),
                'raw_library_percent': percent(count, raw_total),
                'warning': 'LOW_READS(<1000)' if count < 1000 else ''}
               for sample, count in counts.items()]
    editing, seen = [], set()
    paths = sorted(root.glob('*_summary_by_reference/*.stats.tsv'))
    for path in paths:
        if path.name.endswith('.hard_plus_rescued.stats.tsv'):
            continue
        sources.append(path)
        for row in table(path):
            key = row['Sample'], row['Reference']
            if key in seen or key[0] not in counts:
                raise ValueError(f'Duplicate or unknown Stats sample/reference: {key}')
            seen.add(key)
            assigned = integer(row['Assigned reads'])
            modified = integer(row['Modified reads'])
            if modified > assigned or assigned > counts[key[0]]:
                raise ValueError(f'Inconsistent final read counts: {key}')
            freq = percent(modified, assigned)
            if freq is not None:
                exported = float(row['Editing frequency'])
                if not math.isfinite(exported) or abs(exported - freq) > 0.011:
                    raise ValueError(f'Editing frequency differs from Modified / Assigned: {key}')
            editing.append({'sample_id': key[0], 'reference': key[1], 'group': row['Group'],
                            'assigned_pairs': assigned, 'modified_pairs': modified,
                            'frequency_percent': freq, 'scope': 'hard-only',
                            'support': row.get('Editing frequency support', '')})
    if not editing:
        raise ValueError('No read-level hard-only Stats')
    if {r['reference'] for r in editing} != set(context['references']):
        raise ValueError('Missing or extra reference Stats compared with analysis_context.json')
    assignment = []
    groups = sorted({row['group'] for row in editing})
    designs = read_design(abd_design)
    if set(designs) - set(groups):
        raise ValueError('A/B/D design includes unknown target groups')
    abd = []
    for group in groups:
        group_rows = [r for r in editing if r['group'] == group]
        refs = {r['reference'] for r in group_rows}
        design = designs.get(group)
        mapping = design['references'] if design else {h: group + '_' + h for h in 'ABD'}
        if design and set(mapping.values()) != refs:
            raise ValueError(f'{group}: A/B/D design does not match this group reference set')
        for sample in counts:
            rows = {r['reference']: r for r in group_rows if r['sample_id'] == sample}
            if set(rows) != refs:
                raise ValueError(f'Missing Stats row: {sample}/{group}')
            assigned = sum(r['assigned_pairs'] for r in rows.values())
            if assigned > counts[sample]:
                raise ValueError(f'Assigned counts exceed split pairs: {sample}/{group}')
            assignment.append({'sample_id': sample, 'group': group, 'assigned_pairs': assigned,
                               'split_pairs': counts[sample], 'assigned_of_split_percent': percent(assigned, counts[sample])})
            if set(mapping.values()) == refs:
                values = [rows[mapping[h]]['assigned_pairs'] for h in 'ABD']
                abd.append({'sample_id': sample, 'group': group,
                            **{h + '_pairs': n for h, n in zip('ABD', values)},
                            **{h + '_percent': percent(n, sum(values)) for h, n in zip('ABD', values)},
                            'expected': ':'.join(str(x) for x in design['expected']) if design else '未确认',
                            **assess_abd(values, design)})
            else:
                abd.append({'sample_id': sample, 'group': group, 'status': '未评估：不是明确的完整 A/B/D 组'})
    family = []
    family_path = root / 'umi_family_analysis/umi_family_results/umi_family_stats.tsv'
    if config.get('enable_umi_family_analysis'):
        sources.append(family_path)
        for row in table(family_path):
            if row['Assignment_Scope'] != 'hard':
                continue
            assigned, edited = integer(row['Assigned_UMI_Families']), integer(row['Edited_UMI_Families'])
            if edited > assigned:
                raise ValueError('Edited families exceed assigned eligible families')
            family.append({'sample_id': row['Sample'], 'reference': row['Reference'],
                           'assigned_families': assigned, 'edited_families': edited,
                           'frequency_percent': percent(edited, assigned), 'support': row['Frequency_Support']})
        if not family:
            raise ValueError('Missing hard-only family Stats')
    preflight_data = json.loads(Path(preflight).read_text(encoding='utf-8')) if preflight else None
    if preflight_data and preflight_data['fastq']['pairs'] != raw_total:
        raise ValueError('Preflight raw pair count differs from this analysis')
    sources.extend(Path(p) for p in [sample_sheet, abd_design, preflight] if p)
    return {'created_utc': datetime.now(timezone.utc).isoformat(), 'skill_version': '1.2.0',
            'run_root': str(root), 'samples': samples, 'editing': editing, 'assignment': assignment,
            'abd': abd, 'abd_design': designs, 'family': family,
            'library': {'raw_pairs': raw_total, 'split_pairs': split_total,
                        'retained_percent': percent(split_total, raw_total),
                        'sample_ratio': config.get('sample_ratio'), 'barcode_qc': qc,
                        'input_quality': preflight_data.get('fastq') if preflight_data else None},
            'warnings': ['建库质量为测序数据诊断；没有电泳/浓度数据，不能代替实验建库验收。',
                         'A/B/D 仅评估 hard-only 分配结果；分配差异也可能来自参考差异、拷贝数或分配失败，不能单凭比例断言 PCR 偏倚。',
                         '不同 target 的 assigned 数量分别报告，不跨 target 相加为独立 reads 总数。',
                         '孔位未提供时只报告样品 ID，不猜测板孔。',
                         'sample_ratio 小于 1 时拆样深度为抽样后保留量，低深度警告不等于原始建库不足。'],
            'sources': [{'path': str(p), 'bytes': p.stat().st_size, 'mtime_ns': p.stat().st_mtime_ns} for p in sources]}


def write_table(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open('x', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def display_table(rows):
    if not rows:
        return '<p>不适用或无数据。</p>'
    keys = list(dict.fromkeys(key for row in rows for key in row))
    def cell(value):
        if value is None:
            return 'N/A'
        return html.escape(f'{value:.2f}' if isinstance(value, float) else str(value))
    labels = {'sample_id': '样品', 'plate': '板号', 'well': '孔位', 'split_pairs': '拆样 pairs',
              'raw_pairs': '原始 pairs', 'retained_percent': '拆样保留率 %', 'sample_ratio': '抽样比例',
              'library_split_percent': '占全库拆样 %', 'raw_library_percent': '占原始库 %',
              'warning': '提醒', 'reference': '参考', 'group': '目标组', 'assigned_pairs': '有效分配 pairs',
              'assigned_of_split_percent': '有效/拆样 %', 'modified_pairs': '编辑 pairs',
              'frequency_percent': '编辑频率 %', 'status': '结论', 'expected': '预期 A:B:D',
              'max_normalized_fold': '归一化最大/最小', 'scope': '统计范围', 'support': '支持情况',
              'assigned_families': '有效 families', 'edited_families': '编辑 families'}
    return '<div class="scroll"><table><tr>' + ''.join('<th>' + cell(labels.get(k, k)) + '</th>' for k in keys) + '</tr>' + ''.join(
        '<tr>' + ''.join('<td>' + cell(row.get(k)) + '</td>' for k in keys) + '</tr>' for row in rows) + '</table></div>'


def render(data, output):
    # Dependency import before creating output: no apparently successful empty report on missing plotting runtime.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    figures = []
    series = [('read', data['editing'], 'assigned_pairs'), ('family', data['family'], 'assigned_families')]
    for kind, rows, depth_key in series:
        for ref_index, ref in enumerate(sorted({r['reference'] for r in rows})):
            selected = [r for r in rows if r['reference'] == ref]
            for page, start in enumerate(range(0, len(selected), 48), 1):
                part = selected[start:start + 48]
                fig, ax = plt.subplots(figsize=(max(8, len(part) * .25), 4.8))
                values = [r['frequency_percent'] if r['frequency_percent'] is not None else float('nan') for r in part]
                ax.bar(range(len(part)), values, color='#147d92')
                ax.set_xlim(-.75, max(.75, len(part) - .25))
                for index, row in enumerate(part):
                    if row['frequency_percent'] is None:
                        ax.text(index, 3, 'NA', ha='center', fontsize=7)
                ax.set_xticks(range(len(part)), [r['sample_id'] + '\nn=' + str(r[depth_key]) for r in part], rotation=90)
                ax.set_ylim(0, 105)
                ax.set_ylabel('Modified / assigned pairs (%)' if kind == 'read' else 'Edited / eligible assigned families (%)')
                ax.set_title(f'{ref} | {kind}-level | hard-only')
                ax.spines[['top', 'right']].set_visible(False)
                fig.tight_layout()
                name = f'editing_{kind}_{ref_index + 1:03}_{page:02}'
                for extension in ['png', 'svg']:
                    fig.savefig(output / (name + '.' + extension), dpi=180)
                plt.close(fig)
                figures.append((name, ref, kind))
    for key in ['samples', 'assignment', 'editing', 'abd', 'family']:
        write_table(output / (key + '.tsv'), data[key])
    (output / 'report.json').write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    lib = data['library']
    parts = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>HiDOG 分析报告</title>',
             '<style>body{font:15px system-ui;max-width:1200px;margin:40px auto;padding:0 20px;color:#17313b}h1,h2{color:#126c80}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px}td,th{border:1px solid #d7e1e5;padding:8px;text-align:left}th{background:#eef5f7}img{max-width:100%}.note{padding:14px;background:#fff5df}</style>',
             '<h1>HiDOG 分析报告</h1><p>' + html.escape(data['created_utc']) + ' · Skill 1.2.0 · hard-only</p>',
             '<p class="note">本批 ' + str(len(data['samples'])) + ' 个样品；'
             + str(sum(bool(r['warning']) for r in data['samples'])) + ' 个拆样深度低于 1000 对；'
             + str(sum(r['status'] == '疑似扩增或分配偏倚' for r in data['abd'])) + ' 个样品×目标组合提示疑似偏倚。'
             + '未评估项目不能视为通过。</p>',
             '<h2>1. 建库与测序质量</h2>', display_table([{k: lib[k] for k in ['raw_pairs', 'split_pairs', 'retained_percent', 'sample_ratio']}]),
             '<p>retained_percent = 拆样后保留 pairs / 原始 pairs。条码质量、匹配和抽样均影响保留率；顺序过滤的失败计数不能当作独立失败概率。</p>',
             display_table([{'metric': k, 'count': v} for k, v in lib['barcode_qc'].items()]),
             display_table([lib['input_quality']] if lib['input_quality'] else []),
             '<p>Q30/N 指标来自原始 FASTQ 全量检查；未进行预检查时标为无数据。没有实验验收阈值时不自动标记整批建库“合格”。</p>',
             '<h2>2. 每样品/每孔 reads 分配</h2><p>一个 R1/R2 pair 计一次。library_split_percent 的分母是本批全部拆样保留 pairs；raw_library_percent 的分母是原始 pairs。所有空孔仍保留，低于 1000 对警告，等于 1000 不警告。</p>',
             display_table(data['samples']), '<h2>3. 最终可用于编辑分析的 reads</h2>', display_table(data['assignment']),
             '<h2>4. A/B/D 分配与偏倚提示</h2><p>A/B/D 百分比的分母为同样品、同目标组 A+B+D 最终 hard-only pairs；不是全库比例。未确认预期比例、参考对应或深度不足时不判断偏倚。</p>',
             display_table(data['abd']), '<p>本次判定配置：</p><pre>' + html.escape(json.dumps(data['abd_design'], ensure_ascii=False, indent=2)) + '</pre>',
             '<h2>5. 样品编辑频率</h2><p>按样品×参考绘图；分母为最终 assigned pairs，Modified 为分子，零分母显示 NA。总编辑频率不等于 dualPE 完整精准编辑效率。</p>',
             display_table(data['editing'])]
    if data['family']:
        parts.extend(['<h2>UMI family 结果（独立统计）</h2><p>terminal UMI family 不等于原始 DNA molecule；不把 reads 阈值 1000 套用于 family 数。</p>', display_table(data['family'])])
    for name, ref, kind in figures:
        parts.append(f'<h3>{html.escape(ref)} ({kind})</h3><a href="{name}.svg">SVG</a> · <a href="{name}.png">PNG</a><br><img src="{name}.png" alt="editing frequency">')
    parts.append('<h2>限制与追溯</h2><div class="note">' + '<br>'.join(html.escape(x) for x in data['warnings']) + '</div><p>数值表：samples.tsv、assignment.tsv、editing.tsv、abd.tsv、family.tsv；来源、配置和运行时间见 report.json。原始 HiDOG 报告位于 ' + html.escape(data['run_root']) + '。</p></html>')
    (output / 'report.html').write_text('\n'.join(parts), encoding='utf-8')
    return output / 'report.html'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--sample-sheet', type=Path)
    parser.add_argument('--abd-design', type=Path)
    parser.add_argument('--preflight', type=Path)
    args = parser.parse_args()
    print(render(collect(args.run_root, args.sample_sheet, args.abd_design, args.preflight), args.output))


if __name__ == '__main__':
    main()
