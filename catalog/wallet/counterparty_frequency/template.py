# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET = "{{wallet}}"
DAYS = "{{days}}"
TOP_N = "{{top_n}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_TOP_N = {"10", "25", "50", "100"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")
if not DAYS.isdigit() or int(DAYS) <= 0:
    raise ValueError(f"Invalid days: {DAYS!r}")
if TOP_N not in ALLOWED_TOP_N:
    raise ValueError(f"Unsupported top_n: {TOP_N!r}")

wallet_hex = WALLET[2:].lower()

sql = f"""
with interactions as (
    select
        case when "from" = from_hex('{wallet_hex}') then "to" else "from" end as counterparty,
        block_time
    from {CHAIN}.transactions
    where ("from" = from_hex('{wallet_hex}') or "to" = from_hex('{wallet_hex}'))
      and block_time >= now() - interval '{DAYS}' day
)
select
    '0x' || to_hex(counterparty) as counterparty,
    count(*) as interaction_count,
    min(block_time) as first_seen,
    max(block_time) as last_seen
from interactions
where counterparty is not null
group by counterparty
order by interaction_count desc
limit {TOP_N}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
