"""Read-only evidence for preflight, reference-level reports and final delivery."""
import csv
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


def supplier_md5(path):
    path = Path(path)
    manifest = path.parent / 'MD5.txt'
    result = {'file': path.name, 'status': '未提供'}
    if not manifest.is_file():
        return result
    matches = set()
    for line in manifest.read_text(encoding='utf-8-sig').splitlines():
        m = re.fullmatch(r'([0-9a-fA-F]{32})\s+\*?(.+)', line.strip())
        if m and Path(m[2]) == Path(path.name):
            matches.add(m[1].lower())
    if not matches:
        result['status'] = '清单未列出该文件'
        return result
    h = hashlib.md5()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    if matches != {h.hexdigest()}:
        raise ValueError(f'Supplier MD5 mismatch: {path}')
    return dict(result, status='一致', md5=h.hexdigest())


def guide_records(inputs):
    records = []
    for item in inputs:
        path = Path(item)
        long_literal = len(item) > 255 and re.fullmatch(r'[ACGTUNacgtun,]+', item)
        if long_literal or not path.is_file():
            records.extend((seq, seq) for seq in item.split(',') if seq)
            continue
        lines = [s.strip() for s in path.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
        if lines and lines[0].startswith('>'):
            name, parts = None, []
            for line in lines:
                if line.startswith('>'):
                    if name is not None:
                        records.append((name, ''.join(parts)))
                    name, parts = line[1:], []
                else:
                    parts.append(line)
            records.append((name, ''.join(parts)))
        else:
            records.extend((f'{path.name}:{i}', seq) for i, seq in enumerate(lines, 1))
    return records


def guide_sites(refs, guides, tool):
    complement = str.maketrans('ACGTN', 'TGCAN')
    rows = []
    for ref, seq in refs.items():
        for name, guide in guides:
            guide = guide.upper().replace('U', 'T')
            if not guide or set(guide) - set('ACGT'):
                rows.append(dict(reference=ref, guide=name, exact_hits=None, pam_status='序列非确定，未评估'))
                continue
            hits = []
            for strand, oriented in [('+', seq), ('-', seq.translate(complement)[::-1])]:
                offset = oriented.find(guide)
                while offset >= 0:
                    end = offset + len(guide)
                    start1 = offset + 1 if strand == '+' else len(seq) - end + 1
                    row = dict(reference=ref, guide=name, strand=strand, start_1based=start1,
                               end_1based=start1 + len(guide) - 1, pam='', pam_status='未评估该酶型')
                    if tool.lower() == 'cas9':
                        pam = oriented[end:end + 3]
                        row['pam'] = pam
                        if len(pam) < 3:
                            status = '边界不足'
                        elif 'N' in pam[1:]:
                            status = '参考碱基未定'
                        else:
                            status = 'NGG' if pam.endswith('GG') else '非 NGG'
                        row['pam_status'] = status
                    hits.append(row)
                    offset = oriented.find(guide, offset + 1)
            rows.extend(dict(row, exact_hits=len(hits)) for row in hits)
            if not hits:
                rows.append(dict(reference=ref, guide=name, exact_hits=0, pam_status='无精确匹配'))
    return rows


def leading_alleles(path):
    """Retain all top ties among displayed rows; one-column lines identify samples."""
    result = {}
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream, delimiter='\t')
        header = next(reader)
        per_guide = [k for k in header if k.endswith('_In-window variation')]
        if (not {'Reads number', 'Representative sequence'} <= set(header)
                or ('In-window variation' not in header and not per_guide)):
            raise ValueError(f'Unknown allele export: {path}')
        best = -1
        sample = None
        for fields in reader:
            if not fields or not any(fields):
                continue
            if len(fields) == 1:
                sample = fields[0]
                if sample in result:
                    raise ValueError(f'Duplicate allele section: {sample}')
                result[sample], best = [], -1
                continue
            row = dict(zip(header, fields))
            if per_guide:
                row['In-window variation'] = ' | '.join(f'{k}: {row[k]}' for k in per_guide)
            if sample is None:
                raise ValueError(f'Missing sample section: {path}')
            if not (row.get('Reads number') or '').isdigit():
                if row.get('Read status') in ('NA', 'Low depth') or row.get('Reads number') in ('-', 'NA', ''):
                    continue
                raise ValueError(f'Invalid displayed support: {path} / {sample}')
            count = int(row['Reads number'])
            if count > best:
                result[sample] = []
                best = count
            if count == best and count:
                result[sample].append(row)
    return result


def sample_reference_review(stats_path, counts):
    allele_path = stats_path.with_name(stats_path.name[:-len('.stats.tsv')] + '.tsv')
    alleles = leading_alleles(allele_path) if allele_path.exists() else {}
    rows = []
    with stats_path.open(encoding='utf-8-sig', newline='') as stream:
        for s in csv.DictReader(stream, delimiter='\t'):
            sample = s['Sample']
            hard = int(s.get('Hard assigned reads', s['Assigned reads']))
            bwa = s.get('BWA qnames')
            flags = []
            if bwa not in (None, '') and int(bwa) < 100:
                flags.append('目标组比对少于100')
            if hard == 0:
                flags.append('本参考无明确归属')
            elif hard < 1000:
                flags.append('本参考归属少于1000')
            lead = alleles.get(sample, [])
            for allele in lead or [{}]:
                rows.append(dict(sample_id=sample, reference=s['Reference'], group=s['Group'],
                                 split_pairs=counts[sample], group_bwa_qnames=bwa, hard_assigned=hard,
                                 modified_pairs=int(s['Modified reads']), official_percent=s['Editing frequency'],
                                 depth_note='；'.join(flags), top_ties=len(lead), allele_class=allele.get('Allele class'),
                                 window_event=allele.get('In-window variation'), allele_pairs=allele.get('Reads number'),
                                 display_ratio=allele.get('Ratio'), sequence=allele.get('Representative sequence')))
    return rows


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(v for k, v in attrs if k in ('href', 'src') and v)


def local_link_errors(root):
    root = Path(root).resolve()
    errors = []
    for path in sorted(root.rglob('*.html')):
        parser = LocalLinks()
        parser.feed(path.read_text(encoding='utf-8'))
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme in ('https', 'http', 'mailto', 'data') or url.netloc or not url.path:
                continue
            target = (path.parent / unquote(url.path)).resolve()
            if url.scheme or root not in target.parents or not target.is_file():
                errors.append(f'{path.relative_to(root)} -> {link}')
    return errors
