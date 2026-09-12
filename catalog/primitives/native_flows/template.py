# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET = "{{wallet}}"
DAYS = "{{days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")

wallet_hex = WALLET[2:].lower()

# Combines top-level transaction value transfers with internal call-trace
# value transfers to capture both direct and contract-mediated native flows.
sql = f"""
with movements as (
    select
        block_time,
        value,
        case when "to" = from_hex('{wallet_hex}') then 1 else 0 end as is_in,
        case when "from" = from_hex('{wallet_hex}') then 1 else 0 end as is_out
    from {CHAIN}.transactions
    where value > 0
      and ("from" = from_hex('{wallet_hex}') OR "to" = from_hex('{wallet_hex}'))
      {{__time_where}}
    union all
    select
        block_time,
        value,
        case when "to" = from_hex('{wallet_hex}') then 1 else 0 end as is_in,
        case when "from" = from_hex('{wallet_hex}') then 1 else 0 end as is_out
    from {CHAIN}.traces
    where type = 'call'
      and value > 0
      and ("from" = from_hex('{wallet_hex}') OR "to" = from_hex('{wallet_hex}'))
      {{__time_where}}
)
select
    date_trunc('day', block_time) as day,
    sum(case when is_in = 1 then value else 0 end) / 1e18 as inflow_eth,
    sum(case when is_out = 1 then value else 0 end) / 1e18 as outflow_eth,
    sum(case when is_in = 1 then value else -value end) / 1e18 as net_flow_eth
from movements
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
