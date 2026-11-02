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

- (noch keine)
