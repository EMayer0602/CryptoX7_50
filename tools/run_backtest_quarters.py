#!/usr/bin/env python3
"""Jahres-Backtest in Quartalen (RAM-Limit), Kapital wird durchgereicht.

Aufruf: python tools/run_backtest_quarters.py <config.json> <YYYYMMDD-YYYYMMDD> <tag>
"""
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

cfg_path, timerange, tag = sys.argv[1:4]
start, end = (datetime.strptime(x, "%Y%m%d") for x in timerange.split("-"))
cfg = json.load(open(cfg_path))
wallet = float(cfg["dry_run_wallet"])
out_dir = Path("user_data/backtest_results")
out_dir.mkdir(parents=True, exist_ok=True)

# Quartalsgrenzen
bounds = []
t = start
while t < end:
    n = min(t + timedelta(days=91), end)
    bounds.append((t, n))
    t = n

results = []
for i, (a, b) in enumerate(bounds, 1):
    tr = f"{a:%Y%m%d}-{b:%Y%m%d}"
    tmp_cfg = Path(f"/tmp/cfg_{tag}_{i}.json")
    c = dict(cfg)
    c["dry_run_wallet"] = round(wallet, 2)
    tmp_cfg.write_text(json.dumps(c))
    name = f"{tag}-Q{i}-{tr}"
    cmd = [
        "freqtrade", "backtesting", "-c", str(tmp_cfg), "--timerange", tr,
        "--cache", "none", "--export", "trades",
        "--export-filename", str(out_dir / f"{name}.json"),
    ]
    print(f"== Q{i} {tr} Startkapital {wallet:.2f}", flush=True)
    log = Path(f"/tmp/bt_{tag}_Q{i}.log")
    rc = subprocess.run(cmd, stdout=log.open("w"), stderr=subprocess.STDOUT).returncode
    if rc != 0:
        print(f"!! Q{i} fehlgeschlagen rc={rc}, siehe {log}", flush=True)
        sys.exit(rc)
    # Ergebnisdatei (zip) finden
    last = json.loads((out_dir / ".last_result.json").read_text())["latest_backtest"]
    with zipfile.ZipFile(out_dir / last) as z:
        meta = next(n for n in z.namelist() if n.endswith(".json") and "_config" not in n and "_strategy" not in n)
        data = json.loads(z.read(meta))
    s = data["strategy"][cfg["strategy"]]
    wallet = s["final_balance"]
    results.append({"q": i, "timerange": tr, **{k: s[k] for k in (
        "starting_balance", "final_balance", "profit_total", "profit_total_abs", "total_trades",
        "wins", "losses", "draws", "max_drawdown_account", "max_drawdown_abs", "profit_factor",
        "sharpe", "sortino", "calmar", "market_change", "trade_count_long", "trade_count_short")}})
    print(json.dumps(results[-1]), flush=True)

json.dump(results, open(out_dir / f"{tag}-quarters-summary.json", "w"), indent=2)
print("FERTIG", flush=True)
