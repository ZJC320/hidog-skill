"""Public input-format checks; contains no HiDOG analysis algorithm."""
import csv
import gzip
import itertools
import re
from pathlib import Path


def read_barcodes(path, length=None):
    samples, pairs = {}, set()
    text = Path(path).read_text(encoding='utf-8')
    if text.startswith('\ufeff'):
        raise ValueError('Barcode input must be UTF-8 without BOM for the fixed HiDOG core')
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        fields = line.split()
        if len(fields) != 3:
            raise ValueError(f'{path}:{number}: expected sample_id barcode_R1 barcode_R2, no header')
        sample, r1, r2 = fields
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', sample):
            raise ValueError(f'Unsafe sample ID: {sample}; use ASCII letters, digits, _, -, .')
        if sample in samples or (r1, r2) in pairs:
            raise ValueError(f'Duplicate sample ID or barcode pair at line {number}')
        if set(r1 + r2) - set('ACGT') or not r1 or not r2:
            raise ValueError(f'Barcodes must be uppercase ACGT: line {number}')
        if len(r1) != len(r2) or (length is not None and len(r1) != length):
            raise ValueError(f'Barcode length disagrees with layout: line {number}')
        samples[sample] = [r1, r2]
        pairs.add((r1, r2))
    if not samples:
        raise ValueError('Empty barcode table')
    return samples


def read_fasta(paths):
    records = {}
    for path in paths:
        name, sequence = None, []
        text = Path(path).read_text(encoding='utf-8')
        if text.startswith('\ufeff'):
            raise ValueError('Reference FASTA must be UTF-8 without BOM for the fixed HiDOG core')
        def save():
            if name is not None:
                seq = ''.join(sequence)
                if not seq or set(seq.upper()) - set('ACGTN'):
                    raise ValueError(f'{path}: empty/non-ACGTN reference {name}')
                if name in records:
                    raise ValueError(f'Duplicate reference ID: {name}')
                records[name] = len(seq)
        for line in text.splitlines():
            if not line.strip():
                continue
            if line.startswith('>'):
                save()
                name, sequence = line[1:].strip(), []
                if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', name):
                    raise ValueError('Use a unique ASCII FASTA ID without spaces or descriptions')
            elif name is None:
                raise ValueError(f'{path}: sequence before FASTA header')
            else:
                sequence.append(line.strip())
        save()
    if not records:
        raise ValueError('No reference sequences')
    return records


def fastq_records(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='ascii', newline='') as handle:
        number = 0
        while True:
            header = handle.readline()
            if not header:
                return
            number += 1
            seq, plus, qual = (handle.readline().rstrip('\r\n') for _ in range(3))
            if not header.startswith('@') or not plus.startswith('+') or not seq or len(seq) != len(qual):
                raise ValueError(f'{path}: invalid/truncated FASTQ record {number}')
            if set(seq) - set('ACGTN') or any(ord(q) < 33 or ord(q) > 126 for q in qual):
                raise ValueError(f'{path}: require uppercase ACGTN sequence and Phred+33 quality at record {number}')
            fields = header[1:].split()
            if not fields:
                raise ValueError(f'{path}: empty read identifier')
            identifier = re.sub(r'/[12]$', '', fields[0])
            mate = fields[0][-1] if re.search(r'/[12]$', fields[0]) else None
            if len(fields) > 1 and re.match(r'^[12]:', fields[1]):
                if mate and mate != fields[1][0]:
                    raise ValueError(f'{path}: inconsistent mate markers at record {number}')
                mate = fields[1][0]
            yield identifier, seq, qual, mate


def count_pairs(r1, r2, quality=False):
    result = {'pairs': 0, 'R1_bases': 0, 'R2_bases': 0, 'R1_Q30_bases': 0,
              'R2_Q30_bases': 0, 'R1_N_bases': 0, 'R2_N_bases': 0}
    for first, second in itertools.zip_longest(fastq_records(r1), fastq_records(r2)):
        if first is None or second is None or first[0] != second[0]:
            raise ValueError(f'FASTQ pairing/count mismatch after {result["pairs"]} pairs')
        if first[3] not in (None, '1') or second[3] not in (None, '2'):
            raise ValueError('R1/R2 mate markers disagree with input order')
        result['pairs'] += 1
        if quality:
            for label, record in [('R1', first), ('R2', second)]:
                result[label + '_bases'] += len(record[1])
                result[label + '_Q30_bases'] += sum(ord(q) >= 63 for q in record[2])
                result[label + '_N_bases'] += record[1].upper().count('N')
    return result


def read_sample_sheet(path, samples):
    if path is None:
        return {sample: {'plate': '', 'well': ''} for sample in samples}
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle, delimiter='\t')
        if not {'sample_id', 'plate', 'well'}.issubset(reader.fieldnames or []):
            raise ValueError('Sample sheet requires sample_id, plate, well columns')
        result, positions = {}, set()
        for row in reader:
            sample = row['sample_id']
            position = (row['plate'], row['well'])
            if sample not in samples or sample in result or not all(position) or position in positions:
                raise ValueError(f'Unknown/duplicate sample or plate/well: {sample}')
            result[sample] = {'plate': row['plate'], 'well': row['well']}
            positions.add(position)
    if set(result) != set(samples):
        raise ValueError('Sample sheet must cover every barcode sample, including empty wells')
    return result
