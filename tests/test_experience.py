import gzip
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hidog/scripts'))
from experience_qc import guide_sites, leading_alleles, supplier_md5, local_link_errors
from prepare_analysis import motif_evidence

class ExperienceTests(unittest.TestCase):
    def test_sites_both_strands_and_edge(self):
        rows = guide_sites({'A': 'AAACAGG', 'B': 'CCAGTTT', 'D': 'AAAC'}, [('g', 'AAAC')], 'cas9')
        self.assertEqual([(r['strand'], r['pam'], r['pam_status']) for r in rows],
                         [('+', 'AGG', 'NGG'), ('-', 'TGG', 'NGG'), ('+', '', '边界不足')])
        self.assertEqual(guide_sites({'x':'AAAA'}, [('g','AAA')], 'custom')[0]['exact_hits'], 2)
        self.assertEqual(guide_sites({'x':'TTTT'}, [('g','CGC')], 'cas9')[0]['exact_hits'], 0)

    def test_ties_and_empty_sample(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'r.tsv'
            p.write_text('Sort\tReads number\tRatio\tIn-window variation\tRepresentative sequence\nA1\n1\t3\t50%\t-\tAAA\n2\t3\t50%\t1:D\tAAT\nA2\n',encoding='utf-8')
            rows = leading_alleles(p)
            self.assertEqual([r['Representative sequence'] for r in rows['A1']], ['AAA','AAT'])
            self.assertEqual(rows['A2'], [])

    def test_md5_and_broken_links(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.fq.gz'
            p.write_bytes(b'abc')
            self.assertEqual(supplier_md5(p)['status'], '未提供')
            (p.parent/'MD5.txt').write_text('900150983cd24fb0d6963f7d28e17f72  a.fq.gz\n', encoding='utf-8')
            self.assertEqual(supplier_md5(p)['status'], '一致')
            p.write_bytes(b'x')
            with self.assertRaises(ValueError):
                supplier_md5(p)
            (p.parent/'index.html').write_text('<a href="#x">ok</a><img src="missing.png">',encoding='utf-8')
            self.assertEqual(len(local_link_errors(p.parent)), 1)

    def test_layout_gate_is_exact(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r.gz'
            with gzip.open(p,'wt') as f:
                for i,s in enumerate(['ACGT']*3+['ACGA']):
                    f.write(f'@{i}\n{s}\n+\nIIII\n')
            profile={'layout':{'spacer-length':1,'barcode-length':1},'read_motifs':dict.fromkeys(['R1','R2'], {'prefix':'A','post':'G','bridge':'T'})}
            rows=motif_evidence(p,p,profile)
            self.assertEqual(rows['R2']['exact_structure_matches'],3)
            self.assertFalse(rows['R2']['passes_80_percent'])


    def test_multiple_guide_export(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'A.tsv'
            p.write_text('Sort\tReads number\tg1_In-window variation\tg2_In-window variation\tRepresentative sequence\nA1\n1\t2\t-\t3:1D\tACG\n', encoding='utf-8')
            row = leading_alleles(p)['A1'][0]
            self.assertIn('g2_In-window variation: 3:1D', row['In-window variation'])

    def test_zero_assignment_keeps_na(self):
        from experience_qc import sample_reference_review
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'A.stats.tsv'
            p.write_text('Sample\tReference\tGroup\tAssigned reads\tModified reads\tBWA qnames\tEditing frequency\ns\tA\tg\t0\t0\t350\tNA\n', encoding='utf-8')
            row, = sample_reference_review(p, {'s': 600})
            self.assertEqual(row['official_percent'], 'NA')
            self.assertEqual(row['depth_note'], '本参考无明确归属')
            self.assertIsNone(row['allele_pairs'])


    def test_rejected_profile_leaves_both_mates_and_binds_explicit_layout(self):
        import json
        from unittest.mock import patch
        from prepare_analysis import prepare
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            r1, r2 = root/'one.gz', root/'two.gz'
            for p in (r1,r2):
                with gzip.open(p,'wt') as f:
                    f.write('@q\nACGA\n+\nIIII\n')
            b=root/'barcode'; b.write_text('s C C\n',encoding='utf-8')
            from prepare_analysis import digest
            layout={'spacer-length':1,'barcode-length':1,'post-barcode-spacer-length':1,'bridge-length':1,'umi-mode':'off'}
            profile=dict(source='fixture', version='test', layout=layout, barcode=str(b), barcode_sha256=digest(b),
                         read_motifs=dict.fromkeys(['R1','R2'],dict(prefix='A',post='G',bridge='T')))
            pr=root/'profile.json'; pr.write_text(json.dumps(profile),encoding='utf-8')
            ref=root/'ref.fa'; ref.write_text('>test\nAAACAGG\n',encoding='utf-8')
            f=root/'launcher'; f.touch()
            args=['-t','disjoint','--editing-tool','cas9','-r',str(ref),'-g','AAAC','-i',str(r1),'-I',str(r2)]
            manifest=dict(project=d,library='lib',launcher=str(f),profile=str(pr),arguments=args)
            with patch('subprocess.check_output',return_value='--editing-tool --spacer-length --barcode-length --post-barcode-spacer-length --bridge-length --umi-mode'):
                with self.assertRaisesRegex(ValueError, 'below 80%'):
                    prepare(manifest,root/'failed')
                audit=root/'failed/layout_check.json'
                self.assertEqual(set(json.loads(audit.read_text())['mates']),{'R1','R2'})
                manifest.pop('profile')
                manifest.update(layout_diagnostic=str(audit),layout_basis='confirmed fixture layout')
                args.extend(['-b',str(b)])
                for key,value in layout.items():
                    args.extend(['--'+key,str(value)])
                plan=json.loads(prepare(manifest,root/'ok').read_text())
                self.assertEqual(plan['audit']['guide_sites'][0]['pam'],'AGG')
                with gzip.open(r1,'wt') as stream:
                    stream.write('@q\nACGG\n+\nIIII\n')
                with self.assertRaisesRegex(ValueError,'different FASTQ'):
                    prepare(manifest,root/'stale')
