"""Dip-ride BTC bot for make.fun btc-race-24h-20261118-1444 (agent-fun/bars-replay/v1).

Idea, in plain terms (hello, batch, orders, bar):
- Bitcoin's 1-minute bars are mostly noise: a full round trip costs ~26 bps
  (4 bps fee + 2 bps slippage + ~7 bps of pool impact each way), so the bot
  trades rarely and only for multi-hour moves.
- Main mode: after a sharp drop (60-minute return <= -150 bps) the bot arms,
  then buys the bounce once the close crosses back above its 12-bar EMA.
  It rides the recovery with a 150 bps trailing stop, a +180 bps take-profit
  and a 480-bar (8 h) maximum hold. One open position at most, full equity.
- Fallback mode: if no trade has happened by bar 1080 and the last 60 minutes
  are up >20 bps with price above its 12-bar EMA, it takes one trend trade
  (trailing stop 100 bps, take-profit 150 bps), so the bot still meets the
  race's minimum-1-trade guardrail on a quiet, drifting-up day.
- No entries in the last hour of the window; no orders on the last batch.
- Deterministic: every decision is a pure function of the bars seen so far
  (no clock, no environment, no randomness). Uses only the standard library
  plus the kit's vendored bars shim.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
MAX_SLIPPAGE_BPS = 200  # 2%: wide enough for a 1-minute gap, tight vs a spike

# Main (dip-buy) mode.
DROP_WIN = 60          # bars over which the drop is measured
DROP_BPS = 150         # arm when the 60-min return is at or below -150 bps
ARM_STALE_BARS = 240   # an armed dip signal expires after 4 h without entry
FAST_EMA = 12          # bounce confirmation: close above this EMA
TRAIL_BPS = 150        # trailing stop from the peak close since entry
TAKE_PROFIT_BPS = 180  # take profit from the entry close
MAX_HOLD = 480         # bars (8 h) maximum hold

# Fallback (trend) mode, only when no trade has happened yet.
FALLBACK_FROM_BAR = 1080
FALLBACK_UP_BPS = 20   # 60-min return above +20 bps (loose: a quiet day still trades once)
FALLBACK_TRAIL_BPS = 100
FALLBACK_TP_BPS = 150

ENTRY_CUTOFF_BAR = 1380  # no new entries in the last hour


class Bot:
    def __init__(self):
        self.closes = []       # closes by batch seq
        self.ema_fast = None
        self.armed_at = None   # seq when the dip signal armed
        self.in_pos = False
        self.entry_close = None
        self.peak_close = None
        self.hold_bars = 0
        self.trades = 0
        self.fallback_mode = False

    def _ema_update(self, close):
        k_fast = 2.0 / (FAST_EMA + 1)
        self.ema_fast = close if self.ema_fast is None else close * k_fast + self.ema_fast * (1 - k_fast)

    def on_batch(self, state, batch):
        close = state.close(SYMBOL)
        if close is None:
            return []
        seq = batch["seq"]
        self.closes.append(close)
        self._ema_update(close)
        # Keep our own position view in sync with the account the harness reports.
        holding = SYMBOL in state.positions and state.positions[SYMBOL].qty > 0
        if holding and not self.in_pos:
            # Position opened (our buy filled on a previous batch).
            self.in_pos = True
            self.entry_close = close
            self.peak_close = close
            self.hold_bars = 0
            self.trades += 1
        elif not holding and self.in_pos:
            self.in_pos = False
            self.entry_close = None
            self.peak_close = None
            self.fallback_mode = False

        if seq >= 1439:  # last batch: orders would be rejected (after_end)
            return []

        if self.in_pos:
            self.hold_bars += 1
            self.peak_close = max(self.peak_close, close)
            gain_bps = (close - self.entry_close) * 10000 // self.entry_close
            trail_hit = close * 10000 < self.peak_close * (10000 - TRAIL_BPS if not self.fallback_mode else 10000 - FALLBACK_TRAIL_BPS)
            tp_hit = gain_bps >= (TAKE_PROFIT_BPS if not self.fallback_mode else FALLBACK_TP_BPS)
            if trail_hit or tp_hit or self.hold_bars >= MAX_HOLD:
                return [{"side": "sell", "symbol": SYMBOL,
                         "qty": state.positions[SYMBOL].qty,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
            return []

        # Flat: look for an entry.
        if seq >= ENTRY_CUTOFF_BAR:
            return []
        if len(self.closes) <= DROP_WIN:
            return []
        drop_bps = (close - self.closes[-1 - DROP_WIN]) * 10000 // self.closes[-1 - DROP_WIN]
        if drop_bps <= -DROP_BPS:
            self.armed_at = seq
        if self.armed_at is not None and seq - self.armed_at > ARM_STALE_BARS:
            self.armed_at = None
        if self.armed_at is not None and close > self.ema_fast:
            self.armed_at = None
            self.fallback_mode = False
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": state.cash,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        # Fallback: one trend trade late in the window when nothing fired yet.
        if (self.trades == 0 and seq >= FALLBACK_FROM_BAR and seq < ENTRY_CUTOFF_BAR
                and drop_bps >= FALLBACK_UP_BPS and close > self.ema_fast):
            self.fallback_mode = True
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": state.cash,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []


makefun_bars.run(Bot().on_batch)
