"""Validate the packaged read-level report in place, without changing delivery files."""
import argparse
import csv
import json
import math
from zipfile import ZipFile
from pathlib import Path
import sys

from experience_qc import local_link_errors


def verify(root):
    root = Path(root)
    summaries = list(root.glob('*_summary_by_reference'))
    if len(summaries) != 1:
        raise ValueError('Expected one final per-reference summary directory')
    required = {summaries[0].name, 'html_reports', 'plots', 'qc_reports'}
    if {p.name for p in root.iterdir()} != required:
        raise ValueError('Unexpected clean-result layout')
    report = root / 'html_reports' / 'skill-report'
    record = json.loads((root / 'qc_reports' / 'task_record.json').read_text(encoding='utf-8'))
    if record.get('status') != 'PASS' or record.get('core_exit_code') != 0:
        raise ValueError('Core task has no successful completion record')
    data = json.loads((report / 'report.json').read_text(encoding='utf-8'))
    if not (report / 'report.html').is_file() or not (report / 'editing.tsv').is_file():
        raise ValueError('Missing final report or editing table')
    links = local_link_errors(root)
    if links:
        raise ValueError('Broken local report links:\n' + '\n'.join(links))
    samples = {r['sample_id'] for r in data['samples']}
    expected = {(r['sample_id'], r['reference']): r for r in data['editing']}
    refs = {ref for _, ref in expected}
    if not expected or len(expected) != len(data['editing']) or len(expected) != len(samples) * len(refs):
        raise ValueError('Incomplete or duplicate sample/reference rows')
    seen = set()
    for path in summaries[0].glob('*.stats.tsv'):
        if path.name.endswith('.hard_plus_rescued.stats.tsv'):
            continue
        ref = path.name[:-len('.stats.tsv')]
        workbook = summaries[0] / (summaries[0].name[:-len('_summary_by_reference')] + '_' + ref + '.xlsx')
        if not (path.parent / (ref + '.tsv')).is_file() or not workbook.is_file():
            raise ValueError(f'Missing workbook or allele table for {ref}')
        with ZipFile(workbook) as book:
            if 'xl/workbook.xml' not in book.namelist() or book.testzip():
                raise ValueError(f'Unreadable workbook for {ref}')
        with path.open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.DictReader(stream, delimiter='\t'):
                key = (row['Sample'], row['Reference'])
                e = expected.get(key)
                if key in seen or not e or key[0] not in samples or key[1] != ref:
                    raise ValueError(f'Unexpected Stats key {key}')
                freq = e['frequency_percent']
                if (e['assigned_pairs'] != int(row['Assigned reads']) or
                    e['modified_pairs'] != int(row['Modified reads']) or
                    (freq is None) != (row['Editing frequency'] == 'NA') or
                    (freq is not None and not math.isclose(freq, float(row['Editing frequency']), abs_tol=0.011))):
                    raise ValueError(f'Final Stats differ for {key}')
                seen.add(key)
    if seen != set(expected):
        raise ValueError('Missing final Stats')
    return f'{len(samples)} samples, {len(refs)} references, {len(seen)} Stats rows; local links OK'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('clean_result', type=Path)
    try:
        print(verify(parser.parse_args().clean_result))
    except (ValueError, OSError, KeyError) as exc:
        sys.exit(f'ERROR: {exc}')
