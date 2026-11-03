"""Studie: Long -> bei -x% Short -> bei +y% über Tief wieder Long (auf X7-Backtest-Trades).

Preisbasiert, 1 Einheit Notional, Hebel L, Gebühr fee je Seite. Vergleich je Trade:
  base : Long first_rate -> close_rate (ohne Rebuys)
  flip : Long bis -x%, dann Short bis Reversal (+y% über Tief), dann Long bis close_date
"""
import glob, json, os, sys, zipfile
import numpy as np, pandas as pd

DATA = "/home/claude/data/nfidata/binance/futures"
RES = "/home/claude/cryptox7_50/user_data/backtest_results"
STRAT = sys.argv[1] if len(sys.argv) > 1 else 'NostalgiaForInfinityX7'
FILES = {'NostalgiaForInfinityX7': ['backtest-result-2026-11-02_17-02-39.zip','backtest-result-2026-11-02_17-03-59.zip','backtest-result-2026-11-02_17-06-27.zip','backtest-result-2026-11-02_17-08-32.zip'],
         'NostalgiaForInfinityX8': ['backtest-result-2026-11-02_17-42-07.zip','backtest-result-2026-11-02_17-43-35.zip','backtest-result-2026-11-02_17-45-03.zip','backtest-result-2026-11-02_17-46-24.zip']}[STRAT]
L, FEE = 3.0, 0.0004

rows = []
for f in FILES:
    z = zipfile.ZipFile(os.path.join(RES, f))
    meta = [n for n in z.namelist() if n.endswith('.json') and 'config' not in n and 'strategy' not in n][0]
    rows.append(pd.DataFrame(json.loads(z.read(meta))['strategy'][STRAT]['trades']))
t = pd.concat(rows); t = t[~t.is_short].copy()
t['first_rate'] = t.orders.apply(lambda o: o[0]['safe_price'])
t['open_date'] = pd.to_datetime(t.open_date, utc=True); t['close_date'] = pd.to_datetime(t.close_date, utc=True)

cache = {}
def candles(pair):
    if pair not in cache:
        fn = f"{DATA}/{pair.replace('/','_').replace(':','_')}-5m-futures.feather"
        d = pd.read_feather(fn); d['date'] = pd.to_datetime(d.date, utc=True); cache[pair] = d.set_index('date')
    return cache[pair]

def simulate(tr, x, y):
    c = candles(tr.pair).loc[tr.open_date:tr.close_date]
    e = tr.first_rate; trig = e * (1 - x)
    base = (tr.close_rate / e - 1) * L - 2 * FEE * L
    hit = c.index[c.low <= trig]
    if len(hit) == 0:
        return base, base, 0, np.nan, np.nan
    i0 = c.index.get_loc(hit[0])
    pnl = -x * L - 2 * FEE * L                      # Long geschlossen bei -x%
    short_e = trig; low = trig; flipped_back = False
    for ts, r in c.iloc[i0:].iterrows():
        low = min(low, r.low)
        rev = low * (1 + y)
        if r.high >= rev and ts != hit[0]:
            pnl += (short_e / rev - 1) * L - 2 * FEE * L   # Short zu
            pnl += (tr.close_rate / rev - 1) * L - 2 * FEE * L  # neuer Long bis Trade-Ende
            flipped_back = True; break
    if not flipped_back:                              # Short bis Trade-Ende offen
        pnl += (short_e / tr.close_rate - 1) * L - 2 * FEE * L
    return base, pnl, 1, (low / e - 1), flipped_back

out = []
for x in (0.02, 0.03, 0.05, 0.08):
    for y in (0.01, 0.02, 0.03, 0.05):
        r = [simulate(tr, x, y) for tr in t.itertuples()]
        base = np.array([a for a, *_ in r]); flip = np.array([b for _, b, *_ in r]); n = sum(h for *_, h, _, _ in r)
        out.append(dict(x=x*100, y=y*100, ausgeloest=n, base_sum=base.sum()*100, flip_sum=flip.sum()*100,
                        delta=(flip-base).sum()*100, besser=int((((flip-base)[np.array([h for *_, h,_,_ in r])==1])>0).sum())))
df = pd.DataFrame(out)
print(f"Summe Margin-Rendite über {len(t)} Longs in %-Punkten (Hebel 3, Gebühr 0,04 %/Seite)")
print(df.round(1).to_string(index=False))
# Detail bester/typischer Fall
x, y = 0.05, 0.02
det = pd.DataFrame([simulate(tr, x, y) for tr in t.itertuples()], columns=['base','flip','hit','tief','zurueck'])
det['pair'] = t.pair.values; det['open'] = t.open_date.values; det['dur_h'] = t.trade_duration.values/60
d = det[det.hit==1]
print(f"\nDetail x={x*100:.0f}% y={y*100:.0f}%: {len(d)} ausgelöst, Tief ggü. Einstieg median {d.tief.median()*100:.1f}%, min {d.tief.min()*100:.1f}%")
print(f"Flip besser als Basis in {(d.flip>d.base).sum()} Fällen, schlechter in {(d.flip<d.base).sum()}; Delta-Summe {(d.flip-d.base).sum()*100:.1f} %-Punkte")
print((d.assign(base=d.base*100, flip=d.flip*100, tief=d.tief*100).sort_values('flip')[['pair','open','dur_h','base','flip','tief']].round(1).head(8)).to_string(index=False))
print((d.assign(base=d.base*100, flip=d.flip*100, tief=d.tief*100).sort_values('flip', ascending=False)[['pair','open','dur_h','base','flip','tief']].round(1).head(5)).to_string(index=False))
