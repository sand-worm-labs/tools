# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESSES_RAW = "{{contract_addresses}}".replace("[", "").replace("]", "").replace('"', "")

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

contract_addresses = [a.strip() for a in CONTRACT_ADDRESSES_RAW.split(",") if a.strip()]

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not contract_addresses:
    raise ValueError("contract_addresses is required")
for a in contract_addresses:
    if not ADDRESS_RE.match(a):
        raise ValueError(f"Invalid contract address: {a!r}")

schema = CHAIN_SCHEMA[CHAIN]
addr_in_sql = ", ".join(f"from_hex('{a[2:].lower()}')" for a in contract_addresses)

# No lookback input on this tool, so "first interaction" is each depositor's
# true first-ever transaction to any of the given stake contracts (full
# history scan of {schema}.transactions).
sql = f"""
with txs as (
    select date_trunc('day', block_time) as day, "from" as depositor
    from {schema}.transactions
    where "to" in ({addr_in_sql})
),
first_seen as (
    select "from" as depositor, min(date_trunc('day', block_time)) as first_day
    from {schema}.transactions
    where "to" in ({addr_in_sql})
    group by 1
)
select
    t.day as first_date,
    count(distinct case when f.first_day = t.day then t.depositor end) as new_users,
    count(distinct case when f.first_day <> t.day then t.depositor end) as returning_users
from txs t
join first_seen f on f.depositor = t.depositor
group by t.day
order by t.day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
