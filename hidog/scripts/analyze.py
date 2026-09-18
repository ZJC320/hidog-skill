"""Validate paired FASTQ inputs, run the fixed binary, and assemble a local report."""
import argparse
from datetime import datetime, timezone
import json
import re
from pathlib import Path
import subprocess
import sys

from input_checks import count_pairs, read_barcodes, read_fasta, read_sample_sheet
from analysis_report import collect, percent, read_design, render


def check_full_options(arguments, help_text):
    # Core argparse permits abbreviations. Do not let an unchecked --outdi, --barc, etc.
    # override the exact options validated by this companion parser.
    allowed = set(re.findall(r'--[A-Za-z][A-Za-z0-9_-]*', help_text))
    for argument in arguments:
        if argument.startswith('--') and argument != '--' and argument.split('=', 1)[0] not in allowed:
            raise ValueError(f'Use an exact option from the fixed core --help, no abbreviations: {argument}')


def preflight(arguments, sample_sheet=None, abd_design=None):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument('-i', '--read1', type=Path, required=True)
    parser.add_argument('-I', '--read2', type=Path, required=True)
    parser.add_argument('-r', '--reference', type=Path, nargs='+', required=True)
    parser.add_argument('-b', '--barcode', type=Path, required=True)
    parser.add_argument('-o', '--outdir', type=Path, required=True)
    parser.add_argument('-t', '--type', choices=['disjoint', 'overlap'], required=True)
    parser.add_argument('--editing-tool', '--nuclease', required=True)
    for option in ['spacer-length', 'barcode-length', 'bridge-length', 'post-barcode-spacer-length']:
        parser.add_argument('--' + option, type=int, required=True)
    parser.add_argument('--umi-mode', choices=['off', 'dual-primer'], required=True)
    parser.add_argument('--sample-ratio', type=float, default=1)
    parser.add_argument('--umi-length-r1', type=int)
    parser.add_argument('--umi-length-r2', type=int)
    args, remaining = parser.parse_known_args(arguments)
    if args.outdir.exists() or args.outdir.is_symlink() or not args.outdir.is_absolute():
        raise ValueError('Use a new absolute output directory; old results are never overwritten')
    if not 0 < args.sample_ratio <= 1:
        raise ValueError('sample_ratio must be in (0, 1]')
    if args.umi_mode == 'dual-primer' and (args.sample_ratio != 1 or
            not args.umi_length_r1 or not args.umi_length_r2 or min(args.umi_length_r1, args.umi_length_r2) < 1):
        raise ValueError('UMI requires sample_ratio=1 and explicit positive UMI lengths for both mates')
    if min(args.spacer_length, args.bridge_length, args.post_barcode_spacer_length) < 0 or args.barcode_length < 1:
        raise ValueError('Invalid read layout lengths')
    for path in [args.read1, args.read2, args.barcode, *args.reference]:
        if not path.is_absolute() or not path.is_file():
            raise ValueError(f'Provide an existing absolute file path (expand reference directories): {path}')
    if args.read1.resolve() == args.read2.resolve():
        raise ValueError('R1 and R2 must be different files')
    if not str(args.read1).endswith('.gz') or not str(args.read2).endswith('.gz'):
        raise ValueError('The analysis workflow requires paired gzip FASTQ (.fq.gz / .fastq.gz)')
    samples = read_barcodes(args.barcode, args.barcode_length)
    refs = read_fasta(args.reference)
    metadata = read_sample_sheet(sample_sheet, samples)
    designs = read_design(abd_design)
    if any(set(design['references'].values()) - set(refs) for design in designs.values()):
        raise ValueError('A/B/D design references are absent from the supplied FASTA')
    print('Checking all FASTQ records, mate IDs and Phred+33 quality ...', flush=True)
    fastq = count_pairs(args.read1, args.read2, quality=True)
    if not fastq['pairs']:
        raise ValueError('Empty raw FASTQ pair')
    for mate in ['R1', 'R2']:
        fastq[mate + '_Q30_percent'] = percent(fastq[mate + '_Q30_bases'], fastq[mate + '_bases'])
        fastq[mate + '_N_percent'] = percent(fastq[mate + '_N_bases'], fastq[mate + '_bases'])
    return args, {'checked_utc': datetime.now(timezone.utc).isoformat(), 'fastq': fastq,
                  'references': refs, 'samples': metadata, 'abd_design': designs,
                  'arguments': arguments,
                  'inputs': [{'path': str(p.resolve()), 'bytes': p.stat().st_size, 'mtime_ns': p.stat().st_mtime_ns}
                             for p in [args.read1, args.read2, args.barcode, *args.reference]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launcher', type=Path, required=True)
    parser.add_argument('--sample-sheet', type=Path)
    parser.add_argument('--abd-design', type=Path)
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('hidog_args', nargs=argparse.REMAINDER)
    options = parser.parse_args()
    arguments = options.hidog_args
    if arguments[:1] == ['--']:
        arguments = arguments[1:]
    help_text = subprocess.check_output([str(options.launcher), '--help'], text=True)
    check_full_options(arguments, help_text)
    args, audit = preflight(arguments, options.sample_sheet, options.abd_design)
    if options.validate_only:
        print(json.dumps(audit, ensure_ascii=False, indent=2))
        return 0
    version = subprocess.check_output([str(options.launcher), '--version'], text=True).strip()
    if version != 'hidogV11.2 11.2.0':
        raise ValueError(f'Unexpected core version: {version}')
    audit['core_version'] = version
    args.outdir.mkdir(parents=True, exist_ok=False)
    preflight_path = args.outdir / 'input_validation.json'
    preflight_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    record = {'request': 'HiDOG analysis with library QC, sample depth, A/B/D and editing plots',
              'started_utc': datetime.now(timezone.utc).isoformat(), 'core_version': version,
              'command': [str(options.launcher), *arguments], 'status': 'RUNNING'}
    record_path = args.outdir / 'task_record.json'
    def save():
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    save()
    try:
        with (args.outdir / 'analysis.log').open('x', encoding='utf-8') as log:
            process = subprocess.Popen(record['command'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding='utf-8', errors='replace')
            for line in process.stdout:
                log.write(line)
                log.flush()
                print(line, end='', flush=True)
            code = process.wait()
        record['core_exit_code'] = code
        if code:
            raise RuntimeError(f'HiDOG failed with exit code {code}; see analysis.log')
        states = list(args.outdir.glob('*/resume_state.json')) + list(args.outdir.glob('*/*/resume_state.json'))
        if len(states) != 1:
            raise ValueError('Expected exactly one completed HiDOG run under the new output directory')
        report = render(collect(states[0].parent, options.sample_sheet, options.abd_design, preflight_path),
                        args.outdir / 'skill-report')
        record.update(status='PASS', report=str(report), next_steps='Review low-depth/bias warnings against experimental design')
        print('ANALYSIS AND REPORT PASS: ' + str(report))
    except Exception as error:
        record.update(status='FAILED', error=str(error), next_steps='Inspect preserved logs and inputs; do not relax thresholds automatically')
        raise
    finally:
        record['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, RuntimeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
