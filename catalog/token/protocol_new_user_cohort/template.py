# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
CHAIN_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS:
    LOOKBACK_DAYS = "30"
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]
contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with txs as (
    select "from" as user, date_trunc('day', block_time) as dt
    from {schema}.transactions
    where "to" = from_hex('{contract_hex}')
      and success = true
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
first_seen as (
    select user, min(dt) as first_dt
    from txs
    group by user
)
select
    t.dt,
    count(distinct case when f.first_dt = t.dt then t.user end) as new_users,
    count(distinct t.user) as total_users,
    count(distinct case when f.first_dt < t.dt then t.user end) * 1.0 / nullif(count(distinct t.user), 0) as retention_rate
from txs t
join first_seen f on f.user = t.user
group by t.dt
order by t.dt
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
