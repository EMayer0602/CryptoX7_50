"""Studie: Long halten, bei -x% unter Ersteinstieg gleich großen Short als Hedge öffnen,
Short schließen sobald Kurs y% über sein Tief steigt. Variante "re": nach Schließen
erneut hedgen, wenn der Kurs wieder unter -x% fällt. Preisbasiert, Hebel L, Gebühr fee/Seite.
Basis = Long first_rate -> close_rate (ohne Rebuys). Delta = Hedge-P&L (Short-Beiträge).
"""
import json, os, zipfile
import numpy as np, pandas as pd

DATA = "/home/claude/data/nfidata/binance/futures"
RES = "/home/claude/cryptox7_50/user_data/backtest_results"
FILES = ['backtest-result-2026-11-02_17-02-39.zip','backtest-result-2026-11-02_17-03-59.zip',
         'backtest-result-2026-11-02_17-06-27.zip','backtest-result-2026-11-02_17-08-32.zip']
L, FEE = 3.0, 0.0004

rows = []
for f in FILES:
    z = zipfile.ZipFile(os.path.join(RES, f))
    meta = [n for n in z.namelist() if n.endswith('.json') and 'config' not in n and 'strategy' not in n][0]
    rows.append(pd.DataFrame(json.loads(z.read(meta))['strategy']['NostalgiaForInfinityX7']['trades']))
t = pd.concat(rows); t = t[~t.is_short].copy()
t['first_rate'] = t.orders.apply(lambda o: o[0]['safe_price'])
t['open_date'] = pd.to_datetime(t.open_date, utc=True); t['close_date'] = pd.to_datetime(t.close_date, utc=True)

cache = {}
def candles(pair):
    if pair not in cache:
        d = pd.read_feather(f"{DATA}/{pair.replace('/','_').replace(':','_')}-5m-futures.feather")
        d['date'] = pd.to_datetime(d.date, utc=True); cache[pair] = d.set_index('date')
    return cache[pair]

def simulate(tr, x, y, rehedge):
    c = candles(tr.pair).loc[tr.open_date:tr.close_date]
    e = tr.first_rate; trig = e * (1 - x)
    base = (tr.close_rate / e - 1) * L - 2 * FEE * L
    short_pnl, n_hedge, in_short, low, first, prev_close = 0.0, 0, False, None, True, e
    for ts, r in c.iterrows():
        if not in_short:
            if (first or rehedge) and r.low <= trig:
                short_e = trig if prev_close > trig else r.open   # Kreuzen von oben: Trigger, sonst Open
                in_short, low, first, n_hedge = True, min(r.low, short_e), False, n_hedge + 1
                prev_close = r.close
                continue
        else:
            low = min(low, r.low); rev = low * (1 + y)
            if r.high >= rev:
                short_pnl += (short_e / rev - 1) * L - 2 * FEE * L; in_short = False
        prev_close = r.close
    if in_short:
        short_pnl += (short_e / tr.close_rate - 1) * L - 2 * FEE * L
    return base, short_pnl, n_hedge

for rehedge in (False, True):
    out = []
    for x in (0.02, 0.03, 0.05, 0.08):
        for y in (0.01, 0.02, 0.03, 0.05):
            r = pd.DataFrame([simulate(tr, x, y, rehedge) for tr in t.itertuples()], columns=['base','hedge','n'])
            r['open'] = t.open_date.values
            h = r[r.n > 0]; crash = h[(h.open >= '2025-10-10') & (h.open < '2025-10-12')]; rest = h.drop(crash.index)
            out.append(dict(x=x*100, y=y*100, trades=len(h), hedges=int(h.n.sum()), delta=h.hedge.sum()*100,
                            crash=crash.hedge.sum()*100, rest=rest.hedge.sum()*100,
                            rest_pos=int((rest.hedge > 0).sum()), rest_med=rest.hedge.median()*100))
    print(f"\n=== {'Re-Hedge erlaubt' if rehedge else 'Einmaliger Hedge'} === (Delta = Short-P&L in %-Punkten Margin, Hebel 3; Basis-Summe {r.base.sum()*100:.0f})")
    print(pd.DataFrame(out).round(1).to_string(index=False))
