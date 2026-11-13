"""Prepare a local analysis plan; never execute analysis without a matching confirmation.

Manifest keys: project, library, launcher, arguments (HiDOG argv list),
optional output, input_files, sample_sheet, abd_design. All paths are absolute.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def fingerprint(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def normalize_fasta(source, target):
    """Normalize only encoding/case/wrapping; never guess biological IDs or sequence."""
    records, name, sequence = [], None, []
    for line in Path(source).read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():
            continue
        if line.startswith('>'):
            if name is not None:
                records.append((name, ''.join(sequence)))
            name, sequence = line[1:].strip(), []
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', name):
                raise ValueError('Reference IDs must be unique ASCII IDs without descriptions; resolve mapping first')
        else:
            if name is None:
                raise ValueError('Reference requires FASTA headers')
            sequence.append(''.join(line.split()).upper())
    if name is not None:
        records.append((name, ''.join(sequence)))
    if not records or len({x[0] for x in records}) != len(records):
        raise ValueError('Empty or duplicate reference IDs')
    if any(not seq or set(seq) - set('ACGTN') for _, seq in records):
        raise ValueError('Invalid reference sequence')
    with Path(target).open('x', encoding='utf-8') as handle:
        handle.write(''.join(f'>{name}\n{seq}\n' for name, seq in records))


def load_profile(path):
    """Load a locally verified experiment profile, never synthetic bundled barcodes."""
    profile = json.loads(Path(path).read_text(encoding='utf-8'))
    if not profile.get('source') or not profile.get('version'):
        raise ValueError('Profile requires source and version')
    barcode = Path(profile['barcode'])
    if not barcode.is_absolute():
        barcode = (Path(path).resolve().parent / barcode).resolve()
    if not barcode.is_absolute() or digest(barcode) != profile['barcode_sha256']:
        raise ValueError('Profile barcode path/hash mismatch')
    layout = profile['layout']
    keys = ['spacer-length', 'barcode-length', 'bridge-length', 'post-barcode-spacer-length']
    if any(type(layout.get(k)) is not int or layout[k] < 0 for k in keys) or layout['barcode-length'] < 1:
        raise ValueError('Invalid profile layout')
    if layout.get('umi-mode') != 'off':
        raise ValueError('This profile loader currently supports non-UMI layouts only')
    arguments = ['-b', str(barcode)]
    for key in keys + ['umi-mode']:
        arguments += ['--' + key, str(layout[key])]
    return arguments


def check_read_motifs(r1, r2, profile):
    from input_checks import fastq_records
    from itertools import islice
    result = {}
    layout = profile['layout']
    for mate, path in [('R1', r1), ('R2', r2)]:
        motif = profile['read_motifs'][mate]
        barcode_end = layout['spacer-length'] + layout['barcode-length']
        checked = matched = 0
        for _, seq, _, _ in islice(fastq_records(path), 1000):
            checked += 1
            matched += int(seq.startswith(motif['prefix']) and
                           seq[barcode_end:].startswith(motif['post'] + motif['bridge']))
        result[mate] = {'sampled': checked, 'exact_structure_matches': matched}
        # Conservative intake warning gate, not a core analytical threshold.
        if not checked or matched / checked < 0.8:
            raise ValueError(f'{mate} does not confidently match the selected raw-read profile; clarify trimming/library variant before analysis ({matched}/{checked})')
    return result


def prepare(manifest, directory):
    from analyze import check_full_options, preflight
    manifest = dict(manifest)
    if str(manifest.get('library_method', '')).lower().replace('-', '') == 'hitom' and not manifest.get('profile'):
        manifest['profile'] = str(Path(__file__).resolve().parents[1] / 'profiles/hitom-standard-96/profile.json')
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    project = Path(manifest['project'])
    if not project.is_absolute() or not project.is_dir():
        raise ValueError('Provide the actual existing absolute project directory')
    library = manifest['library']
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', library):
        raise ValueError('Use a safe library ID')
    output = Path(manifest.get('output') or project / 'hidog-results' /
                  (library + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')))
    arguments = list(manifest['arguments'])
    if manifest.get('profile'):
        reserved = {'-b', '--barcode', '--spacer-length', '--barcode-length', '--bridge-length',
                    '--post-barcode-spacer-length', '--umi-mode'}
        if any(x.split('=', 1)[0] in reserved for x in arguments):
            raise ValueError('Do not override profile barcode/layout; select the correct profile')
        arguments += load_profile(manifest['profile'])
    if any(x in ('-o', '--outdir') or x.startswith('--outdir=') for x in arguments):
        raise ValueError('Specify output only in manifest.output')
    arguments += ['-o', str(output)]
    launcher = Path(manifest['launcher'])
    if not launcher.is_absolute() or not launcher.is_file():
        raise ValueError('Launcher must be an existing absolute file')
    help_text = subprocess.check_output([str(launcher), '--help'], text=True)
    check_full_options(arguments, help_text)
    args, audit = preflight(arguments, manifest.get('sample_sheet'), manifest.get('abd_design'))
    if manifest.get('profile'):
        profile = json.loads(Path(manifest['profile']).read_text(encoding='utf-8'))
        if profile.get('read_motifs'):
            audit['profile_structure_sample'] = check_read_motifs(args.read1, args.read2, profile)
    # Preserve exact argv, hash all declared input files plus every existing path argument.
    # Large FASTQ hashing is streaming; no raw reads enter the plan.
    files = {item['path'] for item in audit['inputs']}
    resolved_launcher = launcher.resolve()
    files.add(str(resolved_launcher))
    # Pin the resolved release, not the mutable installation-wide symlink.
    release = resolved_launcher.parent.parent
    for relative in ('VERSION', 'build-metadata.json', 'app/hidog.bin'):
        component = release / relative
        if component.is_file():
            files.add(str(component.resolve()))
    for value in arguments + manifest.get('input_files', []):
        p = Path(value)
        if p.is_absolute() and p.is_file():
            files.add(str(p.resolve()))
    for key in ('sample_sheet', 'abd_design', 'profile'):
        if manifest.get(key):
            files.add(str(Path(manifest[key]).resolve()))
    plan = {'schema': 1, 'library': library, 'launcher': str(resolved_launcher),
            'arguments': arguments, 'sample_sheet': manifest.get('sample_sheet'),
            'abd_design': manifest.get('abd_design'), 'audit': audit,
            'files': {p: digest(p) for p in sorted(files)}}
    path = directory / 'plan.json'
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
    token = fingerprint(plan)
    print(f'输入校验完成，尚未开始分析。\n文库：{library}\n结果：{output}\n请向用户展示模式、输入、布局和默认参数，等待明确确认。\n确认标识：{token}')
    return path


def run(plan_path, confirmed_digest):
    plan = json.loads(Path(plan_path).read_text(encoding='utf-8'))
    if not confirmed_digest or confirmed_digest != fingerprint(plan):
        raise ValueError('Explicit user confirmation of this exact prepared plan is required')
    for path, expected in plan['files'].items():
        if digest(path) != expected:
            raise ValueError(f'Input changed; prepare and confirm again: {path}')
    command = [sys.executable, str(Path(__file__).with_name('analyze.py')),
               '--launcher', plan['launcher']]
    for key in ('sample_sheet', 'abd_design'):
        if plan.get(key):
            command += ['--' + key.replace('_', '-'), plan[key]]
    command += ['--', *plan['arguments']]
    return subprocess.call(command)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--manifest', required=True, type=Path)
    prep.add_argument('--directory', required=True, type=Path)
    execute = sub.add_parser('run')
    execute.add_argument('--plan', required=True, type=Path)
    execute.add_argument('--confirmed-plan', required=True)
    norm = sub.add_parser('normalize-fasta')
    norm.add_argument('--source', required=True, type=Path)
    norm.add_argument('--target', required=True, type=Path)
    args = p.parse_args()
    if args.action == 'prepare':
        prepare(json.loads(args.manifest.read_text(encoding='utf-8')), args.directory)
    elif args.action == 'normalize-fasta':
        normalize_fasta(args.source, args.target)
    else:
        return run(args.plan, args.confirmed_plan)
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        raise SystemExit(1)
