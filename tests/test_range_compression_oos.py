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
        trades=[{'session_date':'2026-09-07','side':'short','gross_R':-9},{'session_date':'2026-09-08','side':'long','gross_R':1,'exit_reason':'protective_stop'}, {'session_date':'2026-09-08','side':'short','gross_R':-1,'exit_reason':'protective_stop_gap'}]
        out=account_oos(trades,r); self.assertEqual(out['pre_oos_trade_outcomes_excluded'],1); self.assertEqual(out['long_trades'],1); self.assertEqual(out['short_trades'],1)

    def test_exact_sample_gate(self):
        r=refs(); r.append({'session_date':'2026-09-08','current_reference_width':5})
        # Explicit feature assignments keep this accounting test independent of market reconstruction.
        ts=[{'session_date':'2026-09-08','side':'short','gross_R':-1,'compression_bucket':'compressed'} for _ in range(20)] + [{'session_date':'2026-09-08','side':'short','gross_R':1,'compression_bucket':'normal'} for _ in range(20)]
        out=account_oos(ts,r); self.assertEqual(out['primary_status'],'insufficient_oos_sample')

    def test_gross_r_metrics_and_missing_schema_rejected(self):
        r=refs(); r.append({'session_date':'2026-09-08','current_reference_width':5})
        trades=[{'session_date':'2026-09-08','side':'short','gross_R':-2,'compression_bucket':'compressed'}, {'session_date':'2026-09-08','side':'short','gross_R':1,'compression_bucket':'compressed'}, {'session_date':'2026-09-08','side':'short','gross_R':-1,'compression_bucket':'normal'}]
        out=account_oos(trades,r); m=out['primary']['compressed_short']; self.assertEqual(m['net_R'],-2); self.assertEqual(m['expectancy_R'],-2/3); self.assertEqual(m['median_R'],-1); self.assertEqual(m['profit_factor'],1/3)
        with self.assertRaisesRegex(ValueError,'gross_R'):
            account_oos([{'session_date':'2026-09-08','side':'short','R':1,'compression_bucket':'compressed'}],r)

    def test_both_protective_stop_reasons_count(self):
        r=refs(); r.append({'session_date':'2026-09-08','current_reference_width':5})
        ts=[{'session_date':'2026-09-08','side':'short','gross_R':-1,'compression_bucket':'compressed','exit_reason':reason} for reason in ('protective_stop','protective_stop_gap')]
        self.assertEqual(account_oos(ts,r)['primary']['compressed_short']['stop_rate'],1.0)
    def test_legacy_return_aliases_are_rejected(self):
        r=refs(); r.append({'session_date':'2026-09-08','current_reference_width':5})
        for field in ('R','r','return_R'):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError,'gross_R'):
                    account_oos([{'session_date':'2026-09-08','side':'short',field:1,'compression_bucket':'compressed'}],r)

    def test_realistic_baseline_ledger_schema(self):
        r=refs(); r.append({'session_date':'2026-09-08','current_reference_width':5})
        trade={'session_date':'2026-09-08','side':'short','gross_R':-0.75,'exit_reason':'protective_stop','entry_time':'2026-09-08T13:00:00Z','exit_time':'2026-09-08T14:00:00Z','entry_price':1.0,'exit_price':1.5,'risk':1.0,'compression_bucket':'compressed'}
        metrics=account_oos([trade],r)['primary']['compressed_short']
        self.assertEqual(metrics['net_R'],-0.75); self.assertEqual(metrics['expectancy_R'],-0.75); self.assertEqual(metrics['average_R'],-0.75); self.assertEqual(metrics['median_R'],-0.75); self.assertEqual(metrics['profit_factor'],0); self.assertEqual(metrics['win_rate'],0); self.assertEqual(metrics['stop_rate'],1)
if __name__=='__main__': unittest.main()
