import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from research_core.range_compression_oos_data import prepare_oos_data
class ReadinessTests(unittest.TestCase):
    def make_bundle(self, *, symbol='XAUUSD_o', rows=None, semantics='utc_from_metatrader5_python_api'):
        d=Path(tempfile.mkdtemp())
        if rows is None:
            from datetime import datetime, timedelta, timezone
            start=datetime(2026,9,1,tzinfo=timezone.utc)
            rows=[{'time_utc':(start+timedelta(minutes=5*i)).isoformat().replace('+00:00','Z'),'open':'1','high':'2','low':'0.5','close':'1.5','is_closed':'true'} for i in range(960)]
        cp=d/'m5.csv'
        with cp.open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
        manifest={'schema_version':1,'exporter':{'id':'test'},'timestamp_semantics':semantics,'export_time_utc':'2026-09-07T12:00:00Z','broker':{'company':'test','server':'test'},'symbol':{'name':symbol},'files':[{'path':'m5.csv','kind':'ohlc','timeframe':'M5','rows':len(rows),'sha256':hashlib.sha256(cp.read_bytes()).hexdigest()}]}; p=d/'binding_manifest.json'; p.write_text(json.dumps(manifest)); return p
    def test_valid_historical_bundle_ready_without_performance(self):
        r=prepare_oos_data(self.make_session_bundle()); self.assertEqual(r['status'],'ready'); self.assertFalse(r['performance_evaluated']); self.assertNotIn('net_R',r)
    def test_invalid_bundle_fails(self):
        rows=[{'time_utc':'2026-09-01T00:05:00Z','open':'1','high':'2','low':'0.5','close':'1.5','is_closed':'true'},{'time_utc':'2026-09-01T00:00:00Z','open':'1','high':'0','low':'2','close':'1.5','is_closed':'true'}]; r=prepare_oos_data(self.make_bundle(rows=rows,symbol='X')); self.assertEqual(r['status'],'not_ready'); self.assertTrue(r['errors'])
    def test_forming_bar_is_excluded(self):
        rows=[{'time_utc':'2026-09-01T00:00:00Z','open':'1','high':'2','low':'0.5','close':'1.5','is_closed':'true'},{'time_utc':'2026-09-08T00:00:00Z','open':'1','high':'2','low':'0.5','close':'1.5','is_closed':'false'}]; r=prepare_oos_data(self.make_bundle(rows=rows)); self.assertEqual(r['forming_m5_rows'],1); self.assertEqual(r['closed_m5_rows'],1); self.assertFalse(r['prospective_data_present'])
    def test_start_date_is_immutable(self):
        with self.assertRaises(ValueError): prepare_oos_data(self.make_bundle(),prospective_start='2026-09-09')
    def test_manifest_hash_mismatch_and_missing_m5_fail(self):
        p=self.make_bundle(); doc=json.loads(p.read_text()); doc['files'][0]['sha256']='0'*64; p.write_text(json.dumps(doc)); self.assertEqual(prepare_oos_data(p)['status'],'not_ready')
        p=self.make_bundle(); doc=json.loads(p.read_text()); doc['files'][0]['timeframe']='H1'; p.write_text(json.dumps(doc)); self.assertEqual(prepare_oos_data(p)['status'],'not_ready')

    def test_duplicate_and_unordered_timestamps_fail(self):
        rows=[{'time_utc':'2026-09-01T00:05:00Z','open':'1','high':'2','low':'0.5','close':'1.5','is_closed':'true'},{'time_utc':'2026-09-01T00:05:00Z','open':'1','high':'2','low':'0.5','close':'1.5','is_closed':'true'}]; self.assertEqual(prepare_oos_data(self.make_bundle(rows=rows))['status'],'not_ready')

    def test_deterministic_and_manifest_selected_path(self):
        p=self.make_bundle(); a=prepare_oos_data(p); b=prepare_oos_data(p); self.assertEqual(a,b); self.assertTrue(a['m5_path'].endswith('m5.csv'))
    def make_session_bundle(self, count=22):
        from datetime import date, datetime, timedelta, timezone
        from research_core.session_policy import NamedSessionPolicy
        import yaml
        root=Path(__file__).resolve().parents[1]; policy=NamedSessionPolicy.from_yaml(root/'config/session-policies/xauusd-major-sessions.yaml'); rows=[]; day=date(2026,2,15); made=0
        while made<count:
            if day.weekday() in policy.definitions['new_york'].weekdays:
                start,_=policy.bounds_utc('new_york',day); ref=start-timedelta(minutes=240)
                for i in range(48):
                    ts=ref+timedelta(minutes=5*i); rows.append({'time_utc':ts.isoformat().replace('+00:00','Z'),'open':'1','high':'2','low':'0.5','close':'1.5','is_closed':'true'})
                for i in range(108):
                    ts=start+timedelta(minutes=5*i); rows.append({'time_utc':ts.isoformat().replace('+00:00','Z'),'open':'1','high':'2','low':'0.5','close':'1.5','is_closed':'true'})
                made+=1
            day+=timedelta(days=1)
        return self.make_bundle(rows=rows)

    def test_twenty_eligible_reference_sessions_are_ready(self):
        result=prepare_oos_data(self.make_session_bundle()); self.assertGreaterEqual(result['eligible_pre_oos_reference_sessions'],20); self.assertTrue(result['pre_oos_history_available']); self.assertEqual(result['status'],'ready')
    def _drop_row_and_refresh(self, manifest_path, predicate):
        doc=json.loads(manifest_path.read_text()); csv_path=manifest_path.parent/doc['files'][0]['path']; rows=list(csv.DictReader(csv_path.open()))
        kept=[row for row in rows if not predicate(row)]; csv_path.write_text('')
        with csv_path.open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(kept)
        doc['files'][0]['rows']=len(kept); doc['files'][0]['sha256']=hashlib.sha256(csv_path.read_bytes()).hexdigest(); manifest_path.write_text(json.dumps(doc)); return manifest_path

    def test_complete_reference_but_missing_ny_bar_is_ineligible(self):
        p=self.make_session_bundle(); doc=json.loads(p.read_text()); cp=p.parent/doc['files'][0]['path']; rows=list(csv.DictReader(cp.open())); kept=rows[:48]+rows[49:]; cp.write_text('')
        with cp.open('w',newline='') as h: w=csv.DictWriter(h,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(kept)
        doc['files'][0]['rows']=len(kept); doc['files'][0]['sha256']=hashlib.sha256(cp.read_bytes()).hexdigest(); p.write_text(json.dumps(doc)); result=prepare_oos_data(p); self.assertLessEqual(result['eligible_pre_oos_reference_sessions'],20)

    def test_complete_reference_but_forming_ny_bar_is_ineligible(self):
        p=self.make_session_bundle(); doc=json.loads(p.read_text()); cp=p.parent/doc['files'][0]['path']; rows=list(csv.DictReader(cp.open())); rows[48]['is_closed']='false'; cp.write_text('')
        with cp.open('w',newline='') as h: w=csv.DictWriter(h,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
        doc['files'][0]['sha256']=hashlib.sha256(cp.read_bytes()).hexdigest(); p.write_text(json.dumps(doc)); result=prepare_oos_data(p); self.assertLessEqual(result['eligible_pre_oos_reference_sessions'],20)
    def test_readiness_reference_reconstruction_matches_frozen_semantics(self):
        from research_core.range_compression_oos_data import _eligible_reference_sessions
        p=self.make_session_bundle(); doc=json.loads(p.read_text()); cp=p.parent/doc['files'][0]['path']; rows=list(csv.DictReader(cp.open())); actual=_eligible_reference_sessions(rows,p.parent); self.assertGreaterEqual(len(actual),20); self.assertEqual(actual[0]['current_reference_width'], actual[0]['reference_high']-actual[0]['reference_low'])

    def test_dst_boundaries_are_policy_derived(self):
        from datetime import date
        from research_core.session_policy import NamedSessionPolicy
        root=Path(__file__).resolve().parents[1]; policy=NamedSessionPolicy.from_yaml(root/'config/session-policies/xauusd-major-sessions.yaml'); feb=policy.bounds_utc('new_york',date(2026,3,6))[0]; mar=policy.bounds_utc('new_york',date(2026,3,9))[0]; self.assertNotEqual(feb,mar); self.assertEqual(feb.hour,13); self.assertEqual(mar.hour,12)

    def test_cli_refuses_overwrite(self):
        import subprocess, sys
        p=self.make_bundle(); out=p.parent/'readiness.json'; out.write_text('original'); proc=subprocess.run([sys.executable,'tools/prepare_range_compression_oos_data.py',str(p),'--output',str(out)],capture_output=True,text=True); self.assertNotEqual(proc.returncode,0); self.assertEqual(out.read_text(),'original')
if __name__=='__main__': unittest.main()