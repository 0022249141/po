from __future__ import annotations
from statistics import median
from typing import Iterable, Mapping, Any
from .range_compression_study import midrank_percentile, compression_bucket

START = "2026-09-08"

def classify_reference_widths(rows: Iterable[Mapping[str, Any]], lookback: int = 20):
    history=[]; out=[]
    for raw in sorted((dict(r) for r in rows), key=lambda r: str(r['session_date'])):
        prior=[float(r['current_reference_width']) for r in history[-lookback:]]; row=dict(raw)
        row['historical_state_used']=len(prior)
        if len(prior)==lookback:
            p=midrank_percentile(float(row['current_reference_width']), prior)
            row.update(percentile=p, lagged_baseline=median(prior), compression_bucket=compression_bucket(p))
        else: row.update(percentile=None, lagged_baseline=None, compression_bucket=None)
        history.append(row); out.append(row)
    return out

def _metrics(trades):
    rs=[]
    for index, trade in enumerate(trades):
        if 'gross_R' not in trade:
            raise ValueError(f'OOS trade {index} is missing required gross_R')
        rs.append(float(trade['gross_R']))
    wins=[r for r in rs if r>0]; losses=[r for r in rs if r<0]
    return {'trades':len(rs),'net_R':sum(rs),'expectancy_R':sum(rs)/len(rs) if rs else None,'profit_factor':sum(wins)/abs(sum(losses)) if losses else (float('inf') if wins else None),'win_rate':len(wins)/len(rs) if rs else None,'stop_rate':sum(t.get('exit_reason') in {'protective_stop','protective_stop_gap'} for t in trades)/len(rs) if rs else None,'average_R':sum(rs)/len(rs) if rs else None,'median_R':median(rs) if rs else None}

def account_oos(trades: Iterable[Mapping[str, Any]], reference_rows: Iterable[Mapping[str, Any]], *, start_session: str = START):
    refs=classify_reference_widths(reference_rows); by_date={r['session_date']:r for r in refs}; all_trades=[dict(t) for t in trades]; pre=0; oos=[]
    for t in all_trades:
        feature=by_date.get(str(t['session_date']), {}); t.update(compression_bucket=feature.get('compression_bucket', t.get('compression_bucket')), percentile=feature.get('percentile'))
        if str(t['session_date']) < start_session: pre+=1
        else: oos.append(t)
    short=[t for t in oos if str(t.get('side','')).lower()=='short']; comp=[t for t in short if t.get('compression_bucket')=='compressed']; non=[t for t in short if t.get('compression_bucket') in {'normal','expanded'}]
    c,n=_metrics(comp),_metrics(non); dates=[str(t['session_date']) for t in oos]
    status='insufficient_oos_sample'
    if len(comp)>=20 and len(non)>=20: status='prospective_descriptive_replication' if c['expectancy_R']<0 and c['profit_factor']<1 and c['median_R']<0 and c['stop_rate']>n['stop_rate'] and c['expectancy_R']<n['expectancy_R'] else 'not_replicated'
    return {'prospective_start_session_date':start_session,'first_observed_oos_session_date':min(dates) if dates else None,'last_observed_oos_session_date':max(dates) if dates else None,'candidate_sessions':len(refs),'eligible_reference_sessions':len(refs),'excluded_incomplete_sessions':0,'baseline_generated_trades':len(all_trades),'long_trades':sum(str(t.get('side')).lower()=='long' for t in oos),'short_trades':len(short),'compressed_short_trades':len(comp),'normal_short_trades':sum(t.get('compression_bucket')=='normal' for t in short),'expanded_short_trades':sum(t.get('compression_bucket')=='expanded' for t in short),'noncompressed_short_trades':len(non),'matched_feature_assignments':sum(t.get('compression_bucket') is not None for t in oos),'unmatched_feature_assignments':sum(t.get('compression_bucket') is None for t in oos),'historical_state_sessions_used':sum(r['session_date']<start_session for r in refs),'pre_oos_trade_outcomes_excluded':pre,'primary_status':status,'primary':{'compressed_short':c,'noncompressed_short':n,'delta_expectancy_R':c['expectancy_R']-n['expectancy_R'] if c['expectancy_R'] is not None and n['expectancy_R'] is not None else None}}
