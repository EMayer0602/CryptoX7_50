"""X7 mit harter maximaler Haltedauer.

Erbt vollständig von NostalgiaForInfinityX7; einzige Änderung: ist ein Trade
länger als `max_hold_hours` offen, wird er unabhängig von Gewinn/Verlust
geschlossen (exit_reason "max_hold_<h>h"). Zusätzlich werden für solche
Trades keine weiteren Rebuys/Grinds mehr ausgeführt.
"""

from datetime import datetime, timedelta

from NostalgiaForInfinityX7 import NostalgiaForInfinityX7


class NostalgiaForInfinityX7_MaxHold(NostalgiaForInfinityX7):
  max_hold_hours = 72

  def _over_max_hold(self, trade, current_time: datetime) -> bool:
    return (current_time - trade.open_date_utc) >= timedelta(hours=self.max_hold_hours)

  def custom_exit(self, pair: str, trade, current_time: datetime, current_rate: float, current_profit: float, **kwargs):
    if self._over_max_hold(trade, current_time):
      return f"max_hold_{self.max_hold_hours}h"
    return super().custom_exit(pair, trade, current_time, current_rate, current_profit, **kwargs)

  def adjust_trade_position(self, trade, current_time: datetime, *args, **kwargs):
    if self._over_max_hold(trade, current_time):
      return None
    return super().adjust_trade_position(trade, current_time, *args, **kwargs)
