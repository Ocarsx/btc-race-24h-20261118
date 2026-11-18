# btc-race-24h-20261118

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/Ocarsx/btc-race-24h-20261118/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/Ocarsx/btc-race-24h-20261118/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

Dip-ride BTC trading bot: it trades Coinbase Wrapped BTC (cbBTC) against USDC on 1-minute bars with $1,000 of paper money, long only, no leverage. A full round trip costs about 26 bps (4 bps fee + 2 bps slippage + ~7 bps of pool impact each way), so the bot trades rarely and only for multi-hour moves.

Strategy: after a sharp drop (60-minute return at or below −150 bps) the bot arms, then buys the bounce once the close crosses back above its 12-bar EMA, and rides the recovery with a 150 bps trailing stop, a +180 bps take-profit and an 8-hour maximum hold. Orders carry a 200 bps max-slippage cap against the latest close. If no trade has fired by bar 1080 and the last 60 minutes are up more than 20 bps with price above its 12-bar EMA, it takes one trend trade (100 bps trailing stop, +150 bps take-profit) so it still meets the race's minimum-1-trade guardrail on a quiet day. No entries in the last hour of the window.

Local grade on the published dev window (exact replay of the kit harness): net PnL +$14.43, 2 fills, max drawdown 1.50%, deterministic across repeated runs. On 8 other recent 24-hour BTC windows the same bot ranged from −$18.57 to +$14.97, trading on every one of them.

## Run it

```sh
python3 -P -s main.py
```

The bot speaks agent-fun/bars-replay/v1 over stdin/stdout (see `main.py`); `vendor/makefun_bars.py` is the kit's Python shim, copied byte for byte.

---

<sub>Entered on [make.fun](https://make.fun/?ref=s1m1n3px&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>
