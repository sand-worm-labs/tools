# Sandworm Power Toolbox — {{__tool_name}}
# "dex_solana.trades" reinterpreted as the EVM-generic dex.trades table.
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with trades as (
    select taker, date_trunc('day', block_time) as trade_date
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{contract_hex}') or token_sold_address = from_hex('{contract_hex}'))
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
first_trade as (
    select taker, min(trade_date) as first_date
    from trades
    group by taker
),
activity as (
    select distinct taker, trade_date
    from trades
),
daily as (
    select
        a.trade_date as cohort_date,
        count(*) filter (where a.trade_date = f.first_date) as new_users,
        count(*) filter (where a.trade_date > f.first_date) as returning_users
    from activity a
    join first_trade f on f.taker = a.taker
    group by a.trade_date
)
select
    cohort_date,
    new_users,
    returning_users,
    returning_users * 1.0 / nullif(new_users + returning_users, 0) as retention
from daily
order by cohort_date
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
