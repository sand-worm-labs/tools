# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
FACTORY_ADDRESS = "{{factory_address}}"
DATE_FROM = "{{date_from}}"
PROTOCOL = "{{protocol}}".strip()
TOP_N = "{{top_n}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LABEL_RE = re.compile(r"^[A-Za-z0-9_.-]{0,32}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(FACTORY_ADDRESS):
    raise ValueError(f"Invalid factory_address: {FACTORY_ADDRESS!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if not LABEL_RE.match(PROTOCOL):
    raise ValueError(f"Invalid protocol label: {PROTOCOL!r}")
if not TOP_N.isdigit() or int(TOP_N) <= 0:
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

schema = CHAIN_SCHEMA[CHAIN]
factory_hex = FACTORY_ADDRESS[2:].lower()

# "Virtuals Protocol" (an agent-token launchpad on Base) generalized to any
# EVM factory contract: tokens the factory deploys are the "launches", and
# "post-graduation" trading volume is simply their DEX trading activity —
# on Virtuals and comparable EVM launchpads, liquidity migrates to a DEX
# pool once a token graduates, so any dex.trades activity implies that.
sql = f"""
with launches as (
    select address as token_address, min(block_time) as launch_time
    from {schema}.creation_traces
    where deployer = from_hex('{factory_hex}')
      and block_time >= date('{DATE_FROM}')
    group by 1
),
trades as (
    select date_trunc('day', block_time) as day, token_bought_address as token_address, amount_usd
    from dex.trades
    where blockchain = '{schema}'
    union all
    select date_trunc('day', block_time) as day, token_sold_address as token_address, amount_usd
    from dex.trades
    where blockchain = '{schema}'
),
daily_volume as (
    select l.token_address, l.launch_time, t.day, sum(t.amount_usd) as volume
    from trades t
    join launches l on l.token_address = t.token_address
    group by 1, 2, 3
),
top_tokens as (
    select token_address
    from daily_volume
    group by token_address
    order by sum(volume) desc
    limit {int(TOP_N)}
)
select
    dv.day,
    concat('0x', to_hex(dv.token_address)) as token_address,
    dv.volume,
    dv.launch_time
from daily_volume dv
join top_tokens tt on tt.token_address = dv.token_address
order by dv.day, dv.volume desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
