# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DAYS = "{{days}}"
TOP_N = "{{top_n}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ALLOWED_TOP_N = {"10", "25", "50", "100"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if TOP_N not in ALLOWED_TOP_N:
    raise ValueError(f"Unsupported top_n: {TOP_N!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS}' DAY"

# Merges both call directions (root calling out, and being called into) into
# one edge list rather than picking a side — a protocol's dependency graph is
# usually read from both ends (what it depends on, and what depends on it).
sql = f"""
with edges as (
    select "to" as counterparty, value, 'outgoing' as direction
    from {CHAIN}.traces
    where type = 'call'
      and "from" = from_hex('{contract_hex}')
      and "to" != from_hex('{contract_hex}')
      {time_where}
    union all
    select "from" as counterparty, value, 'incoming' as direction
    from {CHAIN}.traces
    where type = 'call'
      and "to" = from_hex('{contract_hex}')
      and "from" != from_hex('{contract_hex}')
      {time_where}
)
select
    concat('0x', to_hex(counterparty)) as counterparty_address,
    direction,
    count(*) as call_count,
    sum(value) / 1e18 as total_value_eth
from edges
group by 1, 2
order by call_count desc
limit {TOP_N}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="counterparty_address", y="call_count", color="direction")
fig.show()

{{__df_name}}
