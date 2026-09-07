import unittest
from research_core.range_compression_oos import classify_reference_widths, account_oos

def refs(n=20, start='2026-08-01'):
    from datetime import date, timedelta
    d=date.fromisoformat(start)
    return [{'session_date':(d+timedelta(days=i)).isoformat(),'current_reference_width':float(i+1)} for i in range(n)]

class ProspectiveOOSTests(unittest.TestCase):
    def test_historical_state_and_causal_classification(self):
        rows=refs(); rows.append({'session_date':'2026-09-08','current_reference_width':5.0})
        got=classify_reference_widths(rows)
        self.assertEqual(got[-1]['historical_state_used'],20); self.assertIsNotNone(got[-1]['compression_bucket'])
        self.assertEqual(got[-1]['lagged_baseline'],10.5)
        later=classify_reference_widths(rows+[{'session_date':'2026-09-09','current_reference_width':1000}])
        self.assertEqual(got[-1]['compression_bucket'],later[-2]['compression_bucket'])

    def test_oos_groups_exclusions_and_stop_semantics(self):
        r=refs(); r.append({'session_date':'2026-09-08','current_reference_width':5})
        trades=[{'session_date':'2026-09-07','side':'short','R':-9},{'session_date':'2026-09-08','side':'long','R':1,'exit_reason':'protective_stop'}, {'session_date':'2026-09-08','side':'short','R':-1,'exit_reason':'protective_stop_gap'}]
        out=account_oos(trades,r); self.assertEqual(out['pre_oos_trade_outcomes_excluded'],1); self.assertEqual(out['long_trades'],1); self.assertEqual(out['short_trades'],1)

    def test_exact_sample_gate(self):
        r=refs(); r.append({'session_date':'2026-09-08','current_reference_width':5})
        # Explicit feature assignments keep this accounting test independent of market reconstruction.
        ts=[{'session_date':'2026-09-08','side':'short','R':-1,'compression_bucket':'compressed'} for _ in range(20)] + [{'session_date':'2026-09-08','side':'short','R':1,'compression_bucket':'normal'} for _ in range(20)]
        out=account_oos(ts,r); self.assertEqual(out['primary_status'],'insufficient_oos_sample')

if __name__=='__main__': unittest.main()
