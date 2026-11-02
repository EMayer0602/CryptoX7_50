# Cryptox7_50

Kopie von **NostalgiaForInfinityX7** (v17.5.204, Stand 2026-11-02) aus
https://github.com/iterativv/NostalgiaForInfinity – zur Anpassung und zum Testen.

Original-Lizenz: siehe `LICENSE.NFI`.

## Struktur

- `user_data/strategies/NostalgiaForInfinityX7.py` – die Strategie (Freqtrade `IStrategy`, 5m)
- `configs/` – Beispiel-Configs, Pair- und Blacklists für Kraken (Spot/USD) und Binance (Spot/USDT)
- `tests/` – Original-Testsuite (Backtest-Skripte, Unit-Tests)
- `docker-compose.yml` – Freqtrade-Runtime

## Runtime

Die Strategie läuft nur innerhalb von Freqtrade (Docker oder `pip install freqtrade`).
Pflichtwerte aus dem Original: `timeframe` 5m, `use_exit_signal` true,
`exit_profit_only` false, `ignore_roi_if_entry_signal` true.

## Änderungen gegenüber dem Original

- `configs/backtest-binance-spot.json`, `configs/backtest-binance-futures.json` – Backtest-Configs (16.500 USDT, 6 Slots, Hebel 3 isolated bei Futures). Binance-API ist aus der Cloud geo-gesperrt, daher `urls`-Override auf erreichbare Spiegel (nur Marktdefinitionen).
- `tools/run_backtest_quarters.py` – Jahres-Backtest in 91-Tage-Blöcken mit durchgereichtem Kapital (RAM-Limit der Cloud-Umgebung, ~230 MB/Pair-Jahr).
- `user_data/strategies/NostalgiaForInfinityX7_MaxHold.py` – Subklasse mit harter Max-Haltedauer (`max_hold_hours`, Standard 72); Config `configs/backtest-binance-futures-maxhold72.json`.
- `user_data/strategies/NostalgiaForInfinityX8.py` – X8 v18.0.192 (Stand 2026-11-02) zum Vergleich; Config `configs/backtest-binance-futures-x8.json`.
- `results/` – Kennzahlen der Läufe (Daten: iterativv/NostalgiaForInfinityData, Binance USDT-M Futures, 62 Pairs, 2025-09-01..2026-09-01).
