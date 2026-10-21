import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from thermoaudit import analyze_candidates, audit
from thermoaudit.pareto import read_candidates
from thermoaudit.report import render_html
from thermoaudit.validation import ValidationError

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / 'examples/balanced_hx.json').read_text())


def point(sid, sec=1, eff=.5, capex=10, feasible=True):
    return dict(id=sid, sec_kwh_kg=sec, exergy_efficiency=eff, capex_usd=capex, feasible=feasible)


class AuditTests(unittest.TestCase):
    def test_hand_calculated_balances_and_sec(self):
        result = audit(fixture())
        self.assertEqual(result['status'], 'PASS')
        values = {c['code']: c['value'] for c in result['checks']}
        # 2*120 + 1*80 = 2*80 + 1*160 = 320 kW.
        self.assertEqual(values['energy_balance'], 0)
        self.assertEqual(values['mass_balance'], 0)
        self.assertEqual(values['terminal_approach'], 40)
        self.assertEqual(result['metrics']['specific_energy_kwh_kg'], .5)

    def test_detect_deliberate_fault(self):
        result = audit(json.loads((ROOT/'examples/broken_hx.json').read_text()))
        failures = {c['code'] for c in result['checks'] if c['status']=='FAIL'}
        self.assertTrue({'mass_balance', 'energy_balance', 'passive_hx_direction'} <= failures)

    def test_mass_transfer_cannot_cancel_between_hx_sides(self):
        c=fixture(); c['streams'][1]['mass_kg_s']=1.9; c['streams'][3]['mass_kg_s']=1.1
        checks={x['code']:x['status'] for x in audit(c)['checks']}
        self.assertEqual(checks['mass_balance'],'PASS')
        self.assertEqual(checks['hot_side_mass_balance'],'FAIL')
        self.assertEqual(checks['cold_side_mass_balance'],'FAIL')

    def test_crossed_endpoint(self):
        c=fixture(); c['streams'][2]['temperature_k']=90
        result=audit(c)
        check=next(x for x in result['checks'] if x['code']=='terminal_approach')
        self.assertEqual(check['value'],-10); self.assertEqual(check['status'],'FAIL')

    def test_compressor_work_sign(self):
        c=fixture(); c.pop('performance'); c['streams']=c['streams'][:2]
        c['streams'][1].update(temperature_k=150,enthalpy_kj_kg=150)
        c['units']=[dict(id='C',kind='boundary',inlets=['hot_in'],outlets=['hot_out'],heat_kw=0,shaft_work_out_kw=-60)]
        self.assertEqual(audit(c)['status'],'PASS')
        c['units'][0]['shaft_work_out_kw']=60
        self.assertEqual(audit(c)['status'],'FAIL')

    def test_turbine_work_sign(self):
        c=fixture(); c.pop('performance'); c['streams']=c['streams'][:2]
        c['units']=[dict(id='T',kind='boundary',inlets=['hot_in'],outlets=['hot_out'],heat_kw=0,shaft_work_out_kw=80)]
        self.assertEqual(audit(c)['status'],'PASS')

    def test_invalid_numbers(self):
        for value in (float('nan'),float('inf'),-1,True,'2'):
            with self.subTest(value=value):
                c=fixture(); c['streams'][0]['mass_kg_s']=value
                with self.assertRaises(ValidationError): audit(c)

    def test_temperature_must_be_positive(self):
        c=fixture(); c['streams'][0]['temperature_k']=0
        with self.assertRaises(ValidationError): audit(c)

    def test_negative_enthalpy_allowed(self):
        c=fixture()
        for s in c['streams']: s['enthalpy_kj_kg']-=200
        self.assertEqual(audit(c)['status'],'PASS')

    def test_zero_flow_hx_rejected(self):
        c=fixture(); c['streams'][0]['mass_kg_s']=0
        with self.assertRaises(ValidationError): audit(c)

    def test_duplicate_stream(self):
        c=fixture(); c['streams'].append(c['streams'][0].copy())
        with self.assertRaises(ValidationError): audit(c)

    def test_unknown_field(self):
        c=fixture(); c['units'][0]['heat_kw_typo']=10
        with self.assertRaises(ValidationError): audit(c)

    def test_unknown_stream(self):
        c=fixture(); c['units'][0]['inlets'][0]='missing'
        with self.assertRaises(ValidationError): audit(c)

    def test_invalid_hx_mapping(self):
        c=fixture(); c['units'][0]['hot_in']='hot_out'
        with self.assertRaises(ValidationError): audit(c)

    def test_internal_stream_cannot_be_product(self):
        c=fixture(); c['performance']['product_stream']='hot_in'
        with self.assertRaises(ValidationError): audit(c)

    def test_tolerance_boundary(self):
        c=fixture(); c['tolerances']={'rtol':0,'energy_atol_kw':1}
        c['units'][0]['heat_kw']=1
        self.assertEqual(audit(c)['status'],'PASS')
        c['units'][0]['heat_kw']=1.01
        self.assertEqual(audit(c)['status'],'FAIL')

    def test_overflow_is_validation_error(self):
        c=fixture(); c['streams'][0]['mass_kg_s']=1e308
        with self.assertRaises(ValidationError): audit(c)

    def test_audit_does_not_mutate_input(self):
        c=fixture(); original=copy.deepcopy(c); audit(c); self.assertEqual(c,original)


class ParetoTests(unittest.TestCase):
    def test_dominance_and_feasibility(self):
        r=analyze_candidates([point('a'),point('b',2,.4,20),point('excluded',0,1,0,False)])
        self.assertEqual(r['pareto_ids'],['a'])
        self.assertEqual(r['recommendation_id'],'a')
        self.assertEqual(r['excluded_ids'],['excluded'])

    def test_efficiency_is_maximized(self):
        self.assertEqual(analyze_candidates([point('a',eff=.4),point('b',eff=.6)])['pareto_ids'],['b'])

    def test_constant_columns_and_identical_points(self):
        r=analyze_candidates([point('b'),point('a')])
        self.assertEqual(set(r['pareto_ids']),{'a','b'})
        self.assertEqual(r['recommendation_id'],'a')
        self.assertEqual(r['scores'],{'a':0,'b':0})

    def test_weights_change_compromise(self):
        rows=[point('low_energy',1,.5,20),point('low_cost',2,.5,10)]
        self.assertEqual(analyze_candidates(rows,[9,1,1])['recommendation_id'],'low_energy')
        self.assertEqual(analyze_candidates(rows,[1,1,9])['recommendation_id'],'low_cost')

    def test_no_feasible(self):
        with self.assertRaises(ValidationError): analyze_candidates([point('a',feasible=False)])

    def test_invalid_weights(self):
        for w in ([0,1,1],[-1,1,1],[math.nan,1,1],[1,1]):
            with self.subTest(weights=w), self.assertRaises(ValidationError): analyze_candidates([point('a')],w)

    def test_fraction_not_percent(self):
        with self.assertRaises(ValidationError): analyze_candidates([point('a',eff=50)])

    def test_duplicate_id(self):
        with self.assertRaises(ValidationError): analyze_candidates([point('a'),point('a')])

    def test_csv_example(self):
        r=analyze_candidates(read_candidates(ROOT/'examples/candidates.csv'))
        self.assertEqual(set(r['pareto_ids']),{'A','B','C','F'})
        self.assertNotIn('E',r['scores'])

    def test_bad_csv_headers_and_cells(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv'
            for content in ('id,id\na,a\n','id,sec_kwh_kg,exergy_efficiency,capex_usd,feasible\na,1,.5,1,maybe\n'):
                p.write_text(content)
                with self.assertRaises(ValidationError): read_candidates(p)

    def test_pareto_does_not_mutate(self):
        r=[point('a')]; original=copy.deepcopy(r); analyze_candidates(r); self.assertEqual(r,original)



class IntegrationTests(unittest.TestCase):
    def run_cli(self,*args):
        return subprocess.run([sys.executable,'-m','thermoaudit',*map(str,args)],cwd=ROOT,capture_output=True,text=True)

    def test_cli_pass_fail_and_invalid_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.run_cli('audit','examples/balanced_hx.json','--out',d).returncode,0)
            self.assertTrue((Path(d)/'audit.html').exists())
            result=json.loads((Path(d)/'audit.json').read_text())
            self.assertEqual(len(result['metadata']['input_sha256']),64)
            self.assertEqual(self.run_cli('audit','examples/broken_hx.json','--out',d).returncode,1)
            self.assertEqual(self.run_cli('audit','missing.json','--out',d).returncode,2)

    def test_cli_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.json';p.write_text('{"schema_version":1,"schema_version":1}')
            r=self.run_cli('audit',p,'--out',d)
            self.assertEqual(r.returncode,2); self.assertIn('duplicate JSON key',r.stderr)

    def test_cli_pareto(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.run_cli('pareto','examples/candidates.csv','--out',d)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('<svg', (Path(d)/'pareto.html').read_text())

    def test_html_escapes_untrusted_strings(self):
        c=fixture(); c['name']='<script>alert(1)</script>'
        html=render_html(audit(c),'audit')
        self.assertNotIn('<script>',html); self.assertIn('&lt;script&gt;',html)

    def test_cli_does_not_overwrite_input(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'audit.json'; original=json.dumps(fixture()); p.write_text(original)
            self.assertEqual(self.run_cli('audit',p,'--out',d).returncode,2)
            self.assertEqual(p.read_text(),original)


if __name__=='__main__':
    unittest.main()
