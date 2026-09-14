# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if LOOKBACK_DAYS and (not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
lookback = LOOKBACK_DAYS or "30"

# "Clusters" here means mutual (A->B and B->A) direct token transfer pairs —
# a lightweight, EVM-native stand-in for a wash-trading/sybil ring signal,
# not a full graph-clustering algorithm.
sql = f"""
with transfers as (
    select "from" as a, "to" as b
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= now() - interval '{lookback}' day
),
mutual as (
    select t1.a as wallet, t1.b as counterparty
    from transfers t1
    join transfers t2 on t1.a = t2.b and t1.b = t2.a
)
select
    to_hex(wallet) as wallet,
    count(distinct counterparty) as cluster_size,
    count(*) as connections
from mutual
group by 1
order by connections desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
