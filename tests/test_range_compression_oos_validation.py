import copy, tempfile, unittest
from pathlib import Path
import yaml
from research_core.range_compression_oos_validation import validate_range_compression_oos_spec

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'quant/studies/XAUUSD_NY_PREOPEN_RANGE_COMPRESSION_PROSPECTIVE_OOS_V1.yaml'

class OOSValidationTests(unittest.TestCase):
    def check_tamper(self,key,value):
        doc=yaml.safe_load(SPEC.read_text()); doc[key]=value
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.yaml'; p.write_text(yaml.safe_dump(doc)); self.assertEqual(validate_range_compression_oos_spec(p,ROOT).status,'fail')
    def test_immutable_contract_fields(self):
        for key,value in [('prospective_outcome_start_session','2026-09-09'),('implementation_source_commit','x'),('strategy_spec_sha256','x'),('source_backtest_sha256','x'),('primary_group',{'side':'long'}),('comparator_group',{'side':'short','compression_bucket':['compressed']}),('minimum_oos_sample',{'compressed_short':19,'noncompressed_short':20})]: self.check_tamper(key,value)
    def test_lookback_and_thresholds(self):
        doc=yaml.safe_load(SPEC.read_text()); doc['compression']['lookback']=19
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.yaml'; p.write_text(yaml.safe_dump(doc)); self.assertEqual(validate_range_compression_oos_spec(p,ROOT).status,'fail')
    def test_generic_dispatch(self):
        from research_core.study_spec_validation import validate_study_spec
        self.assertEqual(validate_study_spec(SPEC,ROOT).status,'pass')

if __name__=='__main__': unittest.main()
