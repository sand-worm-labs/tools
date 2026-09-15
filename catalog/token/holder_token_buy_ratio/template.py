# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()
CHAIN = "{{chain}}".strip() or "ethereum"
TOP_N = "{{top_n}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
if not TOP_N.isdigit() or int(TOP_N) <= 0:
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
lookback_days_val = int(LOOKBACK_DAYS)
top_n_val = int(TOP_N)

# token_buy_ratio = a trader's target-token buy volume as a share of all its
# buy volume (any token) on this chain in the window — high ratio means the
# wallet is a dedicated buyer of this token rather than a generalist trader.
sql = f"""
with buys as (
    select taker as trader, amount_usd as amt, token_bought_address as token
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{lookback_days_val}' day
),
target_buys as (
    select trader, sum(amt) as total_buy_usd
    from buys
    where token = from_hex('{token_hex}')
    group by trader
),
all_buys as (
    select trader, sum(amt) as total_all_buy_usd
    from buys
    group by trader
)
select
    t.trader as holder,
    t.total_buy_usd / nullif(a.total_all_buy_usd, 0) as token_buy_ratio,
    t.total_buy_usd
from target_buys t
join all_buys a on a.trader = t.trader
order by token_buy_ratio desc
limit {top_n_val}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
